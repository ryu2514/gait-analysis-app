"""
歩行分析サービス
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import math
import time
from scipy import signal
from scipy.fft import fft, fftfreq

from app.models.gait_models import (
    GaitCycle, SpatiotemporalParameters, SymmetryIndices, 
    JointAngles, AnalysisMode, CompensationAlert, BalanceMetrics
)
from app.services.gait_cycle_detector import GaitCycleDetector
from app.services.spatiotemporal_analyzer import SpatiotemporalAnalyzer
from app.services.joint_angle_calculator import JointAngleCalculator
from app.services.symmetry_analyzer import SymmetryAnalyzer
from app.core.config import settings
from app.core.advanced_logger import get_logger
from app.core.performance_config import cache_result, performance_monitor

logger = get_logger(__name__)


class GaitAnalysisService:
    """歩行分析メインサービス"""
    
    def __init__(self):
        self.light_mode = getattr(settings, 'LIGHT_MODE', False)

        if not self.light_mode:
            # 遅延インポートで重い依存の初期化を制御
            import mediapipe as mp  # type: ignore
            import cv2  # type: ignore
            self._cv2 = cv2
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                model_complexity=2,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
                enable_segmentation=False,
                smooth_landmarks=True
            )
            self.gait_detector = GaitCycleDetector()
            self.spatiotemporal_analyzer = SpatiotemporalAnalyzer()
            self.joint_calculator = JointAngleCalculator()
            self.symmetry_analyzer = SymmetryAnalyzer()

            # 新機能モジュール追加（軽量モードでは読み込まない）
            from app.services.center_of_mass_analyzer import CenterOfMassAnalyzer
            from app.services.compensation_detector import CompensationDetector
            from app.services.enhanced_video_processor import EnhancedVideoProcessor
            from app.services.enhanced_spatiotemporal_analyzer import EnhancedSpatiotemporalAnalyzer
            from app.services.enhanced_joint_angle_calculator import EnhancedJointAngleCalculator
            from app.services.performance_optimizer import PerformanceOptimizer

            self.com_analyzer = CenterOfMassAnalyzer()
            self.compensation_detector = CompensationDetector()
            self.video_processor = EnhancedVideoProcessor()
            self.enhanced_spatiotemporal_analyzer = EnhancedSpatiotemporalAnalyzer()
            self.enhanced_joint_calculator = EnhancedJointAngleCalculator()
            self.performance_optimizer = PerformanceOptimizer()
        else:
            # 軽量モード：重い依存の初期化は行わない
            self._cv2 = None
            self.mp_pose = None
            self.pose = None
            self.gait_detector = None
            self.spatiotemporal_analyzer = None
            self.joint_calculator = None
            self.symmetry_analyzer = None
            self.com_analyzer = None
            self.compensation_detector = None
            self.video_processor = None
            self.enhanced_spatiotemporal_analyzer = None
            self.enhanced_joint_calculator = None
            self.performance_optimizer = None
    
    async def analyze_gait_optimized(
        self, 
        video_path: str, 
        user_height_cm: Optional[float] = None,
        analysis_mode: str = "standard",
        analysis_id: str = "",
        camera_position: str = "side",
        target_fps: int = 60,
        device_type: str = "mobile",
        enable_30s_optimization: bool = True
    ) -> Dict[str, Any]:
        """
        30秒最適化歩行分析メイン処理
        
        Args:
            video_path: 動画ファイルパス
            user_height_cm: ユーザー身長
            analysis_mode: 分析モード
            analysis_id: 分析ID
            camera_position: カメラ位置
            target_fps: 目標フレームレート
            device_type: デバイスタイプ
            enable_30s_optimization: 30秒最適化有効化
            
        Returns:
            Dict: 最適化された分析結果
        """
        logger.set_context(analysis_id=analysis_id)
        
        with logger.performance_timer("optimized_gait_analysis_full"):
            logger.gait_analysis("Starting optimized gait analysis", 
                               analysis_id=analysis_id, 
                               video_path=video_path,
                               optimization_enabled=enable_30s_optimization)
        
        if self.light_mode:
            # 軽量モード：モック分析結果を返す
            return self._mock_analysis_result(
                user_height_cm=user_height_cm,
                analysis_mode=analysis_mode,
                camera_position=camera_position,
                target_fps=target_fps,
                device_type=device_type
            )
        if enable_30s_optimization:
            # 30秒最適化パイプライン使用
            analysis_params = {
                'user_height_cm': user_height_cm,
                'analysis_mode': analysis_mode,
                'camera_position': camera_position,
                'target_fps': target_fps,
                'device_type': device_type,
                'analysis_id': analysis_id
            }
            
            result = await self.performance_optimizer.optimize_gait_analysis_pipeline(
                video_path, self, analysis_params
            )
            
            logger.info("Optimized gait analysis completed",
                       analysis_id=analysis_id,
                       processing_time=result.get('optimization_info', {}).get('total_processing_time'),
                       target_achieved=result.get('optimization_info', {}).get('target_achieved'))
            
            return result
        else:
            # 標準分析パイプライン使用
            return await self.analyze_gait(
                video_path, user_height_cm, analysis_mode, analysis_id,
                camera_position, target_fps, device_type
            )
        
    async def analyze_gait(
        self, 
        video_path: str, 
        user_height_cm: Optional[float] = None,
        analysis_mode: str = "standard",
        analysis_id: str = "",
        camera_position: str = "side",  # "side", "posterior", "anterior"
        target_fps: int = 60,  # iPad/iPhone 60fps対応
        device_type: str = "mobile"  # "mobile", "tablet", "desktop"
    ) -> Dict[str, Any]:
        """
        歩行分析メイン処理
        
        Args:
            video_path: 動画ファイルパス
            user_height_cm: ユーザー身長
            analysis_mode: 分析モード
            analysis_id: 分析ID
            
        Returns:
            Dict: 分析結果
        """
        # 分析コンテキストを設定
        logger.set_context(analysis_id=analysis_id)
        
        with logger.performance_timer("gait_analysis_full"):
            logger.gait_analysis("Starting gait analysis", 
                               analysis_id=analysis_id, 
                               video_path=video_path,
                               analysis_mode=analysis_mode,
                               user_height_cm=user_height_cm)
            
            # パフォーマンス監視開始
            start_time = time.time()
        
        try:
            if self.light_mode:
                # 軽量モード：モック分析結果を返す
                return self._mock_analysis_result(
                    user_height_cm=user_height_cm,
                    analysis_mode=analysis_mode,
                    camera_position=camera_position,
                    target_fps=target_fps,
                    device_type=device_type
                )
            # 1. 動画からポーズランドマーク抽出（60fps対応）
            landmarks_data = await self._extract_pose_landmarks_enhanced(
                video_path, target_fps, device_type
            )
            
            if not landmarks_data["landmarks"]:
                raise ValueError("動画からポーズデータを抽出できませんでした")
            
            # 2. スケール補正（身長ベース）
            scale_factor = self._calculate_scale_factor(
                landmarks_data["landmarks"], 
                user_height_cm
            )
            
            # 3. 歩行周期検出（高精度検出器使用）
            gait_cycles = self.gait_detector.detect_gait_cycles(
                landmarks_data["landmarks"], 
                landmarks_data["fps"]
            )
            
            if len(gait_cycles) < 1:  # 最小要件を緩和
                logger.warning("Limited gait cycles detected", cycles=len(gait_cycles))
            
            # 4. 拡張時空間パラメータ計算
            enhanced_spatiotemporal_params = self.enhanced_spatiotemporal_analyzer.analyze_detailed_spatiotemporal_parameters(
                gait_cycles, landmarks_data["landmarks"], scale_factor, landmarks_data["fps"]
            )
            
            # 5. 拡張関節角度計算（股関節ROM、膝・足関節詳細、骨盤・体幹回旋）
            enhanced_joint_angles = None
            if analysis_mode in ["standard", "detailed"]:
                enhanced_joint_angles = self.enhanced_joint_calculator.calculate_enhanced_joint_angles(
                    landmarks_data["landmarks"], gait_cycles, landmarks_data["fps"]
                )
            
            # 6. 重心・バランス分析
            balance_metrics = self.com_analyzer.analyze_center_of_mass(
                landmarks_data["landmarks"], scale_factor, camera_position
            )
            
            # 7. 代償動作検出
            compensation_alerts = self.compensation_detector.detect_compensation_movements(
                landmarks_data["landmarks"], enhanced_joint_angles, gait_cycles
            )
            
            # 8. 対称性指標計算（従来版）
            symmetry_indices = self.symmetry_analyzer.analyze_gait_symmetry(gait_cycles, enhanced_joint_angles)
            
            # 9. 拡張出力形式生成（正規化波形、スローモーション動画、カラーPDF）
            enhanced_output = None
            if analysis_mode == "detailed":
                enhanced_output = self.video_processor.create_enhanced_output(
                    video_path, landmarks_data["landmarks"], enhanced_joint_angles,
                    enhanced_spatiotemporal_params, balance_metrics, compensation_alerts
                )
            
            # 10. 品質評価
            quality_metrics = self._assess_analysis_quality(
                landmarks_data["landmarks"], 
                gait_cycles
            )
            
            # 11. 総合スコア算出（拡張版）
            overall_score = self._calculate_enhanced_overall_score(
                enhanced_spatiotemporal_params, 
                balance_metrics,
                compensation_alerts,
                quality_metrics
            )
            
            # 12. 改善提案生成（拡張分析結果を統合）
            recommendations = self._generate_enhanced_recommendations(
                enhanced_spatiotemporal_params, 
                balance_metrics,
                enhanced_joint_angles,
                compensation_alerts,
                quality_metrics
            )
            
            result = {
                # 拡張時空間パラメータ
                "enhanced_spatiotemporal_params": enhanced_spatiotemporal_params,
                "spatiotemporal_params": enhanced_spatiotemporal_params,  # 後方互換性
                
                # 拡張関節角度・キネマティクス
                "enhanced_joint_angles": enhanced_joint_angles,
                "joint_angles": enhanced_joint_angles,  # 後方互換性
                
                # 重心・バランス指標
                "balance_metrics": balance_metrics,
                
                # 代償動作アラート
                "compensation_alerts": compensation_alerts,
                
                # 従来指標（互換性）
                "symmetry_indices": symmetry_indices,
                "gait_cycles": gait_cycles,
                
                # 品質・スコア
                "video_quality_score": quality_metrics["video_quality"],
                "pose_detection_confidence": quality_metrics["pose_confidence"],
                "gait_cycles_detected": len(gait_cycles),
                "overall_gait_score": overall_score,
                "recommendations": recommendations,
                
                # 拡張出力
                "enhanced_output": enhanced_output,
                
                # メタデータ
                "video_info": landmarks_data["video_info"],
                "analysis_settings": {
                    "analysis_mode": analysis_mode,
                    "camera_position": camera_position,
                    "target_fps": target_fps,
                    "device_type": device_type,
                    "user_height_cm": user_height_cm,
                    "scale_factor": scale_factor,
                    "model_complexity": 2,  # 最高精度モデル
                    "processing_time_seconds": time.time() - start_time
                }
            }
            
            logger.info(
                "Gait analysis completed successfully",
                analysis_id=analysis_id,
                gait_cycles=len(gait_cycles),
                overall_score=overall_score
            )
            
            return result
            
        except Exception as e:
            logger.error("Gait analysis failed", analysis_id=analysis_id, error=str(e))
            raise

    def _mock_analysis_result(
        self,
        user_height_cm: Optional[float],
        analysis_mode: str,
        camera_position: str,
        target_fps: int,
        device_type: str,
    ) -> Dict[str, Any]:
        """軽量モード用のモック分析結果"""
        # シンプルな時系列や指標の擬似値（モード別）
        if analysis_mode == "quick":
            joint_angles = None  # 簡易モードでは角度系列を省略
            sp_params = {
                "gait_speed_ms": 1.25,
                "cadence_steps_per_min": 112,
                "stride_length_m": 1.35,
                "stride_time_s": 1.07,
                "left_step_length_m": 0.67,
                "right_step_length_m": 0.68,
                "left_stance_time_s": 0.66,
                "right_stance_time_s": 0.65,
                "double_support_time_s": 0.18,
            }
        else:
            joint_angles = {
                "hip_flexion_deg": [10, 15, 20, 15, 10],
                "hip_extension_deg": [-5, -10, -12, -10, -5],
                "hip_abduction_deg": [0, 2, 3, 2, 0],
                "hip_rom_deg": 30.0,
                "knee_flexion_deg": [0, 20, 40, 20, 0],
                "knee_heel_contact_deg": 5.0,
                "knee_max_flexion_deg": 40.0,
                "ankle_dorsiflexion_deg": [0, 5, 10, 5, 0],
                "ankle_plantarflexion_deg": [0, -5, -10, -5, 0],
                "ankle_toe_off_deg": -10.0,
            }
            sp_params = {
                "gait_speed_ms": 1.2,
                "cadence_steps_per_min": 115,
                "stride_length_m": 1.4,
                "stride_time_s": 1.1,
                "left_step_length_m": 0.7,
                "right_step_length_m": 0.7,
                "left_stance_time_s": 0.7,
                "right_stance_time_s": 0.7,
                "double_support_time_s": 0.2,
            }
        symmetry = {
            "step_length_symmetry_percent": 2.0,
            "stance_time_symmetry_percent": 3.0,
            "swing_time_symmetry_percent": 2.5,
            "hip_flexion_symmetry_percent": 1.0,
            "knee_flexion_symmetry_percent": 1.5,
            "ankle_dorsiflexion_symmetry_percent": 1.0,
            "overall_symmetry_score": 95.0,
        }
        gait_cycles = [
            {
                "cycle_id": "mock-1",
                "start_frame": 0,
                "end_frame": 30,
                "duration_seconds": 0.5,
                "side": "left",
                "step_length_m": 0.7,
                "step_width_m": 0.1,
                "stance_time_seconds": 0.7,
                "swing_time_seconds": 0.4,
                "stance_ratio": 0.6,
                "hip_flexion_peak_deg": 25.0,
                "knee_flexion_peak_deg": 40.0,
                "ankle_dorsiflexion_peak_deg": 10.0,
                "phase_timings": {"heel_strike": 0.0, "toe_off": 0.6},
            }
        ]
        if analysis_mode == "detailed":
            # 詳細モードでは擬似的にもう1周期追加
            gait_cycles.append({
                "cycle_id": "mock-2",
                "start_frame": 31,
                "end_frame": 62,
                "duration_seconds": 0.52,
                "side": "right",
                "step_length_m": 0.7,
                "step_width_m": 0.1,
                "stance_time_seconds": 0.68,
                "swing_time_seconds": 0.42,
                "stance_ratio": 0.62,
                "hip_flexion_peak_deg": 26.0,
                "knee_flexion_peak_deg": 41.0,
                "ankle_dorsiflexion_peak_deg": 10.5,
                "phase_timings": {"heel_strike": 0.0, "toe_off": 0.6},
            })
        balance = {
            "com_lateral_displacement_cm": [0.0, 0.2, 0.4, 0.2, 0.0],
            "com_anterior_posterior_cm": [0.0, 0.5, 1.0, 0.5, 0.0],
            "com_vertical_displacement_cm": [0.0, 0.3, 0.6, 0.3, 0.0],
            "com_projection_x": [0.1, 0.2, 0.1],
            "com_projection_y": [0.1, 0.2, 0.1],
            "lateral_displacement_max_cm": 0.6,
            "vertical_displacement_max_cm": 0.7,
            "balance_stability_score": 85.0,
        }
        video_info = {
            "total_frames": 60,
            "duration_seconds": 2.0,
            "resolution": "1280x720",
            "fps": target_fps,
        }
        base = {
            "spatiotemporal_params": sp_params,
            "symmetry_indices": symmetry,
            "gait_cycles": gait_cycles,
            "joint_angles": joint_angles,
            "video_quality_score": 90.0,
            "pose_detection_confidence": 0.95,
            "gait_cycles_detected": len(gait_cycles),
            "overall_gait_score": 92.0,
            "recommendations": [
                "良好な歩行パターンです。現状維持のための筋力維持訓練を継続してください"
            ],
            "video_info": video_info,
            "analysis_settings": {
                "analysis_mode": analysis_mode,
                "camera_position": camera_position,
                "target_fps": target_fps,
                "device_type": device_type,
                "user_height_cm": user_height_cm,
                "model_complexity": None,
                "processing_time_seconds": 0.1,
            },
        }
        if analysis_mode == "quick":
            base["overall_gait_score"] = 90.0
            base["recommendations"] = ["基本指標は良好です。運動習慣の継続を推奨します"]
        elif analysis_mode == "detailed":
            base["overall_gait_score"] = 93.0
            base["recommendations"].append("詳細解析で良好な対称性が示されました。可動域維持に留意してください")
        return base
    
    @cache_result(ttl=3600, key_prefix="pose_landmarks")
    async def _extract_pose_landmarks(self, video_path: str) -> Dict[str, Any]:
        """動画からポーズランドマーク抽出"""
        cap = self._cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError("動画ファイルを開けませんでした")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        landmarks_sequence = []
        confidence_scores = []
        frame_count = 0
        
        logger.info(f"Processing video: {total_frames} frames at {fps} FPS")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # RGB変換
            frame_rgb = self._cv2.cvtColor(frame, self._cv2.COLOR_BGR2RGB)
            
            # ポーズ検出
            results = self.pose.process(frame_rgb)
            
            if results.pose_landmarks:
                # ランドマーク座標を正規化座標で保存
                landmarks = []
                for landmark in results.pose_landmarks.landmark:
                    landmarks.append({
                        'x': landmark.x,
                        'y': landmark.y,
                        'z': landmark.z,
                        'visibility': landmark.visibility
                    })
                
                landmarks_sequence.append({
                    'frame': frame_count,
                    'timestamp': frame_count / fps,
                    'landmarks': landmarks
                })
                
                # 信頼度スコア計算
                avg_visibility = np.mean([lm['visibility'] for lm in landmarks])
                confidence_scores.append(avg_visibility)
            else:
                # ランドマークが検出されない場合はNoneを追加
                landmarks_sequence.append(None)
                confidence_scores.append(0.0)
            
            frame_count += 1
        
        cap.release()
        
        # 欠損フレーム補間
        landmarks_sequence = self._interpolate_missing_landmarks(landmarks_sequence)
        
        return {
            "landmarks": landmarks_sequence,
            "fps": fps,
            "confidence_scores": confidence_scores,
            "video_info": {
                "total_frames": total_frames,
                "duration_seconds": total_frames / fps,
                "resolution": f"{width}x{height}",
                "fps": fps
            }
        }
    
    def _interpolate_missing_landmarks(self, landmarks_sequence: List) -> List:
        """欠損ランドマークの補間"""
        # 簡単な線形補間を実装
        valid_indices = [i for i, lm in enumerate(landmarks_sequence) if lm is not None]
        
        if len(valid_indices) < 2:
            raise ValueError("有効なポーズデータが不十分です")
        
        for i, landmarks in enumerate(landmarks_sequence):
            if landmarks is None:
                # 前後の有効なフレームから線形補間
                prev_idx = max([idx for idx in valid_indices if idx < i], default=None)
                next_idx = min([idx for idx in valid_indices if idx > i], default=None)
                
                if prev_idx is not None and next_idx is not None:
                    # 線形補間
                    alpha = (i - prev_idx) / (next_idx - prev_idx)
                    interpolated = self._interpolate_landmarks(
                        landmarks_sequence[prev_idx], 
                        landmarks_sequence[next_idx], 
                        alpha
                    )
                    landmarks_sequence[i] = interpolated
        
        return [lm for lm in landmarks_sequence if lm is not None]
    
    @cache_result(ttl=3600, key_prefix="enhanced_pose_landmarks")
    async def _extract_pose_landmarks_enhanced(
        self, 
        video_path: str, 
        target_fps: int = 60,
        device_type: str = "mobile"
    ) -> Dict[str, Any]:
        """
        拡張ポーズランドマーク抽出（60fps対応、iOS最適化）
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError("動画ファイルを開けませんでした")
        
        original_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # フレームスキップ計算（高fpsサポート）
        frame_skip = max(1, int(original_fps / target_fps)) if original_fps > target_fps else 1
        effective_fps = original_fps / frame_skip
        
        landmarks_sequence = []
        confidence_scores = []
        frame_count = 0
        processed_frames = 0
        
        logger.info(f"Processing enhanced video: {total_frames} frames at {original_fps} FPS, target {target_fps} FPS")
        
        # iOS最適化：小さいフレームサイズでの処理
        process_width = min(width, 640) if device_type == "mobile" else width
        process_height = min(height, 480) if device_type == "mobile" else height
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # フレームスキップ
            if frame_count % frame_skip != 0:
                frame_count += 1
                continue
            
            # フレームリサイズ（処理速度向上）
            if device_type == "mobile" and (width > 640 or height > 480):
                frame = cv2.resize(frame, (process_width, process_height))
            
            # RGB変換
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # ポーズ検出（高精度モデル）
            results = self.pose.process(frame_rgb)
            
            if results.pose_landmarks:
                # 33点すべてのランドマークを保存
                landmarks = []
                for landmark in results.pose_landmarks.landmark:
                    landmarks.append({
                        'x': landmark.x,
                        'y': landmark.y,
                        'z': landmark.z,
                        'visibility': landmark.visibility
                    })
                
                landmarks_sequence.append({
                    'frame': processed_frames,
                    'timestamp': processed_frames / effective_fps,
                    'landmarks': landmarks
                })
                
                # 信頼度スコア計算（33点の平均）
                avg_visibility = np.mean([lm['visibility'] for lm in landmarks])
                confidence_scores.append(avg_visibility)
            else:
                landmarks_sequence.append(None)
                confidence_scores.append(0.0)
            
            frame_count += 1
            processed_frames += 1
        
        cap.release()
        
        # 欠損フレーム補間（改良版）
        landmarks_sequence = self._interpolate_missing_landmarks_enhanced(landmarks_sequence)
        
        return {
            "landmarks": landmarks_sequence,
            "fps": effective_fps,
            "confidence_scores": confidence_scores,
            "video_info": {
                "total_frames": processed_frames,
                "original_fps": original_fps,
                "effective_fps": effective_fps,
                "frame_skip": frame_skip,
                "duration_seconds": processed_frames / effective_fps,
                "resolution": f"{width}x{height}",
                "process_resolution": f"{process_width}x{process_height}",
                "device_optimization": device_type
            }
        }
    
    def _interpolate_missing_landmarks_enhanced(self, landmarks_sequence: List) -> List:
        """拡張欠損ランドマーク補間"""
        valid_indices = [i for i, lm in enumerate(landmarks_sequence) if lm is not None]
        
        if len(valid_indices) < 2:
            logger.warning("Insufficient valid landmarks for interpolation")
            return [lm for lm in landmarks_sequence if lm is not None]
        
        for i, landmarks in enumerate(landmarks_sequence):
            if landmarks is None:
                # 前後の有効なフレームから補間
                prev_idx = max([idx for idx in valid_indices if idx < i], default=None)
                next_idx = min([idx for idx in valid_indices if idx > i], default=None)
                
                if prev_idx is not None and next_idx is not None:
                    # スプライン補間またはより高度な補間
                    alpha = (i - prev_idx) / (next_idx - prev_idx)
                    interpolated = self._interpolate_landmarks_enhanced(
                        landmarks_sequence[prev_idx], 
                        landmarks_sequence[next_idx], 
                        alpha
                    )
                    landmarks_sequence[i] = interpolated
        
        return [lm for lm in landmarks_sequence if lm is not None]
    
    def _interpolate_landmarks_enhanced(self, lm1: Dict, lm2: Dict, alpha: float) -> Dict:
        """拡張ランドマーク補間"""
        interpolated_landmarks = []
        
        for i in range(min(len(lm1['landmarks']), len(lm2['landmarks']))):
            landmark1 = lm1['landmarks'][i]
            landmark2 = lm2['landmarks'][i]
            
            # 3次スプライン風の補間（簡易版）
            smooth_alpha = 3 * alpha**2 - 2 * alpha**3  # スムーズステップ関数
            
            interpolated_landmarks.append({
                'x': landmark1['x'] * (1 - smooth_alpha) + landmark2['x'] * smooth_alpha,
                'y': landmark1['y'] * (1 - smooth_alpha) + landmark2['y'] * smooth_alpha,
                'z': landmark1['z'] * (1 - smooth_alpha) + landmark2['z'] * smooth_alpha,
                'visibility': landmark1['visibility'] * (1 - smooth_alpha) + landmark2['visibility'] * smooth_alpha
            })
        
        return {
            'frame': int(lm1['frame'] * (1 - alpha) + lm2['frame'] * alpha),
            'timestamp': lm1['timestamp'] * (1 - alpha) + lm2['timestamp'] * alpha,
            'landmarks': interpolated_landmarks
        }
    
    def _calculate_enhanced_overall_score(
        self,
        spatiotemporal_params,
        balance_metrics,
        compensation_alerts: List,
        quality_metrics: Dict[str, float]
    ) -> float:
        """拡張総合スコア計算"""
        # 時空間パラメータスコア（30%）
        speed_score = min(100, (spatiotemporal_params.gait_speed_ms / 1.4) * 100)
        cadence_score = 100 if 110 <= spatiotemporal_params.cadence_steps_per_min <= 130 else 70
        spatiotemporal_score = (speed_score + cadence_score) / 2
        
        # バランス・安定性スコア（30%）
        balance_score = balance_metrics.balance_stability_score
        
        # 代償動作ペナルティ（20%）
        critical_alerts = len([a for a in compensation_alerts if a.severity == 'critical'])
        high_alerts = len([a for a in compensation_alerts if a.severity == 'high'])
        compensation_penalty = critical_alerts * 20 + high_alerts * 10
        compensation_score = max(0, 100 - compensation_penalty)
        
        # 動画品質スコア（20%）
        quality_score = quality_metrics["video_quality"]
        
        # 重み付き総合スコア
        overall_score = (
            spatiotemporal_score * 0.3 +
            balance_score * 0.3 +
            compensation_score * 0.2 +
            quality_score * 0.2
        )
        
        return min(100, max(0, overall_score))
    
    def _generate_enhanced_recommendations(
        self,
        spatiotemporal_params,
        balance_metrics,
        joint_angles,
        compensation_alerts: List,
        quality_metrics: Dict[str, float]
    ) -> List[str]:
        """拡張改善提案生成"""
        recommendations = []
        
        # 時空間パラメータベースの推奨
        if spatiotemporal_params.gait_speed_ms < 1.0:
            recommendations.append("歩行速度が低下しています。下肢筋力強化訓練（スクワット、ランジ）を推奨します")
        
        if spatiotemporal_params.cadence_steps_per_min < 100:
            recommendations.append("歩行ピッチが低下しています。メトロノームを使用したリズム歩行練習が有効です")
        
        if spatiotemporal_params.stance_time_asymmetry_percent > 5:
            recommendations.append(f"立脚時間の非対称性（{spatiotemporal_params.stance_time_asymmetry_percent:.1f}%）が検出されました。片麻痺や疼痛の評価が必要です")
        
        # バランス指標ベースの推奨
        if balance_metrics.lateral_displacement_max_cm > 5:
            recommendations.append("左右動揺が大きいです。バランス訓練（片足立ち、タンデム歩行）を実施してください")
        
        if balance_metrics.balance_stability_score < 70:
            recommendations.append("バランス安定性が低下しています。体幹筋力強化と姿勢制御訓練が必要です")
        
        # 関節角度ベースの推奨
        if joint_angles and joint_angles.hip_rom_deg < 20:
            recommendations.append("股関節可動域が制限されています。股関節ストレッチと可動域訓練を行ってください")
        
        if joint_angles and joint_angles.knee_max_flexion_deg < 40:
            recommendations.append("膝関節屈曲が制限されています。膝関節可動域訓練が必要です")
        
        # 代償動作ベースの推奨
        for alert in compensation_alerts:
            if alert.alert_type == "trendelenburg_sign":
                recommendations.append("トレンデレンブルグ兆候が検出されました。中殿筋強化訓練（横歩き、ヒップアブダクション）を推奨します")
            elif alert.alert_type == "knee_valgus":
                recommendations.append("膝外反が検出されました。大腿四頭筋とハムストリングスの筋力バランス改善が必要です")
            elif alert.alert_type == "out_toeing":
                recommendations.append("アウトトゥーイングが検出されました。足部アライメント評価と歩行指導が有効です")
        
        # 品質ベースの推奨
        if quality_metrics.get("pose_confidence", 0) < 0.7:
            recommendations.append("姿勢検出精度が低いです。より良い照明環境と正面/側面からの撮影を推奨します")
        
        return list(dict.fromkeys(recommendations))[:8]  # 重複除去、最大8つに制限
    
    def _interpolate_landmarks(self, lm1: Dict, lm2: Dict, alpha: float) -> Dict:
        """2つのランドマーク間を線形補間"""
        interpolated_landmarks = []
        
        for i in range(len(lm1['landmarks'])):
            landmark1 = lm1['landmarks'][i]
            landmark2 = lm2['landmarks'][i]
            
            interpolated_landmarks.append({
                'x': landmark1['x'] * (1 - alpha) + landmark2['x'] * alpha,
                'y': landmark1['y'] * (1 - alpha) + landmark2['y'] * alpha,
                'z': landmark1['z'] * (1 - alpha) + landmark2['z'] * alpha,
                'visibility': landmark1['visibility'] * (1 - alpha) + landmark2['visibility'] * alpha
            })
        
        return {
            'frame': int(lm1['frame'] * (1 - alpha) + lm2['frame'] * alpha),
            'timestamp': lm1['timestamp'] * (1 - alpha) + lm2['timestamp'] * alpha,
            'landmarks': interpolated_landmarks
        }
    
    def _calculate_scale_factor(self, landmarks_data: List, user_height_cm: Optional[float]) -> float:
        """スケール係数計算（身長ベース）"""
        if not user_height_cm:
            logger.warning("User height not provided, using default scale")
            return 1.0
        
        # 頭頂から足首までの距離で身長推定
        avg_body_height_normalized = 0
        valid_frames = 0
        
        for frame_data in landmarks_data:
            if frame_data:
                landmarks = frame_data['landmarks']
                
                # 鼻（0番）と左足首（27番）の距離
                nose = landmarks[0]
                left_ankle = landmarks[27]
                
                if nose['visibility'] > 0.5 and left_ankle['visibility'] > 0.5:
                    body_height = math.sqrt(
                        (nose['x'] - left_ankle['x'])**2 + 
                        (nose['y'] - left_ankle['y'])**2
                    )
                    avg_body_height_normalized += body_height
                    valid_frames += 1
        
        if valid_frames == 0:
            logger.warning("Could not estimate body height from landmarks")
            return 1.0
        
        avg_body_height_normalized /= valid_frames
        
        # スケール係数計算（実身長 / 推定身長）
        estimated_height_cm = avg_body_height_normalized * 170  # 仮の基準値
        scale_factor = user_height_cm / estimated_height_cm
        
        logger.info(f"Calculated scale factor: {scale_factor}")
        return scale_factor
    
    
    
    def _assess_analysis_quality(
        self, landmarks_data: List, gait_cycles: List[GaitCycle]
    ) -> Dict[str, float]:
        """分析品質評価"""
        # ポーズ検出信頼度
        confidence_scores = []
        for frame_data in landmarks_data:
            if frame_data:
                avg_visibility = np.mean([lm['visibility'] for lm in frame_data['landmarks']])
                confidence_scores.append(avg_visibility)
        
        pose_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
        
        # 動画品質スコア
        video_quality = min(100, pose_confidence * 100)
        
        # 歩行周期検出品質
        if len(gait_cycles) >= 3:
            cycle_quality = 100
        elif len(gait_cycles) >= 2:
            cycle_quality = 80
        else:
            cycle_quality = 50
        
        return {
            "pose_confidence": pose_confidence,
            "video_quality": video_quality,
            "cycle_quality": cycle_quality
        }
    
    def _calculate_overall_score(
        self, 
        spatiotemporal: SpatiotemporalParameters,
        symmetry: SymmetryIndices,
        quality: Dict[str, float]
    ) -> float:
        """総合歩行スコア計算"""
        # 正常値との比較でスコア計算
        speed_score = min(100, (spatiotemporal.gait_speed_ms / 1.4) * 100)  # 1.4m/sを基準
        symmetry_score = symmetry.overall_symmetry_score
        quality_score = quality["video_quality"]
        
        # 重み付き平均
        overall_score = (speed_score * 0.3 + symmetry_score * 0.4 + quality_score * 0.3)
        return min(100, max(0, overall_score))
    
    def _generate_comprehensive_recommendations(
        self, 
        spatiotemporal: SpatiotemporalParameters,
        symmetry: SymmetryIndices,
        joint_angles: Optional[JointAngles],
        quality_metrics: Dict[str, float]
    ) -> List[str]:
        """包括的改善提案生成"""
        recommendations = []
        
        # 時空間パラメータベースの推奨
        speed_recommendations = self._get_speed_recommendations(spatiotemporal)
        recommendations.extend(speed_recommendations)
        
        # 対称性ベースの推奨
        symmetry_recommendations = self.symmetry_analyzer.generate_symmetry_recommendations(symmetry)
        recommendations.extend(symmetry_recommendations)
        
        # 関節角度ベースの推奨
        if joint_angles:
            joint_recommendations = self._get_joint_recommendations(joint_angles)
            recommendations.extend(joint_recommendations)
        
        # 品質ベースの推奨
        quality_recommendations = self._get_quality_recommendations(quality_metrics)
        recommendations.extend(quality_recommendations)
        
        # 重複除去
        unique_recommendations = list(dict.fromkeys(recommendations))
        
        return unique_recommendations[:5]  # 最大5つに制限
    
    def _get_speed_recommendations(self, spatiotemporal: SpatiotemporalParameters) -> List[str]:
        """歩行速度ベースの推奨事項"""
        recommendations = []
        
        if spatiotemporal.gait_speed_ms < 1.0:
            recommendations.append("歩行速度が低下しています。下肢筋力強化と歩行練習を推奨します")
        elif spatiotemporal.gait_speed_ms > 1.8:
            recommendations.append("歩行速度が速すぎる可能性があります。安全な歩行速度を心がけてください")
        
        if spatiotemporal.cadence_steps_per_min < 100:
            recommendations.append("ケイデンスが低下しています。リズミカルな歩行練習が有効です")
        elif spatiotemporal.cadence_steps_per_min > 130:
            recommendations.append("歩調が速すぎます。ゆっくりとした歩行を心がけてください")
        
        if spatiotemporal.stride_length_m < 1.2:
            recommendations.append("ストライド長が短縮しています。股関節可動域訓練を行ってください")
        
        return recommendations
    
    def _get_joint_recommendations(self, joint_angles: JointAngles) -> List[str]:
        """関節角度ベースの推奨事項"""
        recommendations = []
        
        if joint_angles.hip_flexion_deg:
            max_hip_flexion = max(joint_angles.hip_flexion_deg)
            if max_hip_flexion < 20:
                recommendations.append("股関節屈曲が制限されています。股関節ストレッチと可動域訓練を行ってください")
            elif max_hip_flexion > 50:
                recommendations.append("股関節の過度な屈曲が見られます。体幹安定性の向上が必要です")
        
        if joint_angles.knee_flexion_deg:
            max_knee_flexion = max(joint_angles.knee_flexion_deg)
            if max_knee_flexion < 40:
                recommendations.append("膝関節屈曲が制限されています。膝関節可動域訓練を行ってください")
            elif max_knee_flexion > 80:
                recommendations.append("膝関節の過度な屈曲が見られます。歩行パターンの修正が必要です")
        
        if joint_angles.pelvic_drop_deg:
            max_pelvic_drop = max([abs(x) for x in joint_angles.pelvic_drop_deg])
            if max_pelvic_drop > 5:
                recommendations.append("骨盤の動揺が大きいです。中殿筋強化とバランス訓練を推奨します")
        
        return recommendations
    
    def _get_quality_recommendations(self, quality_metrics: Dict[str, float]) -> List[str]:
        """品質ベースの推奨事項"""
        recommendations = []
        
        if quality_metrics.get("pose_confidence", 0) < 0.7:
            recommendations.append("姿勢検出の精度が低いです。より良い照明環境での再測定を推奨します")
        
        if quality_metrics.get("cycle_quality", 0) < 80:
            recommendations.append("歩行周期の検出が不十分です。より長い距離での歩行測定を行ってください")
        
        return recommendations
    
    async def get_analysis_result(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """分析結果取得（将来のデータベース連携用）"""
        # TODO: データベースから結果を取得
        logger.info("Getting analysis result", analysis_id=analysis_id)
        return None
