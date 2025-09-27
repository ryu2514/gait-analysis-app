"""
動画処理サービス
"""

import os
import tempfile
from typing import Dict, Any, Tuple
import numpy as np
from pathlib import Path

from app.core.config import settings
from app.core.logging import StructuredLogger

# 軽量モードではOpenCVに依存しない
if getattr(settings, 'LIGHT_MODE', False):
    cv2 = None  # type: ignore
else:
    try:
        import cv2  # type: ignore
    except Exception:  # 環境によりOpenCVが無い場合に備える
        cv2 = None  # type: ignore

logger = StructuredLogger(__name__)


class VideoProcessingService:
    """動画処理サービス"""
    
    def __init__(self):
        self.supported_formats = settings.SUPPORTED_VIDEO_FORMATS
        self.max_duration = settings.MAX_VIDEO_DURATION_SECONDS
        self.target_fps = settings.TARGET_FPS
    
    async def preprocess_video(
        self, 
        input_path: str, 
        target_fps: int = None
    ) -> Dict[str, Any]:
        """
        動画前処理
        
        Args:
            input_path: 入力動画パス
            target_fps: 目標FPS
            
        Returns:
            Dict: 処理後動画情報
        """
        if target_fps is None:
            target_fps = self.target_fps
            
        logger.info("Starting video preprocessing", input_path=input_path)
        
        try:
            # 軽量モードまたはOpenCV非利用環境では前処理をスキップ
            if cv2 is None:
                stub_info = self._get_video_info_stub(input_path, target_fps)
                return {
                    "path": input_path,
                    "processed": False,
                    **stub_info
                }

            # 動画情報取得
            video_info = self._get_video_info(input_path)

            # 検証
            self._validate_video(video_info)

            # 前処理が必要かチェック
            needs_processing = self._needs_preprocessing(video_info, target_fps)

            if not needs_processing:
                logger.info("Video preprocessing not needed")
                return {
                    "path": input_path,
                    "processed": False,
                    **video_info
                }

            # 前処理実行
            output_path = await self._process_video(
                input_path,
                video_info,
                target_fps
            )

            # 処理後情報取得
            processed_info = self._get_video_info(output_path)

            logger.info(
                "Video preprocessing completed",
                original_fps=video_info["fps"],
                target_fps=target_fps,
                output_path=output_path
            )

            return {
                "path": output_path,
                "processed": True,
                "original_info": video_info,
                **processed_info
            }

        except Exception as e:
            logger.error("Video preprocessing failed", error=str(e))
            raise
    
    def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """動画情報取得"""
        if cv2 is None:
            return self._get_video_info_stub(video_path, self.target_fps)

        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"動画ファイルを開けません: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
        
        return {
            "fps": fps,
            "frame_count": frame_count,
            "width": width,
            "height": height,
            "duration_seconds": duration,
            "file_size_mb": file_size_mb,
            "aspect_ratio": width / height if height > 0 else 0
        }

    def _get_video_info_stub(self, video_path: str, target_fps: int) -> Dict[str, Any]:
        """OpenCV不使用時の動画情報スタブ"""
        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
        # 代表値でスタブ（テスト用途）
        width, height = 1280, 720
        fps = target_fps or self.target_fps or 30
        duration = 5.0
        frame_count = int(duration * fps)
        return {
            "fps": fps,
            "frame_count": frame_count,
            "width": width,
            "height": height,
            "duration_seconds": duration,
            "file_size_mb": file_size_mb,
            "aspect_ratio": width / height,
        }
    
    def _validate_video(self, video_info: Dict[str, Any]) -> None:
        """動画検証"""
        # 時間チェック
        if video_info["duration_seconds"] > self.max_duration:
            raise ValueError(
                f"動画が長すぎます。最大{self.max_duration}秒まで対応しています"
            )
        
        if video_info["duration_seconds"] < 3:
            raise ValueError("動画が短すぎます。最低3秒の動画が必要です")
        
        # 解像度チェック
        if video_info["width"] < 480 or video_info["height"] < 360:
            raise ValueError("解像度が低すぎます。最低480x360が必要です")
        
        # FPSチェック
        if video_info["fps"] < 15:
            raise ValueError("フレームレートが低すぎます。最低15FPSが必要です")
        
        # アスペクト比チェック
        if video_info["aspect_ratio"] < 0.5 or video_info["aspect_ratio"] > 2.0:
            logger.warning(
                "Unusual aspect ratio detected", 
                aspect_ratio=video_info["aspect_ratio"]
            )
    
    def _needs_preprocessing(self, video_info: Dict[str, Any], target_fps: int) -> bool:
        """前処理が必要かチェック"""
        # FPS調整が必要
        if abs(video_info["fps"] - target_fps) > 2:
            return True
        
        # 解像度が高すぎる場合（処理速度向上のため）
        if video_info["width"] > 1920 or video_info["height"] > 1080:
            return True
        
        # 手ブレ補正が必要（将来実装）
        # if self._detect_camera_shake(video_path):
        #     return True
        
        return False
    
    async def _process_video(
        self, 
        input_path: str, 
        video_info: Dict[str, Any], 
        target_fps: int
    ) -> str:
        """動画処理実行"""
        if cv2 is None:
            # 軽量モードではコピーせず元パスを返す（処理無し）
            return input_path
        # 一時出力ファイル作成
        temp_output = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=".mp4",
            dir=tempfile.gettempdir()
        )
        output_path = temp_output.name
        temp_output.close()
        
        cap = cv2.VideoCapture(input_path)
        
        # 出力動画設定
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        target_width = min(video_info["width"], 1920)
        target_height = min(video_info["height"], 1080)
        
        # アスペクト比維持してリサイズ
        if video_info["width"] > target_width or video_info["height"] > target_height:
            scale = min(target_width / video_info["width"], target_height / video_info["height"])
            target_width = int(video_info["width"] * scale)
            target_height = int(video_info["height"] * scale)
        
        out = cv2.VideoWriter(output_path, fourcc, target_fps, (target_width, target_height))
        
        # フレーム処理
        frame_interval = video_info["fps"] / target_fps
        frame_counter = 0
        processed_frames = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # FPS調整のためのフレームスキップ
            if frame_counter % int(frame_interval) == 0:
                # リサイズ
                if (target_width, target_height) != (video_info["width"], video_info["height"]):
                    frame = cv2.resize(frame, (target_width, target_height))
                
                # フレーム安定化（簡易実装）
                frame = self._stabilize_frame(frame)
                
                out.write(frame)
                processed_frames += 1
            
            frame_counter += 1
        
        cap.release()
        out.release()
        
        logger.info(
            "Video processing completed",
            input_frames=frame_counter,
            output_frames=processed_frames,
            output_path=output_path
        )
        
        return output_path
    
    def _stabilize_frame(self, frame: np.ndarray) -> np.ndarray:
        """フレーム安定化（手ブレ補正）"""
        # 簡易実装：ガウシアンフィルタでノイズ除去
        return cv2.GaussianBlur(frame, (3, 3), 0)
    
    def enhance_video_quality(self, video_path: str) -> str:
        """動画品質向上処理"""
        # TODO: 高度な画質向上処理
        # - ノイズ除去
        # - シャープネス調整
        # - コントラスト改善
        pass
    
    def extract_frames(
        self, 
        video_path: str, 
        start_time: float = 0, 
        end_time: float = None
    ) -> list:
        """フレーム抽出"""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        start_frame = int(start_time * fps)
        end_frame = int(end_time * fps) if end_time else int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        frames = []
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        for frame_num in range(start_frame, end_frame):
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        
        cap.release()
        return frames
    
    def create_analysis_video(
        self, 
        original_path: str, 
        landmarks_data: list, 
        output_path: str
    ) -> str:
        """分析結果付き動画作成"""
        # TODO: ランドマーク表示付き動画生成
        # - ポーズランドマーク描画
        # - 歩行周期ハイライト
        # - 分析結果オーバーレイ
        pass
    
    async def cleanup_temp_file(self, file_path: str) -> None:
        """一時ファイルクリーンアップ"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.debug("Temp file cleaned up", file_path=file_path)
        except Exception as e:
            logger.warning("Failed to cleanup temp file", file_path=file_path, error=str(e))
