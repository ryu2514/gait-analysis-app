"""
拡張時空間パラメータ分析器
Enhanced Spatiotemporal Parameter Analyzer
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import statistics
from dataclasses import dataclass

from app.models.gait_models import GaitCycle, DetailedSpatiotemporalParameters
from app.core.advanced_logger import get_logger

logger = get_logger(__name__)


class EnhancedSpatiotemporalAnalyzer:
    """拡張時空間パラメータ分析器"""
    
    def __init__(self):
        # 正常歩行の参照値（年齢別）
        self.NORMAL_RANGES = {
            'gait_speed': (1.2, 1.4),      # m/s
            'cadence': (110, 130),         # steps/min
            'stride_length': (140, 160),   # cm
            'step_length': (65, 75),       # cm
            'stance_percent': (58, 62),    # % gait cycle
            'swing_percent': (38, 42),     # % gait cycle
            'double_support_percent': (10, 12),  # % gait cycle
            'stance_asymmetry': (0, 5),    # %
        }
    
    def analyze_detailed_spatiotemporal_parameters(
        self, 
        gait_cycles: List[GaitCycle], 
        landmarks_data: List[Dict],
        scale_factor: float = 1.0,
        fps: float = 30.0
    ) -> DetailedSpatiotemporalParameters:
        """
        詳細時空間パラメータの分析
        
        Args:
            gait_cycles: 歩行周期データ
            landmarks_data: ランドマークデータ
            scale_factor: スケール補正係数
            fps: フレームレート
            
        Returns:
            DetailedSpatiotemporalParameters: 詳細時空間パラメータ
        """
        logger.info("Starting enhanced spatiotemporal analysis", 
                   cycles=len(gait_cycles), fps=fps)
        
        if not gait_cycles:
            raise ValueError("歩行周期データが空です")
        
        # 左右別に分離
        left_cycles = [gc for gc in gait_cycles if gc.side == 'left']
        right_cycles = [gc for gc in gait_cycles if gc.side == 'right']
        
        # 基本パラメータ計算
        basic_params = self._calculate_enhanced_basic_parameters(
            gait_cycles, left_cycles, right_cycles, scale_factor
        )
        
        # 時間パラメータ（%歩行周期）計算
        temporal_percentages = self._calculate_temporal_percentages(
            gait_cycles, left_cycles, right_cycles
        )
        
        # 左右別速度・対称性計算
        velocity_params = self._calculate_velocity_and_asymmetry(
            left_cycles, right_cycles, scale_factor
        )
        
        result = DetailedSpatiotemporalParameters(
            gait_speed_ms=basic_params['gait_speed'],
            cadence_steps_per_min=basic_params['cadence'],
            step_length_cm=basic_params['step_length_cm'],
            stride_length_cm=basic_params['stride_length_cm'],
            stance_time_percent=temporal_percentages['stance_percent'],
            swing_time_percent=temporal_percentages['swing_percent'],
            double_support_percent=temporal_percentages['double_support_percent'],
            left_side_speed_ms=velocity_params['left_speed'],
            right_side_speed_ms=velocity_params['right_speed'],
            stance_time_asymmetry_percent=velocity_params['stance_asymmetry']
        )
        
        logger.info("Enhanced spatiotemporal analysis completed",
                   gait_speed=result.gait_speed_ms,
                   cadence=result.cadence_steps_per_min,
                   stride_length=result.stride_length_cm)
        
        return result
    
    def _calculate_enhanced_basic_parameters(
        self, 
        all_cycles: List[GaitCycle],
        left_cycles: List[GaitCycle], 
        right_cycles: List[GaitCycle],
        scale_factor: float
    ) -> Dict[str, float]:
        """拡張基本パラメータ計算"""
        
        # 歩行ピッチ（ケイデンス）計算
        cycle_times = [gc.duration_seconds for gc in all_cycles]
        if not cycle_times:
            return self._get_default_basic_params()
        
        avg_cycle_time = statistics.mean(cycle_times)
        cadence = (60.0 / avg_cycle_time) * 2 if avg_cycle_time > 0 else 0  # 両足での歩数
        
        # 歩幅・ストライド長計算（cm）
        step_lengths_m = [gc.step_length_m * scale_factor for gc in all_cycles]
        avg_step_length_m = statistics.mean(step_lengths_m) if step_lengths_m else 0.0
        step_length_cm = avg_step_length_m * 100
        
        # ストライド長（左右歩幅の合計）
        if left_cycles and right_cycles:
            left_lengths = [gc.step_length_m * scale_factor for gc in left_cycles]
            right_lengths = [gc.step_length_m * scale_factor for gc in right_cycles]
            stride_length_cm = (statistics.mean(left_lengths) + statistics.mean(right_lengths)) * 100
        else:
            stride_length_cm = step_length_cm * 2
        
        # 歩行速度計算
        gait_speed = (stride_length_cm / 100) / (avg_cycle_time * 2) if avg_cycle_time > 0 else 0.0
        
        return {
            'gait_speed': gait_speed,
            'cadence': int(round(cadence)),
            'step_length_cm': step_length_cm,
            'stride_length_cm': stride_length_cm
        }
    
    def _calculate_temporal_percentages(
        self, 
        all_cycles: List[GaitCycle],
        left_cycles: List[GaitCycle], 
        right_cycles: List[GaitCycle]
    ) -> Dict[str, float]:
        """時間パラメータ（%歩行周期）計算"""
        
        # 立脚時間・遊脚時間（%歩行周期）
        stance_ratios = [gc.stance_ratio for gc in all_cycles if gc.stance_ratio > 0]
        if stance_ratios:
            avg_stance_ratio = statistics.mean(stance_ratios)
            stance_percent = avg_stance_ratio * 100
            swing_percent = 100 - stance_percent
        else:
            stance_percent = 60.0  # デフォルト値
            swing_percent = 40.0
        
        # 両脚支持時間（%歩行周期）
        # 典型的には立脚時間の約20%
        double_support_percent = stance_percent * 0.2
        
        return {
            'stance_percent': stance_percent,
            'swing_percent': swing_percent,
            'double_support_percent': double_support_percent
        }
    
    def _calculate_velocity_and_asymmetry(
        self, 
        left_cycles: List[GaitCycle], 
        right_cycles: List[GaitCycle],
        scale_factor: float
    ) -> Dict[str, float]:
        """左右別速度・対称性計算"""
        
        # 左右別平均速度
        left_speed = 0.0
        right_speed = 0.0
        
        if left_cycles:
            left_lengths = [gc.step_length_m * scale_factor for gc in left_cycles]
            left_times = [gc.duration_seconds for gc in left_cycles]
            if left_lengths and left_times:
                left_speed = statistics.mean(left_lengths) / statistics.mean(left_times)
        
        if right_cycles:
            right_lengths = [gc.step_length_m * scale_factor for gc in right_cycles]
            right_times = [gc.duration_seconds for gc in right_cycles]
            if right_lengths and right_times:
                right_speed = statistics.mean(right_lengths) / statistics.mean(right_times)
        
        # 立脚時間非対称性（Stance Time Asymmetry）
        stance_asymmetry = 0.0
        if left_cycles and right_cycles:
            left_stance_times = [gc.stance_time_seconds for gc in left_cycles]
            right_stance_times = [gc.stance_time_seconds for gc in right_cycles]
            
            if left_stance_times and right_stance_times:
                left_avg = statistics.mean(left_stance_times)
                right_avg = statistics.mean(right_stance_times)
                
                # 対称性指数（%）= |左-右| / ((左+右)/2) × 100
                if (left_avg + right_avg) > 0:
                    stance_asymmetry = abs(left_avg - right_avg) / ((left_avg + right_avg) / 2) * 100
        
        return {
            'left_speed': left_speed,
            'right_speed': right_speed,
            'stance_asymmetry': stance_asymmetry
        }
    
    def _get_default_basic_params(self) -> Dict[str, float]:
        """デフォルト基本パラメータ"""
        return {
            'gait_speed': 0.0,
            'cadence': 0,
            'step_length_cm': 0.0,
            'stride_length_cm': 0.0
        }
    
    def evaluate_detailed_parameters(
        self, 
        params: DetailedSpatiotemporalParameters
    ) -> Dict[str, Dict[str, str]]:
        """詳細パラメータ評価"""
        evaluation = {}
        
        # 歩行速度評価
        evaluation['gait_speed'] = self._evaluate_single_parameter(
            params.gait_speed_ms,
            self.NORMAL_RANGES['gait_speed'],
            "歩行速度",
            "m/s"
        )
        
        # ケイデンス評価
        evaluation['cadence'] = self._evaluate_single_parameter(
            params.cadence_steps_per_min,
            self.NORMAL_RANGES['cadence'],
            "ケイデンス",
            "歩/分"
        )
        
        # ストライド長評価
        evaluation['stride_length'] = self._evaluate_single_parameter(
            params.stride_length_cm,
            self.NORMAL_RANGES['stride_length'],
            "ストライド長",
            "cm"
        )
        
        # 立脚時間評価
        evaluation['stance_time'] = self._evaluate_single_parameter(
            params.stance_time_percent,
            self.NORMAL_RANGES['stance_percent'],
            "立脚時間",
            "% 歩行周期"
        )
        
        # 対称性評価
        evaluation['stance_asymmetry'] = self._evaluate_single_parameter(
            params.stance_time_asymmetry_percent,
            self.NORMAL_RANGES['stance_asymmetry'],
            "立脚時間対称性",
            "%",
            lower_is_better=True
        )
        
        return evaluation
    
    def _evaluate_single_parameter(
        self, 
        value: float, 
        normal_range: Tuple[float, float],
        param_name: str,
        unit: str,
        lower_is_better: bool = False
    ) -> Dict[str, str]:
        """単一パラメータ評価"""
        min_normal, max_normal = normal_range
        
        if min_normal <= value <= max_normal:
            status = "正常"
            color = "green"
        elif (not lower_is_better and value < min_normal) or (lower_is_better and value > max_normal):
            if (not lower_is_better and value < min_normal * 0.8) or (lower_is_better and value > max_normal * 1.5):
                status = "著明異常"
                color = "red"
            else:
                status = "軽度異常"
                color = "orange"
        else:
            if (not lower_is_better and value > max_normal * 1.2) or (lower_is_better and value < min_normal * 0.5):
                status = "著明異常"
                color = "red"
            else:
                status = "軽度異常"
                color = "orange"
        
        return {
            'value': f"{value:.1f}{unit}",
            'status': status,
            'color': color,
            'normal_range': f"{min_normal}-{max_normal}{unit}",
            'description': self._get_parameter_description(param_name, status, value, normal_range)
        }
    
    def _get_parameter_description(
        self, 
        param_name: str, 
        status: str, 
        value: float, 
        normal_range: Tuple[float, float]
    ) -> str:
        """パラメータ説明文生成"""
        descriptions = {
            "歩行速度": {
                "正常": "正常な歩行速度です。",
                "軽度異常": "歩行速度に軽度の異常があります。",
                "著明異常": "歩行速度に著明な異常があります。バランス訓練や筋力強化が必要です。"
            },
            "ケイデンス": {
                "正常": "正常な歩行リズムです。",
                "軽度異常": "歩行リズムに軽度の異常があります。",
                "著明異常": "歩行リズムに著明な異常があります。歩行練習が推奨されます。"
            },
            "ストライド長": {
                "正常": "正常なストライド長です。",
                "軽度異常": "ストライド長に軽度の異常があります。",
                "著明異常": "ストライド長に著明な異常があります。可動域訓練が推奨されます。"
            },
            "立脚時間": {
                "正常": "正常な立脚時間比率です。",
                "軽度異常": "立脚時間比率に軽度の異常があります。",
                "著明異常": "立脚時間比率に著明な異常があります。バランス評価が必要です。"
            },
            "立脚時間対称性": {
                "正常": "左右の立脚時間は対称的です。",
                "軽度異常": "左右の立脚時間に軽度の非対称性があります。",
                "著明異常": "左右の立脚時間に著明な非対称性があります。片麻痺や疼痛の可能性があります。"
            }
        }
        
        return descriptions.get(param_name, {}).get(status, "評価不明")
    
    def generate_clinical_report_section(
        self, 
        params: DetailedSpatiotemporalParameters,
        evaluations: Dict[str, Dict[str, str]]
    ) -> str:
        """臨床レポート用セクション生成"""
        sections = []
        
        # 基本パラメータサマリー
        sections.append("=== 時空間パラメータ ===")
        sections.append(f"歩行速度: {params.gait_speed_ms:.2f} m/s ({evaluations['gait_speed']['status']})")
        sections.append(f"ケイデンス: {params.cadence_steps_per_min} 歩/分 ({evaluations['cadence']['status']})")
        sections.append(f"歩幅: {params.step_length_cm:.1f} cm")
        sections.append(f"ストライド長: {params.stride_length_cm:.1f} cm ({evaluations['stride_length']['status']})")
        sections.append("")
        
        # 時間的パラメータ
        sections.append("=== 時間的パラメータ（%歩行周期） ===")
        sections.append(f"立脚時間: {params.stance_time_percent:.1f}% ({evaluations['stance_time']['status']})")
        sections.append(f"遊脚時間: {params.swing_time_percent:.1f}%")
        sections.append(f"両脚支持時間: {params.double_support_percent:.1f}%")
        sections.append("")
        
        # 対称性分析
        sections.append("=== 左右対称性分析 ===")
        sections.append(f"左側平均速度: {params.left_side_speed_ms:.2f} m/s")
        sections.append(f"右側平均速度: {params.right_side_speed_ms:.2f} m/s")
        sections.append(f"立脚時間非対称性: {params.stance_time_asymmetry_percent:.1f}% ({evaluations['stance_asymmetry']['status']})")
        
        return "\n".join(sections)