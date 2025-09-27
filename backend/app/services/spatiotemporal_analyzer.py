"""
時空間パラメータ計算エンジン
歩行周期から詳細な時空間的指標を算出
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import statistics
from dataclasses import dataclass

from app.models.gait_models import GaitCycle, SpatiotemporalParameters
from app.core.logging import StructuredLogger

logger = StructuredLogger(__name__)


@dataclass
class GaitMetrics:
    """歩行指標"""
    mean: float
    std: float
    cv: float  # 変動係数
    min_val: float
    max_val: float
    
    @classmethod
    def from_values(cls, values: List[float]) -> 'GaitMetrics':
        """値リストから指標を計算"""
        if not values:
            return cls(0.0, 0.0, 0.0, 0.0, 0.0)
        
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0.0
        cv_val = (std_val / mean_val * 100) if mean_val != 0 else 0.0
        
        return cls(
            mean=mean_val,
            std=std_val,
            cv=cv_val,
            min_val=min(values),
            max_val=max(values)
        )


class SpatiotemporalAnalyzer:
    """時空間パラメータ分析器"""
    
    def __init__(self):
        # 正常歩行の参照値
        self.NORMAL_RANGES = {
            'gait_speed': (1.2, 1.4),      # m/s
            'cadence': (110, 120),         # steps/min
            'stride_length': (1.4, 1.6),   # m
            'step_length': (0.65, 0.75),   # m
            'stance_ratio': (0.58, 0.62),  # ratio
            'step_width': (0.08, 0.12),    # m
            'double_support': (0.10, 0.12) # s
        }
    
    def analyze_spatiotemporal_parameters(
        self, 
        gait_cycles: List[GaitCycle], 
        scale_factor: float = 1.0
    ) -> SpatiotemporalParameters:
        """
        時空間パラメータの詳細分析
        
        Args:
            gait_cycles: 歩行周期データ
            scale_factor: スケール補正係数
            
        Returns:
            SpatiotemporalParameters: 時空間パラメータ
        """
        logger.info("Starting spatiotemporal analysis", cycles=len(gait_cycles))
        
        if not gait_cycles:
            raise ValueError("歩行周期データが空です")
        
        # 左右別に分離
        left_cycles = [gc for gc in gait_cycles if gc.side == 'left']
        right_cycles = [gc for gc in gait_cycles if gc.side == 'right']
        
        # 基本指標の計算
        basic_params = self._calculate_basic_parameters(
            gait_cycles, left_cycles, right_cycles, scale_factor
        )
        
        # 時間的パラメータの計算
        temporal_params = self._calculate_temporal_parameters(
            gait_cycles, left_cycles, right_cycles
        )
        
        # 空間的パラメータの計算
        spatial_params = self._calculate_spatial_parameters(
            gait_cycles, left_cycles, right_cycles, scale_factor
        )
        
        # 両脚支持時間の計算
        double_support_time = self._calculate_double_support_time(gait_cycles)
        
        result = SpatiotemporalParameters(
            gait_speed_ms=basic_params['gait_speed'],
            cadence_steps_per_min=basic_params['cadence'],
            stride_length_m=spatial_params['stride_length'],
            stride_time_s=temporal_params['stride_time'],
            left_step_length_m=spatial_params['left_step_length'],
            right_step_length_m=spatial_params['right_step_length'],
            left_stance_time_s=temporal_params['left_stance_time'],
            right_stance_time_s=temporal_params['right_stance_time'],
            double_support_time_s=double_support_time
        )
        
        logger.info(
            "Spatiotemporal analysis completed",
            gait_speed=result.gait_speed_ms,
            cadence=result.cadence_steps_per_min
        )
        
        return result
    
    def _calculate_basic_parameters(
        self, 
        all_cycles: List[GaitCycle],
        left_cycles: List[GaitCycle], 
        right_cycles: List[GaitCycle],
        scale_factor: float
    ) -> Dict[str, float]:
        """基本的な歩行パラメータ計算"""
        
        # 歩行速度計算
        step_lengths = [gc.step_length_m * scale_factor for gc in all_cycles]
        cycle_times = [gc.duration_seconds for gc in all_cycles]
        
        if not step_lengths or not cycle_times:
            return {'gait_speed': 0.0, 'cadence': 0}
        
        # 平均歩行速度 = 平均歩幅 / 平均歩行周期時間
        avg_step_length = statistics.mean(step_lengths)
        avg_cycle_time = statistics.mean(cycle_times)
        gait_speed = avg_step_length / avg_cycle_time if avg_cycle_time > 0 else 0.0
        
        # ケイデンス計算（歩/分）
        cadence = 60.0 / avg_cycle_time if avg_cycle_time > 0 else 0
        
        return {
            'gait_speed': gait_speed,
            'cadence': int(round(cadence))
        }
    
    def _calculate_temporal_parameters(
        self, 
        all_cycles: List[GaitCycle],
        left_cycles: List[GaitCycle], 
        right_cycles: List[GaitCycle]
    ) -> Dict[str, float]:
        """時間的パラメータ計算"""
        
        # ストライド時間（左右一歩ずつの合計時間）
        if left_cycles and right_cycles:
            # 左右のペアを作成してストライド時間を計算
            stride_times = []
            for i in range(min(len(left_cycles), len(right_cycles))):
                stride_time = left_cycles[i].duration_seconds + right_cycles[i].duration_seconds
                stride_times.append(stride_time)
            
            avg_stride_time = statistics.mean(stride_times) if stride_times else 0.0
        else:
            # 片側のみの場合は2倍して推定
            all_durations = [gc.duration_seconds for gc in all_cycles]
            avg_stride_time = statistics.mean(all_durations) * 2 if all_durations else 0.0
        
        # 左右の立脚時間
        left_stance_times = [gc.stance_time_seconds for gc in left_cycles]
        right_stance_times = [gc.stance_time_seconds for gc in right_cycles]
        
        left_stance_time = statistics.mean(left_stance_times) if left_stance_times else 0.0
        right_stance_time = statistics.mean(right_stance_times) if right_stance_times else 0.0
        
        return {
            'stride_time': avg_stride_time,
            'left_stance_time': left_stance_time,
            'right_stance_time': right_stance_time
        }
    
    def _calculate_spatial_parameters(
        self, 
        all_cycles: List[GaitCycle],
        left_cycles: List[GaitCycle], 
        right_cycles: List[GaitCycle],
        scale_factor: float
    ) -> Dict[str, float]:
        """空間的パラメータ計算"""
        
        # 左右の歩幅
        left_step_lengths = [gc.step_length_m * scale_factor for gc in left_cycles]
        right_step_lengths = [gc.step_length_m * scale_factor for gc in right_cycles]
        
        left_step_length = statistics.mean(left_step_lengths) if left_step_lengths else 0.0
        right_step_length = statistics.mean(right_step_lengths) if right_step_lengths else 0.0
        
        # ストライド長（左右歩幅の合計）
        stride_length = left_step_length + right_step_length
        
        return {
            'left_step_length': left_step_length,
            'right_step_length': right_step_length,
            'stride_length': stride_length
        }
    
    def _calculate_double_support_time(self, gait_cycles: List[GaitCycle]) -> float:
        """両脚支持時間の計算"""
        # 簡易実装：立脚時間の重複部分を推定
        left_cycles = [gc for gc in gait_cycles if gc.side == 'left']
        right_cycles = [gc for gc in gait_cycles if gc.side == 'right']
        
        if not left_cycles or not right_cycles:
            return 0.1  # デフォルト値
        
        # 立脚時間の約20%が両脚支持時間
        avg_stance_time = statistics.mean([
            gc.stance_time_seconds for gc in gait_cycles
        ])
        
        double_support_time = avg_stance_time * 0.2
        return double_support_time
    
    def calculate_gait_stability_metrics(self, gait_cycles: List[GaitCycle]) -> Dict[str, float]:
        """歩行安定性指標の計算"""
        if len(gait_cycles) < 3:
            return {}
        
        # 歩行周期時間の変動性
        cycle_times = [gc.duration_seconds for gc in gait_cycles]
        time_metrics = GaitMetrics.from_values(cycle_times)
        
        # 歩幅の変動性
        step_lengths = [gc.step_length_m for gc in gait_cycles]
        length_metrics = GaitMetrics.from_values(step_lengths)
        
        # 立脚比率の変動性
        stance_ratios = [gc.stance_ratio for gc in gait_cycles]
        stance_metrics = GaitMetrics.from_values(stance_ratios)
        
        return {
            'cycle_time_cv': time_metrics.cv,
            'step_length_cv': length_metrics.cv,
            'stance_ratio_cv': stance_metrics.cv,
            'overall_stability': self._calculate_overall_stability([
                time_metrics.cv, length_metrics.cv, stance_metrics.cv
            ])
        }
    
    def _calculate_overall_stability(self, cv_values: List[float]) -> float:
        """総合安定性スコア計算"""
        if not cv_values:
            return 0.0
        
        # 変動係数の逆数を使用（低い変動 = 高い安定性）
        avg_cv = statistics.mean(cv_values)
        
        # 変動係数5%以下を100点、20%以上を0点として正規化
        if avg_cv <= 5.0:
            stability = 100.0
        elif avg_cv >= 20.0:
            stability = 0.0
        else:
            stability = 100.0 * (20.0 - avg_cv) / 15.0
        
        return max(0.0, min(100.0, stability))
    
    def evaluate_gait_performance(
        self, 
        params: SpatiotemporalParameters, 
        user_age: Optional[int] = None
    ) -> Dict[str, str]:
        """歩行パフォーマンス評価"""
        evaluation = {}
        
        # 歩行速度評価
        speed_eval = self._evaluate_parameter(
            params.gait_speed_ms, 
            self.NORMAL_RANGES['gait_speed'],
            'speed'
        )
        evaluation['gait_speed'] = speed_eval
        
        # ケイデンス評価
        cadence_eval = self._evaluate_parameter(
            params.cadence_steps_per_min,
            self.NORMAL_RANGES['cadence'],
            'cadence'
        )
        evaluation['cadence'] = cadence_eval
        
        # 立脚比率評価（左右平均）
        avg_stance_ratio = (
            params.left_stance_time_s + params.right_stance_time_s
        ) / (2 * params.stride_time_s) if params.stride_time_s > 0 else 0
        
        stance_eval = self._evaluate_parameter(
            avg_stance_ratio,
            self.NORMAL_RANGES['stance_ratio'],
            'stance_ratio'
        )
        evaluation['stance_ratio'] = stance_eval
        
        return evaluation
    
    def _evaluate_parameter(
        self, 
        value: float, 
        normal_range: Tuple[float, float],
        param_type: str
    ) -> str:
        """個別パラメータの評価"""
        min_normal, max_normal = normal_range
        
        if min_normal <= value <= max_normal:
            return '正常'
        elif value < min_normal * 0.8:
            return '著明低下'
        elif value < min_normal:
            return '軽度低下'
        elif value > max_normal * 1.2:
            return '著明増加'
        elif value > max_normal:
            return '軽度増加'
        else:
            return '境界域'
    
    def generate_performance_summary(
        self, 
        params: SpatiotemporalParameters,
        evaluations: Dict[str, str]
    ) -> str:
        """パフォーマンス要約生成"""
        speed_kmh = params.gait_speed_ms * 3.6
        
        summary_parts = []
        summary_parts.append(f"歩行速度: {params.gait_speed_ms:.2f}m/s ({speed_kmh:.1f}km/h) - {evaluations.get('gait_speed', '不明')}")
        summary_parts.append(f"ケイデンス: {params.cadence_steps_per_min}歩/分 - {evaluations.get('cadence', '不明')}")
        summary_parts.append(f"ストライド長: {params.stride_length_m:.2f}m")
        
        # 左右対称性
        step_asymmetry = abs(params.left_step_length_m - params.right_step_length_m)
        if step_asymmetry < 0.05:
            asymmetry_desc = "対称"
        elif step_asymmetry < 0.1:
            asymmetry_desc = "軽度非対称"
        else:
            asymmetry_desc = "明らかな非対称"
        
        summary_parts.append(f"左右対称性: {asymmetry_desc}")
        
        return "\n".join(summary_parts)