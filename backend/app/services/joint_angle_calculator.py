"""
関節角度計算サービス
MediaPipeの3Dランドマークから関節角度を計算
"""

import numpy as np
import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from app.models.gait_models import JointAngles
from app.core.logging import StructuredLogger

logger = StructuredLogger(__name__)


@dataclass
class Point3D:
    """3D座標点"""
    x: float
    y: float
    z: float
    
    def to_array(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])


@dataclass
class JointAngleFrame:
    """単一フレームの関節角度"""
    hip_flexion_l: float
    hip_flexion_r: float
    hip_abduction_l: float
    hip_abduction_r: float
    knee_flexion_l: float
    knee_flexion_r: float
    ankle_dorsiflexion_l: float
    ankle_dorsiflexion_r: float
    pelvic_tilt: float
    pelvic_drop: float


class JointAngleCalculator:
    """関節角度計算器"""
    
    def __init__(self):
        # MediaPipe Poseランドマークインデックス
        self.LANDMARKS = {
            # 体幹
            'nose': 0,
            'left_shoulder': 11,
            'right_shoulder': 12,
            
            # 骨盤・股関節
            'left_hip': 23,
            'right_hip': 24,
            
            # 膝関節
            'left_knee': 25,
            'right_knee': 26,
            
            # 足関節
            'left_ankle': 27,
            'right_ankle': 28,
            
            # 足部
            'left_heel': 29,
            'right_heel': 30,
            'left_foot_index': 31,
            'right_foot_index': 32,
        }
        
        # 正常角度範囲（度）
        self.NORMAL_RANGES = {
            'hip_flexion': (20, 40),        # 歩行時の最大屈曲
            'hip_abduction': (-5, 5),       # 内転・外転
            'knee_flexion': (0, 70),        # 歩行時の最大屈曲
            'ankle_dorsiflexion': (-20, 20), # 底屈・背屈
            'pelvic_tilt': (-5, 5),         # 前後傾
            'pelvic_drop': (-3, 3),         # 左右傾斜
        }
    
    def calculate_joint_angles(self, landmarks_data: List[Dict]) -> JointAngles:
        """
        全フレームの関節角度計算
        
        Args:
            landmarks_data: MediaPipeランドマークデータ
            
        Returns:
            JointAngles: 関節角度時系列データ
        """
        logger.info("Starting joint angle calculation", frames=len(landmarks_data))
        
        joint_angles_frames = []
        timestamps = []
        
        for frame_data in landmarks_data:
            if frame_data and frame_data['landmarks']:
                # 3D座標を抽出
                landmarks_3d = self._extract_3d_landmarks(frame_data['landmarks'])
                
                # 関節角度計算
                angles = self._calculate_frame_angles(landmarks_3d)
                joint_angles_frames.append(angles)
                timestamps.append(frame_data['timestamp'])
            else:
                # 欠損フレームはNaN値で埋める
                angles = JointAngleFrame(
                    hip_flexion_l=np.nan, hip_flexion_r=np.nan,
                    hip_abduction_l=np.nan, hip_abduction_r=np.nan,
                    knee_flexion_l=np.nan, knee_flexion_r=np.nan,
                    ankle_dorsiflexion_l=np.nan, ankle_dorsiflexion_r=np.nan,
                    pelvic_tilt=np.nan, pelvic_drop=np.nan
                )
                joint_angles_frames.append(angles)
                timestamps.append(0.0)
        
        # 欠損値補間
        joint_angles_frames = self._interpolate_missing_angles(joint_angles_frames)
        
        # 時系列データに変換
        result = self._convert_to_time_series(joint_angles_frames, timestamps)
        
        logger.info("Joint angle calculation completed", total_frames=len(joint_angles_frames))
        return result
    
    def _extract_3d_landmarks(self, landmarks: List[Dict]) -> Dict[str, Point3D]:
        """3Dランドマーク座標の抽出"""
        landmarks_3d = {}
        
        for name, idx in self.LANDMARKS.items():
            if idx < len(landmarks):
                landmark = landmarks[idx]
                landmarks_3d[name] = Point3D(
                    x=landmark['x'],
                    y=landmark['y'],
                    z=landmark['z']
                )
        
        return landmarks_3d
    
    def _calculate_frame_angles(self, landmarks: Dict[str, Point3D]) -> JointAngleFrame:
        """単一フレームの関節角度計算"""
        try:
            # 股関節屈曲角度
            hip_flex_l = self._calculate_hip_flexion(landmarks, 'left')
            hip_flex_r = self._calculate_hip_flexion(landmarks, 'right')
            
            # 股関節外転角度
            hip_abd_l = self._calculate_hip_abduction(landmarks, 'left')
            hip_abd_r = self._calculate_hip_abduction(landmarks, 'right')
            
            # 膝関節屈曲角度
            knee_flex_l = self._calculate_knee_flexion(landmarks, 'left')
            knee_flex_r = self._calculate_knee_flexion(landmarks, 'right')
            
            # 足関節背屈角度
            ankle_df_l = self._calculate_ankle_dorsiflexion(landmarks, 'left')
            ankle_df_r = self._calculate_ankle_dorsiflexion(landmarks, 'right')
            
            # 骨盤傾斜
            pelvic_tilt = self._calculate_pelvic_tilt(landmarks)
            pelvic_drop = self._calculate_pelvic_drop(landmarks)
            
            return JointAngleFrame(
                hip_flexion_l=hip_flex_l,
                hip_flexion_r=hip_flex_r,
                hip_abduction_l=hip_abd_l,
                hip_abduction_r=hip_abd_r,
                knee_flexion_l=knee_flex_l,
                knee_flexion_r=knee_flex_r,
                ankle_dorsiflexion_l=ankle_df_l,
                ankle_dorsiflexion_r=ankle_df_r,
                pelvic_tilt=pelvic_tilt,
                pelvic_drop=pelvic_drop
            )
            
        except Exception as e:
            logger.warning("Failed to calculate angles for frame", error=str(e))
            return JointAngleFrame(
                hip_flexion_l=np.nan, hip_flexion_r=np.nan,
                hip_abduction_l=np.nan, hip_abduction_r=np.nan,
                knee_flexion_l=np.nan, knee_flexion_r=np.nan,
                ankle_dorsiflexion_l=np.nan, ankle_dorsiflexion_r=np.nan,
                pelvic_tilt=np.nan, pelvic_drop=np.nan
            )
    
    def _calculate_hip_flexion(self, landmarks: Dict[str, Point3D], side: str) -> float:
        """股関節屈曲角度計算"""
        try:
            hip_key = f'{side}_hip'
            knee_key = f'{side}_knee'
            shoulder_key = f'{side}_shoulder'
            
            if not all(key in landmarks for key in [hip_key, knee_key, shoulder_key]):
                return np.nan
            
            hip = landmarks[hip_key].to_array()
            knee = landmarks[knee_key].to_array()
            shoulder = landmarks[shoulder_key].to_array()
            
            # 体幹ベクトル（肩→股関節）
            trunk_vector = hip - shoulder
            # 大腿ベクトル（股関節→膝関節）
            thigh_vector = knee - hip
            
            # 矢状面での角度計算（XY平面投影）
            trunk_2d = trunk_vector[[0, 1]]  # X, Y成分
            thigh_2d = thigh_vector[[0, 1]]
            
            angle_rad = self._angle_between_vectors(trunk_2d, thigh_2d)
            angle_deg = math.degrees(angle_rad)
            
            # 屈曲を正の値とする調整
            if thigh_vector[1] > 0:  # 膝が股関節より下にある場合
                angle_deg = 180 - angle_deg
            
            return max(0, angle_deg)  # 負の値をクリップ
            
        except Exception:
            return np.nan
    
    def _calculate_hip_abduction(self, landmarks: Dict[str, Point3D], side: str) -> float:
        """股関節外転角度計算"""
        try:
            left_hip = landmarks['left_hip'].to_array()
            right_hip = landmarks['right_hip'].to_array()
            target_knee = landmarks[f'{side}_knee'].to_array()
            
            # 骨盤中点
            pelvis_center = (left_hip + right_hip) / 2
            
            # 骨盤ラインベクトル
            pelvis_vector = right_hip - left_hip
            
            # 大腿ベクトル
            thigh_vector = target_knee - landmarks[f'{side}_hip'].to_array()
            
            # 前額面での角度計算（YZ平面投影）
            pelvis_frontal = pelvis_vector[[1, 2]]  # Y, Z成分
            thigh_frontal = thigh_vector[[1, 2]]
            
            angle_rad = self._angle_between_vectors(pelvis_frontal, thigh_frontal)
            angle_deg = math.degrees(angle_rad) - 90  # 垂直を基準とする
            
            # 左右の方向性を考慮
            if side == 'left':
                angle_deg = -angle_deg
            
            return angle_deg
            
        except Exception:
            return np.nan
    
    def _calculate_knee_flexion(self, landmarks: Dict[str, Point3D], side: str) -> float:
        """膝関節屈曲角度計算"""
        try:
            hip = landmarks[f'{side}_hip'].to_array()
            knee = landmarks[f'{side}_knee'].to_array()
            ankle = landmarks[f'{side}_ankle'].to_array()
            
            # 大腿ベクトル（股関節→膝関節）
            thigh_vector = knee - hip
            # 下腿ベクトル（膝関節→足関節）
            shank_vector = ankle - knee
            
            angle_rad = self._angle_between_vectors(thigh_vector, shank_vector)
            angle_deg = 180 - math.degrees(angle_rad)  # 屈曲角度として表現
            
            return max(0, angle_deg)  # 負の値をクリップ
            
        except Exception:
            return np.nan
    
    def _calculate_ankle_dorsiflexion(self, landmarks: Dict[str, Point3D], side: str) -> float:
        """足関節背屈角度計算"""
        try:
            knee = landmarks[f'{side}_knee'].to_array()
            ankle = landmarks[f'{side}_ankle'].to_array()
            foot_tip = landmarks[f'{side}_foot_index'].to_array()
            
            # 下腿ベクトル（膝関節→足関節）
            shank_vector = ankle - knee
            # 足部ベクトル（足関節→つま先）
            foot_vector = foot_tip - ankle
            
            angle_rad = self._angle_between_vectors(shank_vector, foot_vector)
            angle_deg = 90 - math.degrees(angle_rad)  # 直角を基準とした背屈角度
            
            return angle_deg
            
        except Exception:
            return np.nan
    
    def _calculate_pelvic_tilt(self, landmarks: Dict[str, Point3D]) -> float:
        """骨盤前後傾計算"""
        try:
            left_hip = landmarks['left_hip'].to_array()
            right_hip = landmarks['right_hip'].to_array()
            left_shoulder = landmarks['left_shoulder'].to_array()
            right_shoulder = landmarks['right_shoulder'].to_array()
            
            # 骨盤中点と肩中点
            pelvis_center = (left_hip + right_hip) / 2
            shoulder_center = (left_shoulder + right_shoulder) / 2
            
            # 体幹ベクトル
            trunk_vector = pelvis_center - shoulder_center
            
            # 矢状面での傾斜角度
            tilt_angle = math.degrees(math.atan2(trunk_vector[0], trunk_vector[1]))
            
            return tilt_angle
            
        except Exception:
            return np.nan
    
    def _calculate_pelvic_drop(self, landmarks: Dict[str, Point3D]) -> float:
        """骨盤左右傾斜計算（Trendelenburg徴候評価）"""
        try:
            left_hip = landmarks['left_hip'].to_array()
            right_hip = landmarks['right_hip'].to_array()
            
            # 骨盤の左右傾斜角度
            pelvis_vector = right_hip - left_hip
            drop_angle = math.degrees(math.atan2(pelvis_vector[1], pelvis_vector[0]))
            
            return drop_angle
            
        except Exception:
            return np.nan
    
    def _angle_between_vectors(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """2つのベクトル間の角度計算"""
        v1_norm = v1 / np.linalg.norm(v1)
        v2_norm = v2 / np.linalg.norm(v2)
        
        dot_product = np.clip(np.dot(v1_norm, v2_norm), -1.0, 1.0)
        angle_rad = math.acos(dot_product)
        
        return angle_rad
    
    def _interpolate_missing_angles(
        self, 
        angles_frames: List[JointAngleFrame]
    ) -> List[JointAngleFrame]:
        """欠損角度データの補間"""
        if len(angles_frames) < 3:
            return angles_frames
        
        # 各角度について個別に補間
        angle_attributes = [
            'hip_flexion_l', 'hip_flexion_r',
            'hip_abduction_l', 'hip_abduction_r',
            'knee_flexion_l', 'knee_flexion_r',
            'ankle_dorsiflexion_l', 'ankle_dorsiflexion_r',
            'pelvic_tilt', 'pelvic_drop'
        ]
        
        for attr in angle_attributes:
            values = [getattr(frame, attr) for frame in angles_frames]
            interpolated = self._interpolate_1d_array(values)
            
            for i, frame in enumerate(angles_frames):
                setattr(frame, attr, interpolated[i])
        
        return angles_frames
    
    def _interpolate_1d_array(self, values: List[float]) -> List[float]:
        """1次元配列の線形補間"""
        values_array = np.array(values)
        valid_mask = ~np.isnan(values_array)
        
        if not np.any(valid_mask):
            return [0.0] * len(values)
        
        valid_indices = np.where(valid_mask)[0]
        
        if len(valid_indices) < 2:
            # 有効な値が1つ以下の場合は定数埋め
            fill_value = values_array[valid_indices[0]] if len(valid_indices) == 1 else 0.0
            return [fill_value] * len(values)
        
        # 線形補間
        interpolated = np.interp(
            np.arange(len(values)),
            valid_indices,
            values_array[valid_indices]
        )
        
        return interpolated.tolist()
    
    def _convert_to_time_series(
        self, 
        angles_frames: List[JointAngleFrame], 
        timestamps: List[float]
    ) -> JointAngles:
        """フレーム別データを時系列データに変換"""
        
        # 左右の股関節屈曲角度を統合（平均値）
        hip_flexion = [
            (frame.hip_flexion_l + frame.hip_flexion_r) / 2 
            if not (np.isnan(frame.hip_flexion_l) or np.isnan(frame.hip_flexion_r))
            else frame.hip_flexion_l if not np.isnan(frame.hip_flexion_l)
            else frame.hip_flexion_r if not np.isnan(frame.hip_flexion_r)
            else 0.0
            for frame in angles_frames
        ]
        
        # 左右の股関節外転角度を統合
        hip_abduction = [
            (abs(frame.hip_abduction_l) + abs(frame.hip_abduction_r)) / 2
            if not (np.isnan(frame.hip_abduction_l) or np.isnan(frame.hip_abduction_r))
            else 0.0
            for frame in angles_frames
        ]
        
        # 左右の膝関節屈曲角度を統合
        knee_flexion = [
            (frame.knee_flexion_l + frame.knee_flexion_r) / 2
            if not (np.isnan(frame.knee_flexion_l) or np.isnan(frame.knee_flexion_r))
            else 0.0
            for frame in angles_frames
        ]
        
        # 左右の足関節背屈角度を統合
        ankle_dorsiflexion = [
            (frame.ankle_dorsiflexion_l + frame.ankle_dorsiflexion_r) / 2
            if not (np.isnan(frame.ankle_dorsiflexion_l) or np.isnan(frame.ankle_dorsiflexion_r))
            else 0.0
            for frame in angles_frames
        ]
        
        # 骨盤傾斜データ
        pelvic_drop = [
            frame.pelvic_drop if not np.isnan(frame.pelvic_drop) else 0.0
            for frame in angles_frames
        ]
        
        return JointAngles(
            hip_flexion_deg=hip_flexion,
            hip_abduction_deg=hip_abduction,
            knee_flexion_deg=knee_flexion,
            ankle_dorsiflexion_deg=ankle_dorsiflexion,
            pelvic_drop_deg=pelvic_drop,
            frame_timestamps=timestamps
        )
    
    def analyze_joint_ranges(self, joint_angles: JointAngles) -> Dict[str, Dict[str, float]]:
        """関節可動域分析"""
        analysis = {}
        
        joint_data = {
            'hip_flexion': joint_angles.hip_flexion_deg,
            'hip_abduction': joint_angles.hip_abduction_deg,
            'knee_flexion': joint_angles.knee_flexion_deg,
            'ankle_dorsiflexion': joint_angles.ankle_dorsiflexion_deg,
            'pelvic_drop': joint_angles.pelvic_drop_deg
        }
        
        for joint_name, angles in joint_data.items():
            if angles:
                analysis[joint_name] = {
                    'max': max(angles),
                    'min': min(angles),
                    'range': max(angles) - min(angles),
                    'mean': np.mean(angles),
                    'std': np.std(angles)
                }
        
        return analysis