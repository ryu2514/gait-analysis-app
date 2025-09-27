"""
拡張関節角度計算器
Enhanced Joint Angle Calculator with detailed kinematic analysis
"""

import numpy as np
import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from scipy import signal

from app.models.gait_models import JointAngles
from app.core.advanced_logger import get_logger

logger = get_logger(__name__)


@dataclass
class Point3D:
    """3D座標点"""
    x: float
    y: float
    z: float
    
    def to_array(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])


@dataclass
class EnhancedJointAngleFrame:
    """拡張単一フレーム関節角度"""
    # 股関節（左右別）
    hip_flexion_l: float
    hip_flexion_r: float
    hip_extension_l: float
    hip_extension_r: float
    hip_abduction_l: float
    hip_abduction_r: float
    
    # 膝関節（左右別）
    knee_flexion_l: float
    knee_flexion_r: float
    knee_heel_contact_l: float
    knee_heel_contact_r: float
    
    # 足関節（左右別）
    ankle_dorsiflexion_l: float
    ankle_dorsiflexion_r: float
    ankle_plantarflexion_l: float
    ankle_plantarflexion_r: float
    
    # 骨盤・体幹
    pelvic_drop: float
    pelvic_list: float
    trunk_rotation: float


class EnhancedJointAngleCalculator:
    """拡張関節角度計算器"""
    
    def __init__(self):
        # MediaPipe Poseランドマークインデックス
        self.LANDMARKS = {
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
        
        # 正常関節可動域範囲（度）
        self.NORMAL_ROM_RANGES = {
            'hip_flexion': (20, 40),        # 歩行時股関節屈曲
            'hip_extension': (0, 15),       # 歩行時股関節伸展
            'hip_abduction': (5, 15),       # 歩行時股関節外転
            'knee_flexion': (0, 70),        # 歩行時膝関節屈曲
            'ankle_dorsiflexion': (0, 20),  # 歩行時足関節背屈
            'ankle_plantarflexion': (0, 30), # 歩行時足関節底屈
            'pelvic_drop': (-3, 3),         # 骨盤傾斜
            'trunk_rotation': (-10, 10),    # 体幹回旋
        }
    
    def calculate_enhanced_joint_angles(
        self, 
        landmarks_data: List[Dict],
        gait_cycles: List[Dict],
        fps: float = 30.0
    ) -> JointAngles:
        """
        拡張関節角度計算メイン処理
        
        Args:
            landmarks_data: MediaPipeランドマークデータ
            gait_cycles: 歩行周期データ
            fps: フレームレート
            
        Returns:
            JointAngles: 拡張関節角度データ
        """
        logger.info("Starting enhanced joint angle calculation", 
                   frames=len(landmarks_data), fps=fps)
        
        enhanced_frames = []
        timestamps = []
        
        for frame_data in landmarks_data:
            if frame_data and frame_data['landmarks']:
                # 3D座標を抽出
                landmarks_3d = self._extract_3d_landmarks(frame_data['landmarks'])
                
                # 拡張関節角度計算
                angles = self._calculate_enhanced_frame_angles(landmarks_3d)
                enhanced_frames.append(angles)
                timestamps.append(frame_data['timestamp'])
            else:
                # 欠損フレーム
                angles = self._create_nan_frame()
                enhanced_frames.append(angles)
                timestamps.append(0.0)
        
        # 欠損値補間とスムージング
        enhanced_frames = self._interpolate_and_smooth(enhanced_frames)
        
        # 歩行周期イベント検出
        gait_events = self._detect_gait_events(enhanced_frames, gait_cycles)
        
        # 詳細指標計算
        detailed_metrics = self._calculate_detailed_metrics(enhanced_frames, gait_events)
        
        # JointAnglesモデルに変換
        result = self._convert_to_enhanced_joint_angles(
            enhanced_frames, timestamps, detailed_metrics
        )
        
        logger.info("Enhanced joint angle calculation completed",
                   hip_rom=result.hip_rom_deg,
                   knee_max_flexion=result.knee_max_flexion_deg)
        
        return result
    
    def _extract_3d_landmarks(self, landmarks: List[Dict]) -> Dict[str, Point3D]:
        """3Dランドマーク座標の抽出"""
        landmarks_3d = {}
        
        for name, idx in self.LANDMARKS.items():
            if idx < len(landmarks) and landmarks[idx]['visibility'] > 0.5:
                landmark = landmarks[idx]
                landmarks_3d[name] = Point3D(
                    x=landmark['x'],
                    y=landmark['y'],
                    z=landmark['z']
                )
        
        return landmarks_3d
    
    def _calculate_enhanced_frame_angles(
        self, 
        landmarks: Dict[str, Point3D]
    ) -> EnhancedJointAngleFrame:
        """拡張単一フレーム関節角度計算"""
        try:
            # 股関節屈曲・伸展（左右別）
            hip_flex_l, hip_ext_l = self._calculate_hip_flexion_extension(landmarks, 'left')
            hip_flex_r, hip_ext_r = self._calculate_hip_flexion_extension(landmarks, 'right')
            
            # 股関節外転（左右別）
            hip_abd_l = self._calculate_hip_abduction(landmarks, 'left')
            hip_abd_r = self._calculate_hip_abduction(landmarks, 'right')
            
            # 膝関節屈曲（左右別）
            knee_flex_l = self._calculate_knee_flexion(landmarks, 'left')
            knee_flex_r = self._calculate_knee_flexion(landmarks, 'right')
            
            # ヒールコンタクト時膝関節角度（静的評価）
            knee_hc_l = self._calculate_heel_contact_knee_angle(landmarks, 'left')
            knee_hc_r = self._calculate_heel_contact_knee_angle(landmarks, 'right')
            
            # 足関節背屈・底屈（左右別）
            ankle_df_l, ankle_pf_l = self._calculate_ankle_dorsi_plantarflexion(landmarks, 'left')
            ankle_df_r, ankle_pf_r = self._calculate_ankle_dorsi_plantarflexion(landmarks, 'right')
            
            # 骨盤・体幹
            pelvic_drop = self._calculate_pelvic_drop(landmarks)
            pelvic_list = self._calculate_pelvic_list(landmarks)
            trunk_rotation = self._calculate_trunk_rotation(landmarks)
            
            return EnhancedJointAngleFrame(
                hip_flexion_l=hip_flex_l, hip_flexion_r=hip_flex_r,
                hip_extension_l=hip_ext_l, hip_extension_r=hip_ext_r,
                hip_abduction_l=hip_abd_l, hip_abduction_r=hip_abd_r,
                knee_flexion_l=knee_flex_l, knee_flexion_r=knee_flex_r,
                knee_heel_contact_l=knee_hc_l, knee_heel_contact_r=knee_hc_r,
                ankle_dorsiflexion_l=ankle_df_l, ankle_dorsiflexion_r=ankle_df_r,
                ankle_plantarflexion_l=ankle_pf_l, ankle_plantarflexion_r=ankle_pf_r,
                pelvic_drop=pelvic_drop, pelvic_list=pelvic_list,
                trunk_rotation=trunk_rotation
            )
            
        except Exception as e:
            logger.warning("Failed to calculate enhanced angles", error=str(e))
            return self._create_nan_frame()
    
    def _calculate_hip_flexion_extension(
        self, 
        landmarks: Dict[str, Point3D], 
        side: str
    ) -> Tuple[float, float]:
        """股関節屈曲・伸展角度計算"""
        try:
            shoulder = landmarks[f'{side}_shoulder'].to_array()
            hip = landmarks[f'{side}_hip'].to_array()
            knee = landmarks[f'{side}_knee'].to_array()
            
            # 体幹ベクトル（垂直基準）
            vertical_vector = np.array([0, -1, 0])  # 下向きベクトル
            
            # 大腿ベクトル
            thigh_vector = knee - hip
            
            # 矢状面投影での角度計算
            thigh_sagittal = thigh_vector[[0, 1]]
            vertical_sagittal = vertical_vector[[0, 1]]
            
            angle_rad = self._angle_between_vectors(thigh_sagittal, vertical_sagittal)
            angle_deg = math.degrees(angle_rad)
            
            # 屈曲・伸展の判定
            if thigh_vector[0] > 0:  # 前方成分が正の場合
                hip_flexion = angle_deg
                hip_extension = 0.0
            else:  # 後方成分が正の場合
                hip_flexion = 0.0
                hip_extension = angle_deg
            
            return hip_flexion, hip_extension
            
        except Exception:
            return np.nan, np.nan
    
    def _calculate_hip_abduction(
        self, 
        landmarks: Dict[str, Point3D], 
        side: str
    ) -> float:
        """股関節外転角度計算"""
        try:
            left_hip = landmarks['left_hip'].to_array()
            right_hip = landmarks['right_hip'].to_array()
            knee = landmarks[f'{side}_knee'].to_array()
            hip = landmarks[f'{side}_hip'].to_array()
            
            # 骨盤ベクトル
            pelvis_vector = right_hip - left_hip
            pelvis_normal = pelvis_vector / np.linalg.norm(pelvis_vector)
            
            # 大腿ベクトル
            thigh_vector = knee - hip
            
            # 前額面での外転角度計算
            # 骨盤に垂直な面での大腿ベクトルの成分
            abduction_component = np.dot(thigh_vector, pelvis_normal)
            thigh_length = np.linalg.norm(thigh_vector)
            
            if thigh_length > 0:
                abduction_angle = math.degrees(math.asin(
                    np.clip(abs(abduction_component) / thigh_length, 0, 1)
                ))
            else:
                abduction_angle = 0.0
            
            return abduction_angle
            
        except Exception:
            return np.nan
    
    def _calculate_knee_flexion(
        self, 
        landmarks: Dict[str, Point3D], 
        side: str
    ) -> float:
        """膝関節屈曲角度計算"""
        try:
            hip = landmarks[f'{side}_hip'].to_array()
            knee = landmarks[f'{side}_knee'].to_array()
            ankle = landmarks[f'{side}_ankle'].to_array()
            
            # 大腿ベクトル
            thigh_vector = knee - hip
            # 下腿ベクトル
            shank_vector = ankle - knee
            
            angle_rad = self._angle_between_vectors(thigh_vector, shank_vector)
            knee_flexion = 180 - math.degrees(angle_rad)
            
            return max(0, knee_flexion)
            
        except Exception:
            return np.nan
    
    def _calculate_heel_contact_knee_angle(
        self, 
        landmarks: Dict[str, Point3D], 
        side: str
    ) -> float:
        """ヒールコンタクト時膝関節角度推定"""
        try:
            # 現在のフレームでの膝関節角度（ヒールコンタクト検出は別途実装）
            return self._calculate_knee_flexion(landmarks, side)
            
        except Exception:
            return np.nan
    
    def _calculate_ankle_dorsi_plantarflexion(
        self, 
        landmarks: Dict[str, Point3D], 
        side: str
    ) -> Tuple[float, float]:
        """足関節背屈・底屈角度計算"""
        try:
            knee = landmarks[f'{side}_knee'].to_array()
            ankle = landmarks[f'{side}_ankle'].to_array()
            heel = landmarks[f'{side}_heel'].to_array()
            foot_tip = landmarks[f'{side}_foot_index'].to_array()
            
            # 下腿ベクトル
            shank_vector = ankle - knee
            
            # 足部ベクトル（踵からつま先）
            foot_vector = foot_tip - heel
            
            # 下腿軸と足部軸の角度
            angle_rad = self._angle_between_vectors(shank_vector, foot_vector)
            angle_deg = math.degrees(angle_rad)
            
            # 中性位（90度）からの偏差
            neutral_angle = 90.0
            deviation = angle_deg - neutral_angle
            
            if deviation > 0:  # 背屈
                dorsiflexion = deviation
                plantarflexion = 0.0
            else:  # 底屈
                dorsiflexion = 0.0
                plantarflexion = abs(deviation)
            
            return dorsiflexion, plantarflexion
            
        except Exception:
            return np.nan, np.nan
    
    def _calculate_pelvic_drop(self, landmarks: Dict[str, Point3D]) -> float:
        """骨盤下降（Trendelenburg sign）計算"""
        try:
            left_hip = landmarks['left_hip'].to_array()
            right_hip = landmarks['right_hip'].to_array()
            
            # 骨盤の水平からの傾斜
            pelvis_vector = right_hip - left_hip
            drop_angle = math.degrees(math.atan2(pelvis_vector[1], pelvis_vector[0]))
            
            return drop_angle
            
        except Exception:
            return np.nan
    
    def _calculate_pelvic_list(self, landmarks: Dict[str, Point3D]) -> float:
        """骨盤リスト（左右傾き）計算"""
        try:
            left_hip = landmarks['left_hip'].to_array()
            right_hip = landmarks['right_hip'].to_array()
            
            # 前額面での骨盤傾斜
            height_diff = left_hip[1] - right_hip[1]
            width = abs(left_hip[0] - right_hip[0])
            
            if width > 0:
                list_angle = math.degrees(math.atan(height_diff / width))
            else:
                list_angle = 0.0
            
            return list_angle
            
        except Exception:
            return np.nan
    
    def _calculate_trunk_rotation(self, landmarks: Dict[str, Point3D]) -> float:
        """体幹回旋角度計算"""
        try:
            left_shoulder = landmarks['left_shoulder'].to_array()
            right_shoulder = landmarks['right_shoulder'].to_array()
            left_hip = landmarks['left_hip'].to_array()
            right_hip = landmarks['right_hip'].to_array()
            
            # 肩ラインベクトル
            shoulder_vector = right_shoulder - left_shoulder
            # 骨盤ラインベクトル
            pelvis_vector = right_hip - left_hip
            
            # 水平面での肩と骨盤の角度差（回旋）
            shoulder_angle = math.atan2(shoulder_vector[1], shoulder_vector[0])
            pelvis_angle = math.atan2(pelvis_vector[1], pelvis_vector[0])
            
            rotation_rad = shoulder_angle - pelvis_angle
            rotation_deg = math.degrees(rotation_rad)
            
            # -180°〜180°の範囲に正規化
            while rotation_deg > 180:
                rotation_deg -= 360
            while rotation_deg < -180:
                rotation_deg += 360
            
            return rotation_deg
            
        except Exception:
            return np.nan
    
    def _create_nan_frame(self) -> EnhancedJointAngleFrame:
        """NaN値で埋められたフレーム作成"""
        return EnhancedJointAngleFrame(
            hip_flexion_l=np.nan, hip_flexion_r=np.nan,
            hip_extension_l=np.nan, hip_extension_r=np.nan,
            hip_abduction_l=np.nan, hip_abduction_r=np.nan,
            knee_flexion_l=np.nan, knee_flexion_r=np.nan,
            knee_heel_contact_l=np.nan, knee_heel_contact_r=np.nan,
            ankle_dorsiflexion_l=np.nan, ankle_dorsiflexion_r=np.nan,
            ankle_plantarflexion_l=np.nan, ankle_plantarflexion_r=np.nan,
            pelvic_drop=np.nan, pelvic_list=np.nan, trunk_rotation=np.nan
        )
    
    def _interpolate_and_smooth(
        self, 
        frames: List[EnhancedJointAngleFrame]
    ) -> List[EnhancedJointAngleFrame]:
        """欠損値補間とスムージング"""
        if len(frames) < 3:
            return frames
        
        # 各角度データについて補間とスムージング
        angle_attributes = [
            'hip_flexion_l', 'hip_flexion_r', 'hip_extension_l', 'hip_extension_r',
            'hip_abduction_l', 'hip_abduction_r', 'knee_flexion_l', 'knee_flexion_r',
            'knee_heel_contact_l', 'knee_heel_contact_r', 
            'ankle_dorsiflexion_l', 'ankle_dorsiflexion_r',
            'ankle_plantarflexion_l', 'ankle_plantarflexion_r',
            'pelvic_drop', 'pelvic_list', 'trunk_rotation'
        ]
        
        for attr in angle_attributes:
            values = [getattr(frame, attr) for frame in frames]
            
            # 補間
            interpolated = self._interpolate_1d_array(values)
            
            # スムージング（Butterworth低域通過フィルタ）
            smoothed = self._smooth_signal(interpolated)
            
            for i, frame in enumerate(frames):
                setattr(frame, attr, smoothed[i])
        
        return frames
    
    def _interpolate_1d_array(self, values: List[float]) -> List[float]:
        """1次元配列の線形補間"""
        values_array = np.array(values, dtype=float)
        valid_mask = ~np.isnan(values_array)
        
        if not np.any(valid_mask):
            return [0.0] * len(values)
        
        valid_indices = np.where(valid_mask)[0]
        
        if len(valid_indices) < 2:
            fill_value = values_array[valid_indices[0]] if len(valid_indices) == 1 else 0.0
            return [fill_value] * len(values)
        
        interpolated = np.interp(
            np.arange(len(values)),
            valid_indices,
            values_array[valid_indices]
        )
        
        return interpolated.tolist()
    
    def _smooth_signal(self, values: List[float], cutoff_freq: float = 5.0) -> List[float]:
        """信号のスムージング"""
        if len(values) < 10:
            return values
        
        try:
            # Butterworth低域通過フィルタ
            nyquist = 30.0 / 2  # 30fps の場合
            normal_cutoff = cutoff_freq / nyquist
            b, a = signal.butter(2, normal_cutoff, btype='low', analog=False)
            
            smoothed = signal.filtfilt(b, a, values)
            return smoothed.tolist()
        
        except Exception:
            return values
    
    def _detect_gait_events(
        self, 
        frames: List[EnhancedJointAngleFrame], 
        gait_cycles: List[Dict]
    ) -> Dict[str, List[int]]:
        """歩行イベント検出（ヒールストライク、トーオフ）"""
        # 簡易実装：既存の歩行周期データを使用
        gait_events = {
            'heel_strikes': [],
            'toe_offs': []
        }
        
        for cycle in gait_cycles:
            gait_events['heel_strikes'].append(cycle.get('start_frame', 0))
            gait_events['toe_offs'].append(cycle.get('end_frame', 0))
        
        return gait_events
    
    def _calculate_detailed_metrics(
        self, 
        frames: List[EnhancedJointAngleFrame], 
        gait_events: Dict[str, List[int]]
    ) -> Dict[str, float]:
        """詳細指標計算"""
        # 股関節可動域
        hip_flexion_values = [f.hip_flexion_l + f.hip_flexion_r for f in frames if not np.isnan(f.hip_flexion_l + f.hip_flexion_r)]
        hip_rom = max(hip_flexion_values) - min(hip_flexion_values) if hip_flexion_values else 0.0
        
        # 膝関節最大屈曲角度
        knee_flexion_values = [f.knee_flexion_l + f.knee_flexion_r for f in frames if not np.isnan(f.knee_flexion_l + f.knee_flexion_r)]
        knee_max_flexion = max(knee_flexion_values) if knee_flexion_values else 0.0
        
        # ヒールコンタクト時膝関節角度（平均）
        knee_hc_values = [f.knee_heel_contact_l + f.knee_heel_contact_r for f in frames if not np.isnan(f.knee_heel_contact_l + f.knee_heel_contact_r)]
        knee_heel_contact_avg = np.mean(knee_hc_values) if knee_hc_values else 0.0
        
        # トーオフ時足関節角度（平均）
        ankle_values = [f.ankle_plantarflexion_l + f.ankle_plantarflexion_r for f in frames if not np.isnan(f.ankle_plantarflexion_l + f.ankle_plantarflexion_r)]
        ankle_toe_off_avg = np.mean(ankle_values) if ankle_values else 0.0
        
        return {
            'hip_rom': hip_rom,
            'knee_max_flexion': knee_max_flexion,
            'knee_heel_contact_avg': knee_heel_contact_avg,
            'ankle_toe_off_avg': ankle_toe_off_avg
        }
    
    def _convert_to_enhanced_joint_angles(
        self, 
        frames: List[EnhancedJointAngleFrame], 
        timestamps: List[float],
        metrics: Dict[str, float]
    ) -> JointAngles:
        """拡張JointAnglesモデルに変換"""
        
        # 左右統合された時系列データ生成
        hip_flexion = [(f.hip_flexion_l + f.hip_flexion_r) / 2 for f in frames]
        hip_extension = [(f.hip_extension_l + f.hip_extension_r) / 2 for f in frames]
        hip_abduction = [(f.hip_abduction_l + f.hip_abduction_r) / 2 for f in frames]
        
        knee_flexion = [(f.knee_flexion_l + f.knee_flexion_r) / 2 for f in frames]
        
        ankle_dorsiflexion = [(f.ankle_dorsiflexion_l + f.ankle_dorsiflexion_r) / 2 for f in frames]
        ankle_plantarflexion = [(f.ankle_plantarflexion_l + f.ankle_plantarflexion_r) / 2 for f in frames]
        
        pelvic_drop = [f.pelvic_drop for f in frames]
        pelvic_list = [f.pelvic_list for f in frames]
        trunk_rotation = [f.trunk_rotation for f in frames]
        
        return JointAngles(
            hip_flexion_deg=hip_flexion,
            hip_extension_deg=hip_extension,
            hip_abduction_deg=hip_abduction,
            hip_rom_deg=metrics['hip_rom'],
            knee_flexion_deg=knee_flexion,
            knee_heel_contact_deg=metrics['knee_heel_contact_avg'],
            knee_max_flexion_deg=metrics['knee_max_flexion'],
            ankle_dorsiflexion_deg=ankle_dorsiflexion,
            ankle_plantarflexion_deg=ankle_plantarflexion,
            ankle_toe_off_deg=metrics['ankle_toe_off_avg'],
            pelvic_drop_deg=pelvic_drop,
            pelvic_list_deg=pelvic_list,
            trunk_rotation_deg=trunk_rotation,
            frame_timestamps=timestamps
        )
    
    def _angle_between_vectors(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """2つのベクトル間の角度計算"""
        v1_norm = v1 / (np.linalg.norm(v1) + 1e-8)
        v2_norm = v2 / (np.linalg.norm(v2) + 1e-8)
        
        dot_product = np.clip(np.dot(v1_norm, v2_norm), -1.0, 1.0)
        angle_rad = math.acos(abs(dot_product))
        
        return angle_rad