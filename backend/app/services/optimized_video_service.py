"""
Optimized Video Processing Service
最適化された動画処理サービス
"""

import cv2
import numpy as np
import asyncio
import multiprocessing
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import tempfile
import shutil
import os
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time

from app.core.advanced_logger import get_logger
from app.core.performance_config import cache_result, performance_monitor, task_queue
from app.core.config import settings

logger = get_logger("optimized_video_service")


class OptimizedVideoProcessor:
    """最適化された動画処理クラス"""
    
    def __init__(self):
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.process_pool = ProcessPoolExecutor(max_workers=min(4, multiprocessing.cpu_count()))
        
    async def preprocess_video_optimized(
        self, 
        video_path: str, 
        target_fps: int = 15,
        target_height: int = 720,
        compression_quality: int = 85
    ) -> Dict[str, Any]:
        """最適化された動画前処理"""
        
        start_time = time.time()
        logger.info("Starting optimized video preprocessing", 
                   video_path=video_path,
                   target_fps=target_fps,
                   target_height=target_height)
        
        try:
            # 動画情報取得
            video_info = await self._get_video_info_async(video_path)
            
            # 最適化の必要性を判定
            needs_optimization = self._needs_optimization(
                video_info, target_fps, target_height
            )
            
            if not needs_optimization:
                logger.info("Video already optimized, skipping preprocessing")
                return {
                    "path": video_path,
                    "optimized": False,
                    "original_info": video_info
                }
            
            # 最適化実行
            optimized_path = await self._optimize_video_async(
                video_path, target_fps, target_height, compression_quality
            )
            
            # 最適化後の情報取得
            optimized_info = await self._get_video_info_async(optimized_path)
            
            processing_time = time.time() - start_time
            performance_monitor.record_metric(
                "video_preprocessing_time", 
                processing_time * 1000,
                {"fps": target_fps, "height": target_height}
            )
            
            logger.info("Video preprocessing completed",
                       processing_time=processing_time,
                       size_reduction_percent=self._calculate_size_reduction(video_path, optimized_path))
            
            return {
                "path": optimized_path,
                "optimized": True,
                "original_info": video_info,
                "optimized_info": optimized_info,
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error("Video preprocessing failed", error=str(e))
            raise
    
    async def _get_video_info_async(self, video_path: str) -> Dict[str, Any]:
        """非同期で動画情報を取得"""
        
        def get_info():
            cap = cv2.VideoCapture(video_path)
            try:
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                return {
                    "fps": fps,
                    "frame_count": frame_count,
                    "width": width,
                    "height": height,
                    "duration": frame_count / fps if fps > 0 else 0,
                    "file_size": Path(video_path).stat().st_size
                }
            finally:
                cap.release()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.thread_pool, get_info)
    
    def _needs_optimization(
        self, 
        video_info: Dict[str, Any], 
        target_fps: int, 
        target_height: int
    ) -> bool:
        """最適化が必要かどうか判定"""
        
        needs_fps_reduction = video_info["fps"] > target_fps * 1.1
        needs_resolution_reduction = video_info["height"] > target_height * 1.1
        file_too_large = video_info["file_size"] > 50 * 1024 * 1024  # 50MB
        
        return needs_fps_reduction or needs_resolution_reduction or file_too_large
    
    async def _optimize_video_async(
        self,
        input_path: str,
        target_fps: int,
        target_height: int,
        quality: int
    ) -> str:
        """非同期で動画を最適化"""
        
        def optimize_video():
            # 一時出力ファイル作成
            output_fd, output_path = tempfile.mkstemp(suffix='.mp4')
            
            try:
                cap = cv2.VideoCapture(input_path)
                
                # 元の動画情報取得
                original_fps = cap.get(cv2.CAP_PROP_FPS)
                original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                # スケール計算
                scale_factor = min(1.0, target_height / original_height)
                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)
                
                # フレームスキップ計算
                frame_skip = max(1, int(original_fps / target_fps))
                
                # 動画ライター設定
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(
                    output_path, 
                    fourcc, 
                    min(target_fps, original_fps), 
                    (new_width, new_height)
                )
                
                frame_count = 0
                processed_frames = 0
                
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # フレームスキップ
                    if frame_count % frame_skip == 0:
                        # リサイズ
                        if scale_factor < 1.0:
                            frame = cv2.resize(frame, (new_width, new_height))
                        
                        out.write(frame)
                        processed_frames += 1
                    
                    frame_count += 1
                
                cap.release()
                out.release()
                
                logger.debug("Video optimization completed",
                           original_frames=frame_count,
                           processed_frames=processed_frames,
                           scale_factor=scale_factor)
                
                return output_path
                
            except Exception as e:
                # エラー時はファイルを削除
                try:
                    os.unlink(output_path)
                except:
                    pass
                raise e
            finally:
                os.close(output_fd)
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.process_pool, optimize_video)
    
    def _calculate_size_reduction(self, original_path: str, optimized_path: str) -> float:
        """ファイルサイズ削減率を計算"""
        original_size = Path(original_path).stat().st_size
        optimized_size = Path(optimized_path).stat().st_size
        
        return ((original_size - optimized_size) / original_size) * 100
    
    @cache_result(ttl=1800, key_prefix="frame_extraction")
    async def extract_frames_optimized(
        self, 
        video_path: str, 
        max_frames: int = 450,  # 15fps × 30秒
        target_size: Tuple[int, int] = (640, 480)
    ) -> List[np.ndarray]:
        """最適化されたフレーム抽出"""
        
        start_time = time.time()
        
        def extract_frames():
            cap = cv2.VideoCapture(video_path)
            frames = []
            
            try:
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                step = max(1, total_frames // max_frames)
                
                frame_count = 0
                while len(frames) < max_frames:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
                    ret, frame = cap.read()
                    
                    if not ret:
                        break
                    
                    # リサイズ
                    frame = cv2.resize(frame, target_size)
                    
                    # RGB変換
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    frames.append(frame)
                    frame_count += step
                
                return frames
                
            finally:
                cap.release()
        
        loop = asyncio.get_event_loop()
        frames = await loop.run_in_executor(self.process_pool, extract_frames)
        
        processing_time = time.time() - start_time
        performance_monitor.record_metric(
            "frame_extraction_time",
            processing_time * 1000,
            {"frame_count": len(frames)}
        )
        
        logger.debug("Frame extraction completed",
                    frame_count=len(frames),
                    processing_time=processing_time)
        
        return frames
    
    async def batch_process_frames(
        self,
        frames: List[np.ndarray],
        processor_func,
        batch_size: int = 8
    ) -> List[Any]:
        """フレームのバッチ処理"""
        
        results = []
        total_batches = (len(frames) + batch_size - 1) // batch_size
        
        logger.info("Starting batch frame processing",
                   total_frames=len(frames),
                   batch_size=batch_size,
                   total_batches=total_batches)
        
        for i in range(0, len(frames), batch_size):
            batch = frames[i:i + batch_size]
            batch_start_time = time.time()
            
            # バッチ処理を並列実行
            tasks = [
                asyncio.create_task(
                    asyncio.to_thread(processor_func, frame)
                ) for frame in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # エラーハンドリング
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.warning("Frame processing failed",
                                 batch_index=i // batch_size,
                                 frame_index=i + j,
                                 error=str(result))
                    results.append(None)
                else:
                    results.append(result)
            
            batch_time = time.time() - batch_start_time
            performance_monitor.record_metric(
                "batch_processing_time",
                batch_time * 1000,
                {"batch_size": len(batch)}
            )
            
            logger.debug("Batch processing completed",
                        batch_index=i // batch_size + 1,
                        batch_size=len(batch),
                        processing_time=batch_time)
        
        return results
    
    async def cleanup_temp_files(self, file_paths: List[str]):
        """一時ファイルの非同期クリーンアップ"""
        
        def cleanup():
            for path in file_paths:
                try:
                    if Path(path).exists():
                        Path(path).unlink()
                        logger.debug("Temp file cleaned up", path=path)
                except Exception as e:
                    logger.warning("Failed to cleanup temp file", path=path, error=str(e))
        
        await task_queue.add_task(cleanup)
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """最適化統計を取得"""
        return {
            "thread_pool_active": self.thread_pool._threads,
            "process_pool_active": len(self.process_pool._processes) if hasattr(self.process_pool, '_processes') else 0,
            "performance_metrics": {
                "video_preprocessing": performance_monitor.get_metrics_summary("video_preprocessing_time"),
                "frame_extraction": performance_monitor.get_metrics_summary("frame_extraction_time"),
                "batch_processing": performance_monitor.get_metrics_summary("batch_processing_time")
            }
        }
    
    async def shutdown(self):
        """リソースのクリーンアップ"""
        logger.info("Shutting down optimized video processor")
        
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)
        
        logger.info("Optimized video processor shutdown completed")


# グローバルインスタンス
optimized_video_processor = OptimizedVideoProcessor()


# 便利関数
async def process_video_optimized(video_path: str, **kwargs) -> Dict[str, Any]:
    """最適化された動画処理の便利関数"""
    return await optimized_video_processor.preprocess_video_optimized(video_path, **kwargs)


async def extract_frames_fast(video_path: str, **kwargs) -> List[np.ndarray]:
    """高速フレーム抽出の便利関数"""
    return await optimized_video_processor.extract_frames_optimized(video_path, **kwargs)