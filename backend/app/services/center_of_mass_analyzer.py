"""
重心・バランス分析器
Center of Mass and Balance Analysis
"""

import numpy as np
import math
from typing import List, Dict, Any, Optional, Tuple
from app.models.gait_models import BalanceMetrics
from app.core.advanced_logger import get_logger

logger = get_logger(__name__)


class CenterOfMassAnalyzer:
    """重心・バランス分析クラス"""
    
    def __init__(self):
        # MediaPipe人体セグメント重量比率（Dempster, 1955）
        self.segment_weights = {
            'head': 0.073,
            'trunk': 0.507,
            'upper_arm': 0.026,
            'forearm': 0.016,
            'hand': 0.007,
            'thigh': 0.103,
            'shank': 0.043,
            'foot': 0.015
        }
        
        # MediaPipeランドマークインデックス
        self.landmark_indices = {
            'nose': 0, 'left_eye_inner': 1, 'left_eye': 2, 'left_eye_outer': 3,
            'right_eye_inner': 4, 'right_eye': 5, 'right_eye_outer': 6,
            'left_ear': 7, 'right_ear': 8, 'mouth_left': 9, 'mouth_right': 10,
            'left_shoulder': 11, 'right_shoulder': 12,
            'left_elbow': 13, 'right_elbow': 14,
            'left_wrist': 15, 'right_wrist': 16,
            'left_pinky': 17, 'right_pinky': 18,
            'left_index': 19, 'right_index': 20,
            'left_thumb': 21, 'right_thumb': 22,
            'left_hip': 23, 'right_hip': 24,
            'left_knee': 25, 'right_knee': 26,
            'left_ankle': 27, 'right_ankle': 28,
            'left_heel': 29, 'right_heel': 30,
            'left_foot_index': 31, 'right_foot_index': 32
        }
    
    def analyze_center_of_mass(
        self, 
        landmarks_data: List[Dict], 
        scale_factor: float = 1.0,
        camera_position: str = "side"
    ) -> BalanceMetrics:
        """
        重心・バランス分析メイン処理
        
        Args:
            landmarks_data: ランドマークデータ
            scale_factor: スケール係数
            camera_position: カメラ位置（side/posterior/anterior）
            
        Returns:
            BalanceMetrics: 重心・バランス指標
        """
        logger.info("Starting center of mass analysis", 
                   frames=len(landmarks_data), 
                   camera_position=camera_position)
        
        com_positions = []
        timestamps = []
        
        for frame_data in landmarks_data:
            if frame_data and frame_data['landmarks']:
                # 全身重心計算
                com_x, com_y = self._calculate_whole_body_com(
                    frame_data['landmarks'], 
                    camera_position
                )
                
                com_positions.append((com_x, com_y))
                timestamps.append(frame_data['timestamp'])
        
        if len(com_positions) < 10:
            logger.warning("Insufficient COM data points", points=len(com_positions))
            return self._create_empty_balance_metrics()
        
        # 重心軌跡分析
        lateral_displacement = self._calculate_lateral_displacement(
            com_positions, scale_factor, camera_position
        )
        vertical_displacement = self._calculate_vertical_displacement(
            com_positions, scale_factor
        )
        anterior_posterior = self._calculate_anterior_posterior_displacement(
            com_positions, scale_factor, camera_position
        )
        
        # バランス安定性スコア算出
        stability_score = self._calculate_balance_stability_score(
            lateral_displacement, vertical_displacement
        )
        
        # 重心投影線データ（2Dマップ用）
        projection_x, projection_y = self._prepare_projection_data(
            com_positions, scale_factor
        )
        
        balance_metrics = BalanceMetrics(
            com_lateral_displacement_cm=lateral_displacement,
            com_anterior_posterior_cm=anterior_posterior,
            com_vertical_displacement_cm=vertical_displacement,
            com_projection_x=projection_x,
            com_projection_y=projection_y,
            lateral_displacement_max_cm=max(lateral_displacement) if lateral_displacement else 0.0,
            vertical_displacement_max_cm=max(vertical_displacement) if vertical_displacement else 0.0,
            balance_stability_score=stability_score
        )
        
        logger.info("Center of mass analysis completed",
                   lateral_max=balance_metrics.lateral_displacement_max_cm,
                   vertical_max=balance_metrics.vertical_displacement_max_cm,
                   stability_score=stability_score)
        
        return balance_metrics
    
    def _calculate_whole_body_com(
        self, 
        landmarks: List[Dict], 
        camera_position: str
    ) -> Tuple[float, float]:
        """全身重心計算"""
        total_weighted_x = 0.0
        total_weighted_y = 0.0
        total_weight = 0.0
        
        # 頭部重心
        head_x, head_y = self._get_segment_com(landmarks, 'head')
        if head_x is not None:
            total_weighted_x += head_x * self.segment_weights['head']
            total_weighted_y += head_y * self.segment_weights['head']
            total_weight += self.segment_weights['head']
        
        # 体幹重心
        trunk_x, trunk_y = self._get_segment_com(landmarks, 'trunk')
        if trunk_x is not None:
            total_weighted_x += trunk_x * self.segment_weights['trunk']
            total_weighted_y += trunk_y * self.segment_weights['trunk']
            total_weight += self.segment_weights['trunk']
        
        # 左右上肢重心
        for side in ['left', 'right']:
            # 上腕
            upper_arm_x, upper_arm_y = self._get_segment_com(landmarks, f'{side}_upper_arm')
            if upper_arm_x is not None:
                total_weighted_x += upper_arm_x * self.segment_weights['upper_arm']
                total_weighted_y += upper_arm_y * self.segment_weights['upper_arm']
                total_weight += self.segment_weights['upper_arm']
            
            # 前腕
            forearm_x, forearm_y = self._get_segment_com(landmarks, f'{side}_forearm')
            if forearm_x is not None:
                total_weighted_x += forearm_x * self.segment_weights['forearm']
                total_weighted_y += forearm_y * self.segment_weights['forearm']
                total_weight += self.segment_weights['forearm']
            
            # 手
            hand_x, hand_y = self._get_segment_com(landmarks, f'{side}_hand')
            if hand_x is not None:
                total_weighted_x += hand_x * self.segment_weights['hand']
                total_weighted_y += hand_y * self.segment_weights['hand']
                total_weight += self.segment_weights['hand']
            
            # 大腿
            thigh_x, thigh_y = self._get_segment_com(landmarks, f'{side}_thigh')
            if thigh_x is not None:
                total_weighted_x += thigh_x * self.segment_weights['thigh']
                total_weighted_y += thigh_y * self.segment_weights['thigh']
                total_weight += self.segment_weights['thigh']
            
            # 下腿
            shank_x, shank_y = self._get_segment_com(landmarks, f'{side}_shank')
            if shank_x is not None:
                total_weighted_x += shank_x * self.segment_weights['shank']
                total_weighted_y += shank_y * self.segment_weights['shank']
                total_weight += self.segment_weights['shank']
            
            # 足
            foot_x, foot_y = self._get_segment_com(landmarks, f'{side}_foot')
            if foot_x is not None:
                total_weighted_x += foot_x * self.segment_weights['foot']
                total_weighted_y += foot_y * self.segment_weights['foot']
                total_weight += self.segment_weights['foot']
        
        if total_weight > 0:
            return total_weighted_x / total_weight, total_weighted_y / total_weight
        else:
            return 0.0, 0.0
    
    def _get_segment_com(self, landmarks: List[Dict], segment: str) -> Tuple[Optional[float], Optional[float]]:
        """セグメント重心計算"""
        if segment == 'head':
            # 頭部：鼻を重心とする
            nose = landmarks[self.landmark_indices['nose']]
            if nose['visibility'] > 0.5:
                return nose['x'], nose['y']
        
        elif segment == 'trunk':
            # 体幹：肩と腰の中点
            left_shoulder = landmarks[self.landmark_indices['left_shoulder']]
            right_shoulder = landmarks[self.landmark_indices['right_shoulder']]
            left_hip = landmarks[self.landmark_indices['left_hip']]
            right_hip = landmarks[self.landmark_indices['right_hip']]
            
            if all(lm['visibility'] > 0.5 for lm in [left_shoulder, right_shoulder, left_hip, right_hip]):
                shoulder_mid_x = (left_shoulder['x'] + right_shoulder['x']) / 2
                shoulder_mid_y = (left_shoulder['y'] + right_shoulder['y']) / 2
                hip_mid_x = (left_hip['x'] + right_hip['x']) / 2
                hip_mid_y = (left_hip['y'] + right_hip['y']) / 2
                
                return (shoulder_mid_x + hip_mid_x) / 2, (shoulder_mid_y + hip_mid_y) / 2
        
        elif 'upper_arm' in segment:
            side = segment.split('_')[0]
            shoulder = landmarks[self.landmark_indices[f'{side}_shoulder']]
            elbow = landmarks[self.landmark_indices[f'{side}_elbow']]
            
            if shoulder['visibility'] > 0.5 and elbow['visibility'] > 0.5:
                return (shoulder['x'] + elbow['x']) / 2, (shoulder['y'] + elbow['y']) / 2
        
        elif 'forearm' in segment:
            side = segment.split('_')[0]
            elbow = landmarks[self.landmark_indices[f'{side}_elbow']]
            wrist = landmarks[self.landmark_indices[f'{side}_wrist']]
            
            if elbow['visibility'] > 0.5 and wrist['visibility'] > 0.5:
                return (elbow['x'] + wrist['x']) / 2, (elbow['y'] + wrist['y']) / 2
        
        elif 'hand' in segment:
            side = segment.split('_')[0]
            wrist = landmarks[self.landmark_indices[f'{side}_wrist']]
            if wrist['visibility'] > 0.5:
                return wrist['x'], wrist['y']
        
        elif 'thigh' in segment:
            side = segment.split('_')[0]
            hip = landmarks[self.landmark_indices[f'{side}_hip']]
            knee = landmarks[self.landmark_indices[f'{side}_knee']]
            
            if hip['visibility'] > 0.5 and knee['visibility'] > 0.5:
                return (hip['x'] + knee['x']) / 2, (hip['y'] + knee['y']) / 2
        
        elif 'shank' in segment:
            side = segment.split('_')[0]
            knee = landmarks[self.landmark_indices[f'{side}_knee']]
            ankle = landmarks[self.landmark_indices[f'{side}_ankle']]
            
            if knee['visibility'] > 0.5 and ankle['visibility'] > 0.5:
                return (knee['x'] + ankle['x']) / 2, (knee['y'] + ankle['y']) / 2
        
        elif 'foot' in segment:
            side = segment.split('_')[0]
            ankle = landmarks[self.landmark_indices[f'{side}_ankle']]
            foot_index = landmarks[self.landmark_indices[f'{side}_foot_index']]
            
            if ankle['visibility'] > 0.5 and foot_index['visibility'] > 0.5:
                return (ankle['x'] + foot_index['x']) / 2, (ankle['y'] + foot_index['y']) / 2
        
        return None, None
    
    def _calculate_lateral_displacement(
        self, 
        com_positions: List[Tuple[float, float]], 
        scale_factor: float,
        camera_position: str
    ) -> List[float]:
        """左右移動幅計算（cm）"""
        if camera_position == "side":
            # 側面からの撮影：X座標が左右移動
            x_positions = [pos[0] for pos in com_positions]
        else:
            # 後方/前方からの撮影：X座標が左右移動
            x_positions = [pos[0] for pos in com_positions]
        
        # 基準点からの偏差をcmに変換
        mean_x = np.mean(x_positions)
        lateral_displacements = [(x - mean_x) * scale_factor * 100 for x in x_positions]
        
        return lateral_displacements
    
    def _calculate_vertical_displacement(
        self, 
        com_positions: List[Tuple[float, float]], 
        scale_factor: float
    ) -> List[float]:
        """上下変位計算（cm）"""
        y_positions = [pos[1] for pos in com_positions]
        
        # 平均高さからの偏差をcmに変換
        mean_y = np.mean(y_positions)
        vertical_displacements = [(mean_y - y) * scale_factor * 100 for y in y_positions]  # Y軸反転
        
        return vertical_displacements
    
    def _calculate_anterior_posterior_displacement(
        self, 
        com_positions: List[Tuple[float, float]], 
        scale_factor: float,
        camera_position: str
    ) -> List[float]:
        """前後移動幅計算（cm）"""
        if camera_position == "side":
            # 側面からの撮影：Y座標の変化が前後移動を反映
            # ただし、歩行中の前後移動は限定的
            return [0.0] * len(com_positions)
        else:
            # 後方/前方からの撮影：Y座標が前後移動
            y_positions = [pos[1] for pos in com_positions]
            mean_y = np.mean(y_positions)
            anterior_posterior = [(y - mean_y) * scale_factor * 100 for y in y_positions]
            return anterior_posterior
    
    def _calculate_balance_stability_score(
        self, 
        lateral_displacement: List[float], 
        vertical_displacement: List[float]
    ) -> float:
        """バランス安定性スコア計算（0-100）"""
        if not lateral_displacement or not vertical_displacement:
            return 0.0
        
        # 変動係数（CV）を基にしたスコア
        lateral_cv = np.std(lateral_displacement) / (np.mean(np.abs(lateral_displacement)) + 1e-6)
        vertical_cv = np.std(vertical_displacement) / (np.mean(np.abs(vertical_displacement)) + 1e-6)
        
        # 正常範囲の設定
        normal_lateral_cv = 0.3  # 正常値
        normal_vertical_cv = 0.2  # 正常値
        
        # スコア計算（変動が小さいほど高スコア）
        lateral_score = max(0, 100 - (lateral_cv / normal_lateral_cv) * 100)
        vertical_score = max(0, 100 - (vertical_cv / normal_vertical_cv) * 100)
        
        # 重み付き平均
        stability_score = lateral_score * 0.6 + vertical_score * 0.4
        
        return min(100, max(0, stability_score))
    
    def _prepare_projection_data(
        self, 
        com_positions: List[Tuple[float, float]], 
        scale_factor: float
    ) -> Tuple[List[float], List[float]]:
        """重心投影線データ準備（2Dマップ表示用）"""
        projection_x = [(pos[0] * scale_factor * 100) for pos in com_positions]
        projection_y = [(pos[1] * scale_factor * 100) for pos in com_positions]
        
        return projection_x, projection_y
    
    def _create_empty_balance_metrics(self) -> BalanceMetrics:
        """空のバランス指標作成"""
        return BalanceMetrics(
            com_lateral_displacement_cm=[],
            com_anterior_posterior_cm=[],
            com_vertical_displacement_cm=[],
            com_projection_x=[],
            com_projection_y=[],
            lateral_displacement_max_cm=0.0,
            vertical_displacement_max_cm=0.0,
            balance_stability_score=0.0
        )