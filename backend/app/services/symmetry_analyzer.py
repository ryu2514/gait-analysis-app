"""
対称性指数分析サービス
歩行の左右対称性を定量評価
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
import statistics

from app.models.gait_models import GaitCycle, SymmetryIndices, JointAngles
from app.core.logging import StructuredLogger

logger = StructuredLogger(__name__)


class SymmetryAnalyzer:
    """歩行対称性分析器"""
    
    def __init__(self):
        # 対称性評価基準
        self.SYMMETRY_THRESHOLDS = {
            'excellent': 5.0,    # 5%以下の非対称性
            'good': 10.0,        # 10%以下の非対称性
            'fair': 15.0,        # 15%以下の非対称性
            'poor': 20.0         # 20%以上の非対称性
        }
        
        # 重み付け係数（臨床的重要度に基づく）
        self.CLINICAL_WEIGHTS = {
            'step_length': 0.25,      # 歩幅対称性
            'stance_time': 0.20,      # 立脚時間対称性
            'swing_time': 0.15,       # 遊脚時間対称性
            'hip_flexion': 0.15,      # 股関節屈曲対称性
            'knee_flexion': 0.15,     # 膝関節屈曲対称性
            'ankle_flexion': 0.10     # 足関節背屈対称性
        }
    
    def analyze_gait_symmetry(
        self, 
        gait_cycles: List[GaitCycle], 
        joint_angles: Optional[JointAngles] = None
    ) -> SymmetryIndices:
        """
        歩行対称性の包括的分析
        
        Args:
            gait_cycles: 歩行周期データ
            joint_angles: 関節角度データ（オプション）
            
        Returns:
            SymmetryIndices: 対称性指標
        """
        logger.info("Starting symmetry analysis", cycles=len(gait_cycles))
        
        if not gait_cycles:
            return self._create_empty_symmetry_indices()
        
        # 左右別にデータを分離
        left_cycles = [gc for gc in gait_cycles if gc.side == 'left']
        right_cycles = [gc for gc in gait_cycles if gc.side == 'right']
        
        if not left_cycles or not right_cycles:
            logger.warning("Insufficient data for symmetry analysis")
            return self._create_partial_symmetry_indices(gait_cycles)
        
        # 時空間パラメータの対称性
        spatial_symmetry = self._analyze_spatial_symmetry(left_cycles, right_cycles)
        temporal_symmetry = self._analyze_temporal_symmetry(left_cycles, right_cycles)
        
        # 関節角度の対称性
        joint_symmetry = {}
        if joint_angles:
            joint_symmetry = self._analyze_joint_symmetry(joint_angles, gait_cycles)
        
        # 総合対称性スコア計算
        overall_score = self._calculate_overall_symmetry_score(
            spatial_symmetry, temporal_symmetry, joint_symmetry
        )
        
        result = SymmetryIndices(
            step_length_symmetry_percent=spatial_symmetry.get('step_length', 0.0),
            stance_time_symmetry_percent=temporal_symmetry.get('stance_time', 0.0),
            swing_time_symmetry_percent=temporal_symmetry.get('swing_time', 0.0),
            hip_flexion_symmetry_percent=joint_symmetry.get('hip_flexion', 0.0),
            knee_flexion_symmetry_percent=joint_symmetry.get('knee_flexion', 0.0),
            ankle_dorsiflexion_symmetry_percent=joint_symmetry.get('ankle_flexion', 0.0),
            overall_symmetry_score=overall_score
        )
        
        logger.info(
            "Symmetry analysis completed",
            overall_score=overall_score,
            step_length_asymmetry=spatial_symmetry.get('step_length', 0.0)
        )
        
        return result
    
    def _analyze_spatial_symmetry(
        self, 
        left_cycles: List[GaitCycle], 
        right_cycles: List[GaitCycle]
    ) -> Dict[str, float]:
        """空間的パラメータの対称性分析"""
        spatial_symmetry = {}
        
        # 歩幅対称性
        left_step_lengths = [gc.step_length_m for gc in left_cycles]
        right_step_lengths = [gc.step_length_m for gc in right_cycles]
        
        if left_step_lengths and right_step_lengths:
            left_mean = statistics.mean(left_step_lengths)
            right_mean = statistics.mean(right_step_lengths)
            step_length_si = self._calculate_symmetry_index(left_mean, right_mean)
            spatial_symmetry['step_length'] = step_length_si
        
        # 歩隔対称性
        left_step_widths = [gc.step_width_m for gc in left_cycles]
        right_step_widths = [gc.step_width_m for gc in right_cycles]
        
        if left_step_widths and right_step_widths:
            left_mean = statistics.mean(left_step_widths)
            right_mean = statistics.mean(right_step_widths)
            step_width_si = self._calculate_symmetry_index(left_mean, right_mean)
            spatial_symmetry['step_width'] = step_width_si
        
        return spatial_symmetry
    
    def _analyze_temporal_symmetry(
        self, 
        left_cycles: List[GaitCycle], 
        right_cycles: List[GaitCycle]
    ) -> Dict[str, float]:
        """時間的パラメータの対称性分析"""
        temporal_symmetry = {}
        
        # 立脚時間対称性
        left_stance_times = [gc.stance_time_seconds for gc in left_cycles]
        right_stance_times = [gc.stance_time_seconds for gc in right_cycles]
        
        if left_stance_times and right_stance_times:
            left_mean = statistics.mean(left_stance_times)
            right_mean = statistics.mean(right_stance_times)
            stance_time_si = self._calculate_symmetry_index(left_mean, right_mean)
            temporal_symmetry['stance_time'] = stance_time_si
        
        # 遊脚時間対称性
        left_swing_times = [gc.swing_time_seconds for gc in left_cycles]
        right_swing_times = [gc.swing_time_seconds for gc in right_cycles]
        
        if left_swing_times and right_swing_times:
            left_mean = statistics.mean(left_swing_times)
            right_mean = statistics.mean(right_swing_times)
            swing_time_si = self._calculate_symmetry_index(left_mean, right_mean)
            temporal_symmetry['swing_time'] = swing_time_si
        
        # 歩行周期時間対称性
        left_cycle_times = [gc.duration_seconds for gc in left_cycles]
        right_cycle_times = [gc.duration_seconds for gc in right_cycles]
        
        if left_cycle_times and right_cycle_times:
            left_mean = statistics.mean(left_cycle_times)
            right_mean = statistics.mean(right_cycle_times)
            cycle_time_si = self._calculate_symmetry_index(left_mean, right_mean)
            temporal_symmetry['cycle_time'] = cycle_time_si
        
        return temporal_symmetry
    
    def _analyze_joint_symmetry(
        self, 
        joint_angles: JointAngles, 
        gait_cycles: List[GaitCycle]
    ) -> Dict[str, float]:
        """関節角度の対称性分析"""
        joint_symmetry = {}
        
        if not joint_angles.frame_timestamps:
            return joint_symmetry
        
        # 左右の歩行周期を時間で対応付け
        left_cycles = [gc for gc in gait_cycles if gc.side == 'left']
        right_cycles = [gc for gc in gait_cycles if gc.side == 'right']
        
        # 各関節の対称性を分析
        joint_data = {
            'hip_flexion': joint_angles.hip_flexion_deg,
            'knee_flexion': joint_angles.knee_flexion_deg,
            'ankle_flexion': joint_angles.ankle_dorsiflexion_deg
        }
        
        for joint_name, angles in joint_data.items():
            if angles and len(angles) > 0:
                # 左右の歩行周期での角度ピーク値を比較
                left_peaks = self._extract_cycle_peaks(angles, left_cycles, joint_angles.frame_timestamps)
                right_peaks = self._extract_cycle_peaks(angles, right_cycles, joint_angles.frame_timestamps)
                
                if left_peaks and right_peaks:
                    left_mean = statistics.mean(left_peaks)
                    right_mean = statistics.mean(right_peaks)
                    symmetry_index = self._calculate_symmetry_index(left_mean, right_mean)
                    joint_symmetry[joint_name] = symmetry_index
        
        return joint_symmetry
    
    def _extract_cycle_peaks(
        self, 
        angles: List[float], 
        cycles: List[GaitCycle], 
        timestamps: List[float]
    ) -> List[float]:
        """歩行周期ごとの角度ピーク値抽出"""
        peaks = []
        
        for cycle in cycles:
            # 歩行周期の時間範囲に対応するフレームを特定
            cycle_start_time = cycle.start_frame / 30.0  # 仮のfps
            cycle_end_time = cycle.end_frame / 30.0
            
            # 該当時間範囲の角度データを抽出
            cycle_angles = []
            for i, timestamp in enumerate(timestamps):
                if cycle_start_time <= timestamp <= cycle_end_time and i < len(angles):
                    cycle_angles.append(angles[i])
            
            # ピーク値（最大値）を取得
            if cycle_angles:
                peak_value = max(cycle_angles)
                peaks.append(peak_value)
        
        return peaks
    
    def _calculate_symmetry_index(self, left_value: float, right_value: float) -> float:
        """
        対称性指数計算
        
        SI = |left - right| / ((left + right) / 2) * 100
        
        Args:
            left_value: 左側の値
            right_value: 右側の値
            
        Returns:
            float: 対称性指数（%）、0%が完全対称
        """
        if left_value == 0 and right_value == 0:
            return 0.0
        
        mean_value = (left_value + right_value) / 2
        if mean_value == 0:
            return 0.0
        
        symmetry_index = abs(left_value - right_value) / mean_value * 100
        return min(100.0, symmetry_index)  # 最大100%でクリップ
    
    def _calculate_overall_symmetry_score(
        self, 
        spatial_symmetry: Dict[str, float],
        temporal_symmetry: Dict[str, float],
        joint_symmetry: Dict[str, float]
    ) -> float:
        """総合対称性スコア計算"""
        weighted_asymmetries = []
        
        # 各パラメータの非対称性を重み付きで集計
        asymmetry_data = {
            **spatial_symmetry,
            **temporal_symmetry,
            **joint_symmetry
        }
        
        for param_name, asymmetry_percent in asymmetry_data.items():
            weight = self.CLINICAL_WEIGHTS.get(param_name, 0.1)
            weighted_asymmetries.append(asymmetry_percent * weight)
        
        if not weighted_asymmetries:
            return 50.0  # デフォルトスコア
        
        # 平均非対称性を計算
        avg_asymmetry = sum(weighted_asymmetries)
        
        # 対称性スコア = 100 - 非対称性%
        symmetry_score = 100.0 - avg_asymmetry
        
        return max(0.0, min(100.0, symmetry_score))
    
    def _create_empty_symmetry_indices(self) -> SymmetryIndices:
        """空の対称性指標作成"""
        return SymmetryIndices(
            step_length_symmetry_percent=0.0,
            stance_time_symmetry_percent=0.0,
            swing_time_symmetry_percent=0.0,
            hip_flexion_symmetry_percent=0.0,
            knee_flexion_symmetry_percent=0.0,
            ankle_dorsiflexion_symmetry_percent=0.0,
            overall_symmetry_score=50.0
        )
    
    def _create_partial_symmetry_indices(self, gait_cycles: List[GaitCycle]) -> SymmetryIndices:
        """部分的対称性指標作成（左右どちらか片方のみの場合）"""
        # 変動性ベースの評価
        if gait_cycles:
            step_lengths = [gc.step_length_m for gc in gait_cycles]
            stance_times = [gc.stance_time_seconds for gc in gait_cycles]
            
            # 変動係数を対称性の代替指標として使用
            step_cv = (np.std(step_lengths) / np.mean(step_lengths) * 100) if step_lengths else 0.0
            stance_cv = (np.std(stance_times) / np.mean(stance_times) * 100) if stance_times else 0.0
            
            overall_score = max(0.0, 100.0 - (step_cv + stance_cv) / 2)
        else:
            step_cv = stance_cv = 0.0
            overall_score = 50.0
        
        return SymmetryIndices(
            step_length_symmetry_percent=step_cv,
            stance_time_symmetry_percent=stance_cv,
            swing_time_symmetry_percent=0.0,
            hip_flexion_symmetry_percent=0.0,
            knee_flexion_symmetry_percent=0.0,
            ankle_dorsiflexion_symmetry_percent=0.0,
            overall_symmetry_score=overall_score
        )
    
    def evaluate_symmetry_quality(self, symmetry_indices: SymmetryIndices) -> Dict[str, str]:
        """対称性品質評価"""
        evaluations = {}
        
        # 各指標の評価
        metrics = {
            'step_length': symmetry_indices.step_length_symmetry_percent,
            'stance_time': symmetry_indices.stance_time_symmetry_percent,
            'swing_time': symmetry_indices.swing_time_symmetry_percent,
            'overall': 100.0 - symmetry_indices.overall_symmetry_score  # 非対称性%に変換
        }
        
        for metric_name, asymmetry_percent in metrics.items():
            if asymmetry_percent <= self.SYMMETRY_THRESHOLDS['excellent']:
                evaluations[metric_name] = '優秀'
            elif asymmetry_percent <= self.SYMMETRY_THRESHOLDS['good']:
                evaluations[metric_name] = '良好'
            elif asymmetry_percent <= self.SYMMETRY_THRESHOLDS['fair']:
                evaluations[metric_name] = '普通'
            else:
                evaluations[metric_name] = '要改善'
        
        return evaluations
    
    def generate_symmetry_recommendations(
        self, 
        symmetry_indices: SymmetryIndices
    ) -> List[str]:
        """対称性改善の推奨事項生成"""
        recommendations = []
        
        # 歩幅非対称性
        if symmetry_indices.step_length_symmetry_percent > 10.0:
            recommendations.append("歩幅の左右差が大きいため、バランス訓練や片脚立位練習を行ってください")
        
        # 立脚時間非対称性
        if symmetry_indices.stance_time_symmetry_percent > 10.0:
            recommendations.append("立脚時間の非対称性があります。荷重訓練や下肢筋力強化を検討してください")
        
        # 総合対称性
        if symmetry_indices.overall_symmetry_score < 70.0:
            recommendations.append("全体的な歩行対称性の改善が必要です。理学療法士による包括的評価を推奨します")
        
        # 関節角度非対称性
        if symmetry_indices.hip_flexion_symmetry_percent > 15.0:
            recommendations.append("股関節の動きに左右差があります。股関節可動域訓練を行ってください")
        
        if not recommendations:
            recommendations.append("良好な歩行対称性です。現在の活動レベルを維持してください")
        
        return recommendations