"""
代償動作検出器
Compensation Movement Detector
"""

import numpy as np
import math
from typing import List, Dict, Any, Optional, Tuple
from app.models.gait_models import CompensationAlert, JointAngles
from app.core.advanced_logger import get_logger

logger = get_logger(__name__)


class CompensationDetector:
    """代償動作検出クラス"""
    
    def __init__(self):
        # 代償動作検出のしきい値設定
        self.thresholds = {
            # アウト/イントゥーイング（足部回旋）
            'out_toeing_deg': 15.0,    # 外旋15度以上
            'in_toeing_deg': -10.0,    # 内旋10度以上
            
            # 膝外反/内反
            'knee_valgus_deg': 10.0,   # 外反10度以上
            'knee_varus_deg': -5.0,    # 内反5度以上
            
            # トレンデレンブルグ兆候（中殿筋機能低下）
            'trendelenburg_deg': 5.0,  # 骨盤傾斜5度以上
            
            # ペルビックドロップ
            'pelvic_drop_deg': 8.0,    # 骨盤傾斜8度以上
            
            # ラテラルスウェイ
            'lateral_sway_cm': 5.0,    # 左右動揺5cm以上
            
            # 過度な体幹代償
            'trunk_rotation_deg': 15.0,  # 体幹回旋15度以上
            'trunk_lean_deg': 10.0,      # 体幹側屈10度以上
        }
        
        # MediaPipeランドマークインデックス
        self.landmark_indices = {
            'left_shoulder': 11, 'right_shoulder': 12,
            'left_hip': 23, 'right_hip': 24,
            'left_knee': 25, 'right_knee': 26,
            'left_ankle': 27, 'right_ankle': 28,
            'left_heel': 29, 'right_heel': 30,
            'left_foot_index': 31, 'right_foot_index': 32
        }
    
    def detect_compensation_movements(
        self, 
        landmarks_data: List[Dict], 
        joint_angles: JointAngles,
        gait_cycles: List[Dict]
    ) -> List[CompensationAlert]:
        """
        代償動作検出メイン処理
        
        Args:
            landmarks_data: ランドマークデータ
            joint_angles: 関節角度データ
            gait_cycles: 歩行周期データ
            
        Returns:
            List[CompensationAlert]: 検出された代償動作アラート
        """
        logger.info("Starting compensation movement detection", 
                   frames=len(landmarks_data))
        
        alerts = []
        
        # 1. アウト/イントゥーイング検出
        foot_rotation_alerts = self._detect_foot_rotation_compensation(landmarks_data)
        alerts.extend(foot_rotation_alerts)
        
        # 2. 膝外反/内反検出
        knee_alignment_alerts = self._detect_knee_alignment_compensation(landmarks_data)
        alerts.extend(knee_alignment_alerts)
        
        # 3. トレンデレンブルグ兆候検出
        trendelenburg_alerts = self._detect_trendelenburg_sign(
            landmarks_data, joint_angles
        )
        alerts.extend(trendelenburg_alerts)
        
        # 4. ペルビックドロップ検出
        pelvic_drop_alerts = self._detect_pelvic_drop(joint_angles)
        alerts.extend(pelvic_drop_alerts)
        
        # 5. ラテラルスウェイ検出
        lateral_sway_alerts = self._detect_lateral_sway(landmarks_data)
        alerts.extend(lateral_sway_alerts)
        
        # 6. 体幹代償動作検出
        trunk_compensation_alerts = self._detect_trunk_compensation(
            landmarks_data, joint_angles
        )
        alerts.extend(trunk_compensation_alerts)
        
        logger.info("Compensation detection completed", 
                   total_alerts=len(alerts))
        
        return alerts
    
    def _detect_foot_rotation_compensation(
        self, 
        landmarks_data: List[Dict]
    ) -> List[CompensationAlert]:
        """アウト/イントゥーイング検出"""
        alerts = []
        foot_angles = []
        
        for frame_idx, frame_data in enumerate(landmarks_data):
            if not frame_data or not frame_data['landmarks']:
                continue
                
            landmarks = frame_data['landmarks']
            
            # 左右の足部角度計算
            for side in ['left', 'right']:
                ankle_idx = self.landmark_indices[f'{side}_ankle']
                foot_idx = self.landmark_indices[f'{side}_foot_index']
                heel_idx = self.landmark_indices[f'{side}_heel']
                
                ankle = landmarks[ankle_idx]
                foot = landmarks[foot_idx]
                heel = landmarks[heel_idx]
                
                if all(lm['visibility'] > 0.5 for lm in [ankle, foot, heel]):
                    # 足部の向きを計算（ヒール-足指ベクトル）
                    foot_vector_x = foot['x'] - heel['x']
                    foot_vector_y = foot['y'] - heel['y']
                    
                    # 前方向（Y軸負方向）に対する角度
                    foot_angle = math.degrees(math.atan2(foot_vector_x, -foot_vector_y))
                    foot_angles.append((frame_idx, side, foot_angle))
                    
                    # しきい値チェック
                    if foot_angle > self.thresholds['out_toeing_deg']:
                        alert = CompensationAlert(
                            alert_type="out_toeing",
                            severity="medium",
                            message=f"{side.title()}足のアウトトゥーイング検出: {foot_angle:.1f}°",
                            frame_range=(frame_idx, frame_idx),
                            threshold_value=self.thresholds['out_toeing_deg'],
                            measured_value=foot_angle
                        )
                        alerts.append(alert)
                    
                    elif foot_angle < self.thresholds['in_toeing_deg']:
                        alert = CompensationAlert(
                            alert_type="in_toeing",
                            severity="medium",
                            message=f"{side.title()}足のイントゥーイング検出: {foot_angle:.1f}°",
                            frame_range=(frame_idx, frame_idx),
                            threshold_value=self.thresholds['in_toeing_deg'],
                            measured_value=foot_angle
                        )
                        alerts.append(alert)
        
        return alerts
    
    def _detect_knee_alignment_compensation(
        self, 
        landmarks_data: List[Dict]
    ) -> List[CompensationAlert]:
        """膝外反/内反検出"""
        alerts = []
        
        for frame_idx, frame_data in enumerate(landmarks_data):
            if not frame_data or not frame_data['landmarks']:
                continue
                
            landmarks = frame_data['landmarks']
            
            # 左右の膝アライメント計算
            for side in ['left', 'right']:
                hip_idx = self.landmark_indices[f'{side}_hip']
                knee_idx = self.landmark_indices[f'{side}_knee']
                ankle_idx = self.landmark_indices[f'{side}_ankle']
                
                hip = landmarks[hip_idx]
                knee = landmarks[knee_idx]
                ankle = landmarks[ankle_idx]
                
                if all(lm['visibility'] > 0.5 for lm in [hip, knee, ankle]):
                    # 膝の内外反角度計算
                    knee_angle = self._calculate_knee_valgus_angle(hip, knee, ankle)
                    
                    # しきい値チェック
                    if knee_angle > self.thresholds['knee_valgus_deg']:
                        alert = CompensationAlert(
                            alert_type="knee_valgus",
                            severity="high",
                            message=f"{side.title()}膝外反検出: {knee_angle:.1f}°",
                            frame_range=(frame_idx, frame_idx),
                            threshold_value=self.thresholds['knee_valgus_deg'],
                            measured_value=knee_angle
                        )
                        alerts.append(alert)
                    
                    elif knee_angle < self.thresholds['knee_varus_deg']:
                        alert = CompensationAlert(
                            alert_type="knee_varus",
                            severity="medium",
                            message=f"{side.title()}膝内反検出: {knee_angle:.1f}°",
                            frame_range=(frame_idx, frame_idx),
                            threshold_value=self.thresholds['knee_varus_deg'],
                            measured_value=knee_angle
                        )
                        alerts.append(alert)
        
        return alerts
    
    def _detect_trendelenburg_sign(
        self, 
        landmarks_data: List[Dict], 
        joint_angles: JointAngles
    ) -> List[CompensationAlert]:
        """トレンデレンブルグ兆候検出（中殿筋機能低下）"""
        alerts = []
        
        if not joint_angles.pelvic_drop_deg:
            return alerts
        
        for i, pelvic_angle in enumerate(joint_angles.pelvic_drop_deg):
            if abs(pelvic_angle) > self.thresholds['trendelenburg_deg']:
                alert = CompensationAlert(
                    alert_type="trendelenburg_sign",
                    severity="high",
                    message=f"トレンデレンブルグ兆候検出: 骨盤傾斜 {pelvic_angle:.1f}°",
                    frame_range=(i, i),
                    threshold_value=self.thresholds['trendelenburg_deg'],
                    measured_value=abs(pelvic_angle)
                )
                alerts.append(alert)
        
        return alerts
    
    def _detect_pelvic_drop(self, joint_angles: JointAngles) -> List[CompensationAlert]:
        """ペルビックドロップ検出"""
        alerts = []
        
        if not joint_angles.pelvic_list_deg:
            return alerts
        
        for i, pelvic_list in enumerate(joint_angles.pelvic_list_deg):
            if abs(pelvic_list) > self.thresholds['pelvic_drop_deg']:
                alert = CompensationAlert(
                    alert_type="pelvic_drop",
                    severity="medium",
                    message=f"ペルビックドロップ検出: {pelvic_list:.1f}°",
                    frame_range=(i, i),
                    threshold_value=self.thresholds['pelvic_drop_deg'],
                    measured_value=abs(pelvic_list)
                )
                alerts.append(alert)
        
        return alerts
    
    def _detect_lateral_sway(self, landmarks_data: List[Dict]) -> List[CompensationAlert]:
        """ラテラルスウェイ検出"""
        alerts = []
        
        # 肩の左右動揺を分析
        shoulder_positions = []
        
        for frame_data in landmarks_data:
            if not frame_data or not frame_data['landmarks']:
                continue
                
            landmarks = frame_data['landmarks']
            left_shoulder = landmarks[self.landmark_indices['left_shoulder']]
            right_shoulder = landmarks[self.landmark_indices['right_shoulder']]
            
            if left_shoulder['visibility'] > 0.5 and right_shoulder['visibility'] > 0.5:
                shoulder_center_x = (left_shoulder['x'] + right_shoulder['x']) / 2
                shoulder_positions.append(shoulder_center_x)
        
        if len(shoulder_positions) < 10:
            return alerts
        
        # 左右動揺の変動を計算
        mean_position = np.mean(shoulder_positions)
        max_sway = max([abs(pos - mean_position) for pos in shoulder_positions])
        max_sway_cm = max_sway * 100  # cm変換（概算）
        
        if max_sway_cm > self.thresholds['lateral_sway_cm']:
            alert = CompensationAlert(
                alert_type="lateral_sway",
                severity="medium",
                message=f"過度な左右動揺検出: {max_sway_cm:.1f}cm",
                frame_range=(0, len(landmarks_data)-1),
                threshold_value=self.thresholds['lateral_sway_cm'],
                measured_value=max_sway_cm
            )
            alerts.append(alert)
        
        return alerts
    
    def _detect_trunk_compensation(
        self, 
        landmarks_data: List[Dict], 
        joint_angles: JointAngles
    ) -> List[CompensationAlert]:
        """体幹代償動作検出"""
        alerts = []
        
        # 体幹回旋の過度な動きを検出
        if joint_angles.trunk_rotation_deg:
            for i, rotation in enumerate(joint_angles.trunk_rotation_deg):
                if abs(rotation) > self.thresholds['trunk_rotation_deg']:
                    alert = CompensationAlert(
                        alert_type="excessive_trunk_rotation",
                        severity="medium",
                        message=f"過度な体幹回旋検出: {rotation:.1f}°",
                        frame_range=(i, i),
                        threshold_value=self.thresholds['trunk_rotation_deg'],
                        measured_value=abs(rotation)
                    )
                    alerts.append(alert)
        
        # 体幹側屈の検出
        trunk_lean_angles = self._calculate_trunk_lean(landmarks_data)
        for i, lean_angle in enumerate(trunk_lean_angles):
            if abs(lean_angle) > self.thresholds['trunk_lean_deg']:
                alert = CompensationAlert(
                    alert_type="trunk_lean",
                    severity="medium",
                    message=f"体幹側屈検出: {lean_angle:.1f}°",
                    frame_range=(i, i),
                    threshold_value=self.thresholds['trunk_lean_deg'],
                    measured_value=abs(lean_angle)
                )
                alerts.append(alert)
        
        return alerts
    
    def _calculate_knee_valgus_angle(
        self, 
        hip: Dict, 
        knee: Dict, 
        ankle: Dict
    ) -> float:
        """膝外反角度計算"""
        # 股関節-膝関節ベクトル
        thigh_vector_x = knee['x'] - hip['x']
        thigh_vector_y = knee['y'] - hip['y']
        
        # 膝関節-足関節ベクトル
        shank_vector_x = ankle['x'] - knee['x']
        shank_vector_y = ankle['y'] - knee['y']
        
        # 大腿と下腿の角度差から膝の内外反を計算
        thigh_angle = math.degrees(math.atan2(thigh_vector_x, -thigh_vector_y))
        shank_angle = math.degrees(math.atan2(shank_vector_x, -shank_vector_y))
        
        # 外反角度（正の値が外反、負の値が内反）
        valgus_angle = shank_angle - thigh_angle
        
        # -180°〜180°の範囲に正規化
        while valgus_angle > 180:
            valgus_angle -= 360
        while valgus_angle < -180:
            valgus_angle += 360
        
        return valgus_angle
    
    def _calculate_trunk_lean(self, landmarks_data: List[Dict]) -> List[float]:
        """体幹側屈角度計算"""
        trunk_lean_angles = []
        
        for frame_data in landmarks_data:
            if not frame_data or not frame_data['landmarks']:
                trunk_lean_angles.append(0.0)
                continue
                
            landmarks = frame_data['landmarks']
            left_shoulder = landmarks[self.landmark_indices['left_shoulder']]
            right_shoulder = landmarks[self.landmark_indices['right_shoulder']]
            left_hip = landmarks[self.landmark_indices['left_hip']]
            right_hip = landmarks[self.landmark_indices['right_hip']]
            
            if all(lm['visibility'] > 0.5 for lm in [left_shoulder, right_shoulder, left_hip, right_hip]):
                # 肩の中点と腰の中点
                shoulder_mid_x = (left_shoulder['x'] + right_shoulder['x']) / 2
                shoulder_mid_y = (left_shoulder['y'] + right_shoulder['y']) / 2
                hip_mid_x = (left_hip['x'] + right_hip['x']) / 2
                hip_mid_y = (left_hip['y'] + right_hip['y']) / 2
                
                # 体幹の垂直からの傾きを計算
                trunk_vector_x = shoulder_mid_x - hip_mid_x
                trunk_vector_y = shoulder_mid_y - hip_mid_y
                
                # 垂直線（Y軸）からの角度
                lean_angle = math.degrees(math.atan2(trunk_vector_x, -trunk_vector_y))
                trunk_lean_angles.append(lean_angle)
            else:
                trunk_lean_angles.append(0.0)
        
        return trunk_lean_angles