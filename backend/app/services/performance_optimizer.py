"""
30秒処理時間最適化
Performance Optimizer for 30-second processing target
"""

import asyncio
import time
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Dict, Any, List, Optional
import numpy as np
from functools import lru_cache

from app.core.advanced_logger import get_logger

logger = get_logger(__name__)


class PerformanceOptimizer:
    """30秒処理時間最適化クラス"""
    
    def __init__(self):
        self.target_processing_time = 30.0  # 目標30秒
        self.cpu_cores = mp.cpu_count()
        self.optimization_settings = {
            'parallel_processing': True,
            'frame_reduction': True,
            'fast_mode_threshold': 25.0,  # 25秒を超えたら高速モード
            'max_workers': min(4, self.cpu_cores),
            'memory_optimization': True,
            'cache_optimization': True
        }
        
        # 処理時間監視
        self.processing_times = {
            'landmark_extraction': 0.0,
            'gait_cycle_detection': 0.0,
            'spatiotemporal_analysis': 0.0,
            'joint_angle_calculation': 0.0,
            'balance_analysis': 0.0,
            'compensation_detection': 0.0,
            'output_generation': 0.0
        }
        
    async def optimize_gait_analysis_pipeline(
        self,
        video_path: str,
        gait_service,
        analysis_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        最適化された歩行分析パイプライン
        
        Args:
            video_path: 動画ファイルパス
            gait_service: 歩行分析サービス
            analysis_params: 分析パラメータ
            
        Returns:
            Dict: 最適化された分析結果
        """
        start_time = time.time()
        
        logger.info("Starting optimized gait analysis pipeline", 
                   target_time=self.target_processing_time)
        
        # 1. 動画前処理・最適化
        optimized_video_info = await self._optimize_video_preprocessing(
            video_path, analysis_params.get('target_fps', 60)
        )
        
        # 2. 並列処理によるランドマーク抽出
        landmarks_data = await self._parallel_landmark_extraction(
            video_path, optimized_video_info, gait_service
        )
        
        # 3. 時間監視とダイナミック最適化
        elapsed_time = time.time() - start_time
        if elapsed_time > self.optimization_settings['fast_mode_threshold']:
            logger.warning("Entering fast processing mode", elapsed_time=elapsed_time)
            return await self._fast_mode_analysis(
                landmarks_data, gait_service, analysis_params
            )
        
        # 4. 並列処理による分析
        analysis_result = await self._parallel_analysis_pipeline(
            landmarks_data, gait_service, analysis_params
        )
        
        # 5. 最適化された出力生成
        if analysis_params.get('analysis_mode') == 'detailed':
            analysis_result = await self._optimized_output_generation(
                analysis_result, gait_service, video_path
            )
        
        total_time = time.time() - start_time
        analysis_result['optimization_info'] = {
            'total_processing_time': total_time,
            'target_achieved': total_time <= self.target_processing_time,
            'optimization_applied': True,
            'processing_breakdown': self.processing_times,
            'performance_score': self._calculate_performance_score(total_time)
        }
        
        logger.info("Optimized analysis completed",
                   total_time=total_time,
                   target_achieved=total_time <= self.target_processing_time)
        
        return analysis_result
    
    async def _optimize_video_preprocessing(
        self, 
        video_path: str, 
        target_fps: int
    ) -> Dict[str, Any]:
        """動画前処理最適化"""
        start_time = time.time()
        
        import cv2
        cap = cv2.VideoCapture(video_path)
        
        original_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / original_fps
        
        cap.release()
        
        # 最適化パラメータ計算
        optimized_params = {
            'original_fps': original_fps,
            'target_fps': min(target_fps, original_fps),
            'frame_skip': max(1, int(original_fps / target_fps)),
            'process_width': min(width, 640),  # 処理用解像度制限
            'process_height': min(height, 480),
            'estimated_process_frames': int(total_frames / max(1, int(original_fps / target_fps))),
            'duration': duration
        }
        
        # 処理時間予測
        estimated_time = self._estimate_processing_time(optimized_params)
        if estimated_time > self.target_processing_time:
            # さらなる最適化が必要
            optimized_params = self._apply_aggressive_optimization(optimized_params)
        
        self.processing_times['video_preprocessing'] = time.time() - start_time
        
        return optimized_params
    
    async def _parallel_landmark_extraction(
        self,
        video_path: str,
        video_info: Dict[str, Any],
        gait_service
    ) -> Dict[str, Any]:
        """並列ランドマーク抽出"""
        start_time = time.time()
        
        # フレーム分割による並列処理
        if self.optimization_settings['parallel_processing'] and video_info['estimated_process_frames'] > 100:
            landmarks_data = await self._extract_landmarks_parallel(
                video_path, video_info, gait_service
            )
        else:
            # 標準処理
            landmarks_data = await gait_service._extract_pose_landmarks_enhanced(
                video_path, video_info['target_fps'], 'mobile'
            )
        
        self.processing_times['landmark_extraction'] = time.time() - start_time
        return landmarks_data
    
    async def _extract_landmarks_parallel(
        self,
        video_path: str,
        video_info: Dict[str, Any],
        gait_service
    ) -> Dict[str, Any]:
        """並列ランドマーク抽出実装"""
        
        # フレーム範囲分割
        total_frames = video_info['estimated_process_frames']
        chunk_size = max(50, total_frames // self.optimization_settings['max_workers'])
        frame_chunks = [
            (i, min(i + chunk_size, total_frames))
            for i in range(0, total_frames, chunk_size)
        ]
        
        # 並列処理実行
        with ThreadPoolExecutor(max_workers=self.optimization_settings['max_workers']) as executor:
            chunk_results = await asyncio.gather(*[
                self._process_frame_chunk(video_path, start_frame, end_frame, video_info, gait_service)
                for start_frame, end_frame in frame_chunks
            ])
        
        # 結果統合
        return self._merge_landmark_chunks(chunk_results, video_info)
    
    async def _process_frame_chunk(
        self,
        video_path: str,
        start_frame: int,
        end_frame: int,
        video_info: Dict[str, Any],
        gait_service
    ) -> List[Dict]:
        """フレームチャンク処理"""
        import cv2
        
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame * video_info['frame_skip'])
        
        landmarks_chunk = []
        
        for frame_idx in range(start_frame, end_frame):
            ret, frame = cap.read()
            if not ret:
                break
            
            # フレームサイズ最適化
            if frame.shape[1] > video_info['process_width']:
                frame = cv2.resize(frame, (video_info['process_width'], video_info['process_height']))
            
            # RGB変換
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # ポーズ検出
            results = gait_service.pose.process(frame_rgb)
            
            if results.pose_landmarks:
                landmarks = [
                    {
                        'x': lm.x, 'y': lm.y, 'z': lm.z, 'visibility': lm.visibility
                    }
                    for lm in results.pose_landmarks.landmark
                ]
                
                landmarks_chunk.append({
                    'frame': frame_idx,
                    'timestamp': frame_idx / video_info['target_fps'],
                    'landmarks': landmarks
                })
            else:
                landmarks_chunk.append(None)
        
        cap.release()
        return landmarks_chunk
    
    def _merge_landmark_chunks(
        self, 
        chunk_results: List[List[Dict]], 
        video_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ランドマークチャンク結果統合"""
        
        landmarks_sequence = []
        confidence_scores = []
        
        for chunk in chunk_results:
            for frame_data in chunk:
                if frame_data:
                    landmarks_sequence.append(frame_data)
                    avg_visibility = np.mean([lm['visibility'] for lm in frame_data['landmarks']])
                    confidence_scores.append(avg_visibility)
                else:
                    landmarks_sequence.append(None)
                    confidence_scores.append(0.0)
        
        return {
            "landmarks": landmarks_sequence,
            "fps": video_info['target_fps'],
            "confidence_scores": confidence_scores,
            "video_info": video_info
        }
    
    async def _parallel_analysis_pipeline(
        self,
        landmarks_data: Dict[str, Any],
        gait_service,
        analysis_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """並列分析パイプライン"""
        
        # 並列実行可能な分析タスク
        analysis_tasks = []
        
        # スケール係数計算
        scale_factor = gait_service._calculate_scale_factor(
            landmarks_data["landmarks"], 
            analysis_params.get('user_height_cm')
        )
        
        # 歩行周期検出
        gait_cycles_task = asyncio.create_task(
            self._async_gait_cycle_detection(landmarks_data, gait_service)
        )
        analysis_tasks.append(('gait_cycles', gait_cycles_task))
        
        # 重心・バランス分析
        balance_task = asyncio.create_task(
            self._async_balance_analysis(landmarks_data, gait_service, scale_factor)
        )
        analysis_tasks.append(('balance_metrics', balance_task))
        
        # 並列実行
        task_results = {}
        for task_name, task in analysis_tasks:
            try:
                task_results[task_name] = await task
            except Exception as e:
                logger.error(f"Task {task_name} failed", error=str(e))
                task_results[task_name] = None
        
        # 依存関係のある分析（順次実行）
        gait_cycles = task_results['gait_cycles'] or []
        
        # 拡張時空間パラメータ
        spatiotemporal_params = gait_service.enhanced_spatiotemporal_analyzer.analyze_detailed_spatiotemporal_parameters(
            gait_cycles, landmarks_data["landmarks"], scale_factor, landmarks_data["fps"]
        )
        
        # 拡張関節角度
        joint_angles = None
        if analysis_params.get('analysis_mode') in ["standard", "detailed"]:
            joint_angles = gait_service.enhanced_joint_calculator.calculate_enhanced_joint_angles(
                landmarks_data["landmarks"], gait_cycles, landmarks_data["fps"]
            )
        
        # 代償動作検出
        compensation_alerts = gait_service.compensation_detector.detect_compensation_movements(
            landmarks_data["landmarks"], joint_angles, gait_cycles
        )
        
        return {
            'landmarks_data': landmarks_data,
            'gait_cycles': gait_cycles,
            'scale_factor': scale_factor,
            'spatiotemporal_params': spatiotemporal_params,
            'joint_angles': joint_angles,
            'balance_metrics': task_results['balance_metrics'],
            'compensation_alerts': compensation_alerts
        }
    
    async def _async_gait_cycle_detection(self, landmarks_data: Dict, gait_service):
        """非同期歩行周期検出"""
        start_time = time.time()
        result = gait_service.gait_detector.detect_gait_cycles(
            landmarks_data["landmarks"], 
            landmarks_data["fps"]
        )
        self.processing_times['gait_cycle_detection'] = time.time() - start_time
        return result
    
    async def _async_balance_analysis(self, landmarks_data: Dict, gait_service, scale_factor: float):
        """非同期バランス分析"""
        start_time = time.time()
        result = gait_service.com_analyzer.analyze_center_of_mass(
            landmarks_data["landmarks"], scale_factor, 'side'
        )
        self.processing_times['balance_analysis'] = time.time() - start_time
        return result
    
    async def _fast_mode_analysis(
        self,
        landmarks_data: Dict[str, Any],
        gait_service,
        analysis_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """高速モード分析（簡略版）"""
        
        logger.info("Executing fast mode analysis")
        
        # 基本的な分析のみ実行
        scale_factor = gait_service._calculate_scale_factor(
            landmarks_data["landmarks"], 
            analysis_params.get('user_height_cm')
        )
        
        # 簡略歩行周期検出
        gait_cycles = gait_service.gait_detector.detect_gait_cycles(
            landmarks_data["landmarks"], 
            landmarks_data["fps"]
        )
        
        # 基本時空間パラメータのみ
        spatiotemporal_params = gait_service.spatiotemporal_analyzer.analyze_spatiotemporal_parameters(
            gait_cycles, scale_factor
        )
        
        # 基本品質評価
        quality_metrics = gait_service._assess_analysis_quality(
            landmarks_data["landmarks"], 
            gait_cycles
        )
        
        return {
            'spatiotemporal_params': spatiotemporal_params,
            'gait_cycles': gait_cycles,
            'video_quality_score': quality_metrics["video_quality"],
            'pose_detection_confidence': quality_metrics["pose_confidence"],
            'gait_cycles_detected': len(gait_cycles),
            'overall_gait_score': 70.0,  # 簡易スコア
            'recommendations': ["高速処理モードのため簡易分析を実行しました"],
            'fast_mode': True,
            'analysis_settings': analysis_params
        }
    
    async def _optimized_output_generation(
        self,
        analysis_result: Dict[str, Any],
        gait_service,
        video_path: str
    ) -> Dict[str, Any]:
        """最適化された出力生成"""
        start_time = time.time()
        
        # 軽量版出力生成（動画処理を簡略化）
        try:
            enhanced_output = gait_service.video_processor.create_enhanced_output(
                video_path,
                analysis_result['landmarks_data']['landmarks'],
                analysis_result['joint_angles'],
                analysis_result['spatiotemporal_params'],
                analysis_result['balance_metrics'],
                analysis_result['compensation_alerts']
            )
            analysis_result['enhanced_output'] = enhanced_output
        except Exception as e:
            logger.warning("Enhanced output generation failed, using basic output", error=str(e))
            analysis_result['enhanced_output'] = None
        
        self.processing_times['output_generation'] = time.time() - start_time
        return analysis_result
    
    def _estimate_processing_time(self, video_params: Dict[str, Any]) -> float:
        """処理時間予測"""
        
        # 基本処理時間（経験値）
        base_time_per_frame = 0.1  # 秒/フレーム
        
        # フレーム数ベースの推定
        estimated_frames = video_params['estimated_process_frames']
        base_time = estimated_frames * base_time_per_frame
        
        # 解像度補正
        resolution_factor = (video_params['process_width'] * video_params['process_height']) / (640 * 480)
        resolution_time = base_time * resolution_factor
        
        # 分析処理時間
        analysis_overhead = 5.0  # 秒
        
        total_estimated_time = resolution_time + analysis_overhead
        
        return total_estimated_time
    
    def _apply_aggressive_optimization(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """積極的最適化適用"""
        
        # フレームレート削減
        params['target_fps'] = min(params['target_fps'], 30)
        params['frame_skip'] = max(params['frame_skip'], 2)
        
        # 解像度削減
        params['process_width'] = min(params['process_width'], 480)
        params['process_height'] = min(params['process_height'], 360)
        
        # フレーム数再計算
        params['estimated_process_frames'] = int(
            params['estimated_process_frames'] * params['target_fps'] / params['original_fps']
        )
        
        logger.info("Applied aggressive optimization", optimized_params=params)
        
        return params
    
    def _calculate_performance_score(self, processing_time: float) -> float:
        """パフォーマンススコア計算"""
        
        if processing_time <= self.target_processing_time:
            # 目標時間内：100-90点
            score = 100 - (processing_time / self.target_processing_time) * 10
        else:
            # 目標時間超過：90-0点
            overtime_ratio = (processing_time - self.target_processing_time) / self.target_processing_time
            score = max(0, 90 - overtime_ratio * 90)
        
        return min(100, max(0, score))
    
    @lru_cache(maxsize=128)
    def get_optimization_recommendations(self, processing_time: float) -> List[str]:
        """最適化推奨事項"""
        recommendations = []
        
        if processing_time > self.target_processing_time:
            recommendations.append("処理時間が目標を超過しています。動画解像度または長さの調整を検討してください")
            
        if processing_time > 45:
            recommendations.append("処理時間が大幅に超過しています。高速モードまたは簡易分析モードを使用してください")
            
        if processing_time <= 20:
            recommendations.append("優秀な処理時間です。詳細分析モードでより高精度な結果を取得できます")
        
        return recommendations