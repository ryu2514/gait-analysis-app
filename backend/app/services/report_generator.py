"""
歩行分析レポート生成サービス
PDF/PNG形式でのレポート出力機能
"""

import io
import os
import base64
from datetime import datetime
from typing import Dict, Any, Optional, List
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import json

from app.models.gait_models import (
    GaitAnalysisResponse, SpatiotemporalParameters, 
    SymmetryIndices, JointAngles, GaitCycle
)
from app.core.config import settings
from app.core.logging import StructuredLogger

logger = StructuredLogger(__name__)

# 日本語フォント設定
plt.rcParams['font.family'] = ['DejaVu Sans', 'SimHei', 'Microsoft YaHei']
sns.set_style("whitegrid")
sns.set_palette("husl")


class ReportGenerator:
    """歩行分析レポート生成器"""
    
    def __init__(self):
        self.report_template_dir = "app/templates/reports"
        self.output_dir = "reports"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # レポート設定
        self.COLORS = {
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'success': '#F18F01',
            'warning': '#C73E1D',
            'excellent': '#22C55E',
            'good': '#84CC16',
            'fair': '#F59E0B',
            'poor': '#EF4444'
        }
        
    async def generate_pdf_report(
        self, 
        analysis_result: GaitAnalysisResponse,
        patient_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        PDF形式の詳細レポートを生成
        
        Args:
            analysis_result: 分析結果データ
            patient_info: 患者情報（オプション）
            
        Returns:
            str: 生成されたPDFファイルのパス
        """
        logger.info("Starting PDF report generation", 
                   analysis_id=analysis_result.analysis_id)
        
        try:
            # ファイル名生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gait_analysis_report_{analysis_result.analysis_id[:8]}_{timestamp}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            with PdfPages(filepath) as pdf:
                # ページ1: 概要とスコア
                self._create_overview_page(pdf, analysis_result, patient_info)
                
                # ページ2: 時空間パラメータ
                if analysis_result.spatiotemporal_params:
                    self._create_spatiotemporal_page(pdf, analysis_result.spatiotemporal_params)
                
                # ページ3: 対称性分析
                if analysis_result.symmetry_indices:
                    self._create_symmetry_page(pdf, analysis_result.symmetry_indices)
                
                # ページ4: 関節角度分析
                if analysis_result.joint_angles:
                    self._create_joint_angles_page(pdf, analysis_result.joint_angles)
                
                # ページ5: 改善提案
                self._create_recommendations_page(pdf, analysis_result.recommendations)
            
            logger.info("PDF report generated successfully", filepath=filepath)
            return filepath
            
        except Exception as e:
            logger.error("Failed to generate PDF report", error=str(e))
            raise
    
    async def generate_png_summary(
        self, 
        analysis_result: GaitAnalysisResponse,
        size: tuple = (1200, 800)
    ) -> str:
        """
        PNG形式のサマリー画像を生成
        
        Args:
            analysis_result: 分析結果データ
            size: 画像サイズ (width, height)
            
        Returns:
            str: 生成されたPNGファイルのパス
        """
        logger.info("Starting PNG summary generation", 
                   analysis_id=analysis_result.analysis_id)
        
        try:
            # ファイル名生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gait_summary_{analysis_result.analysis_id[:8]}_{timestamp}.png"
            filepath = os.path.join(self.output_dir, filename)
            
            # 図作成
            fig, axes = plt.subplots(2, 3, figsize=(15, 10))
            fig.suptitle('歩行分析サマリー', fontsize=20, fontweight='bold')
            
            # 総合スコア (左上)
            self._plot_overall_score(axes[0, 0], analysis_result.overall_gait_score)
            
            # 対称性スコア (右上)
            if analysis_result.symmetry_indices:
                self._plot_symmetry_radar(axes[0, 1], analysis_result.symmetry_indices)
            
            # 品質指標 (中央上)
            self._plot_quality_metrics(axes[0, 2], analysis_result)
            
            # 歩行パラメータ (左下)
            if analysis_result.spatiotemporal_params:
                self._plot_gait_parameters(axes[1, 0], analysis_result.spatiotemporal_params)
            
            # 関節角度サマリー (中央下)
            if analysis_result.joint_angles:
                self._plot_joint_summary(axes[1, 1], analysis_result.joint_angles)
            
            # 推奨事項 (右下)
            self._plot_recommendations_summary(axes[1, 2], analysis_result.recommendations)
            
            plt.tight_layout()
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()
            
            logger.info("PNG summary generated successfully", filepath=filepath)
            return filepath
            
        except Exception as e:
            logger.error("Failed to generate PNG summary", error=str(e))
            raise
    
    def _create_overview_page(
        self, 
        pdf: PdfPages, 
        analysis_result: GaitAnalysisResponse,
        patient_info: Optional[Dict[str, Any]]
    ):
        """概要ページ作成"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(11, 8))
        
        # ページタイトル
        fig.suptitle('歩行分析レポート - 概要', fontsize=16, fontweight='bold')
        
        # 患者情報とメタデータ
        info_text = f"""
分析ID: {analysis_result.analysis_id}
分析日時: {analysis_result.timestamp.strftime('%Y年%m月%d日 %H:%M')}
処理時間: {analysis_result.processing_time_seconds:.1f}秒
検出された歩行周期: {analysis_result.gait_cycles_detected}個
"""
        if patient_info:
            info_text += f"""
患者ID: {patient_info.get('patient_id', 'N/A')}
身長: {patient_info.get('height_cm', 'N/A')}cm
年齢: {patient_info.get('age', 'N/A')}歳
"""
        
        ax1.text(0.05, 0.95, info_text, transform=ax1.transAxes, 
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
        ax1.set_title('分析情報')
        ax1.axis('off')
        
        # 総合スコア
        self._plot_overall_score(ax2, analysis_result.overall_gait_score)
        
        # 品質指標
        self._plot_quality_metrics(ax3, analysis_result)
        
        # 主要指標サマリー
        if analysis_result.spatiotemporal_params:
            self._plot_key_metrics_summary(ax4, analysis_result.spatiotemporal_params)
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _create_spatiotemporal_page(
        self, 
        pdf: PdfPages, 
        params: SpatiotemporalParameters
    ):
        """時空間パラメータページ作成"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(11, 8))
        fig.suptitle('時空間パラメータ詳細', fontsize=16, fontweight='bold')
        
        # 歩行速度とケイデンス
        metrics = ['歩行速度\n(m/s)', 'ケイデンス\n(歩/分)', 'ストライド長\n(m)', '両脚支持時間\n(ms)']
        values = [
            params.gait_speed_ms,
            params.cadence_steps_per_min,
            params.stride_length_m,
            params.double_support_time_s * 1000
        ]
        
        bars = ax1.bar(metrics, values, color=[self.COLORS['primary'], self.COLORS['secondary'], 
                                              self.COLORS['success'], self.COLORS['warning']])
        ax1.set_title('主要パラメータ')
        ax1.set_ylabel('値')
        
        # 値をバーの上に表示
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'{value:.2f}', ha='center', va='bottom')
        
        # 左右比較
        left_right_metrics = ['左脚歩幅(m)', '右脚歩幅(m)', '左脚立脚時間(s)', '右脚立脚時間(s)']
        left_right_values = [
            params.left_step_length_m,
            params.right_step_length_m,
            params.left_stance_time_s,
            params.right_stance_time_s
        ]
        
        x_pos = np.arange(len(left_right_metrics))
        bars2 = ax2.bar(x_pos, left_right_values, 
                       color=[self.COLORS['primary'] if i % 2 == 0 else self.COLORS['secondary'] 
                             for i in range(len(left_right_values))])
        ax2.set_title('左右比較')
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(left_right_metrics, rotation=45, ha='right')
        ax2.set_ylabel('値')
        
        # 正常値との比較
        normal_ranges = {
            '歩行速度': (1.2, 1.6),
            'ケイデンス': (100, 120),
            'ストライド長': (1.2, 1.6),
            '立脚時間': (0.6, 0.8)
        }
        
        current_values = [
            params.gait_speed_ms,
            params.cadence_steps_per_min,
            params.stride_length_m,
            (params.left_stance_time_s + params.right_stance_time_s) / 2
        ]
        
        # 正常値比較チャート
        y_pos = np.arange(len(normal_ranges))
        for i, (metric, (min_val, max_val)) in enumerate(normal_ranges.items()):
            current = current_values[i]
            
            # 正常範囲を描画
            ax3.barh(i, max_val - min_val, left=min_val, alpha=0.3, 
                    color=self.COLORS['success'], label='正常範囲' if i == 0 else "")
            
            # 現在値を描画
            color = self.COLORS['success'] if min_val <= current <= max_val else self.COLORS['warning']
            ax3.scatter(current, i, color=color, s=100, zorder=3, 
                       label='現在値' if i == 0 else "")
        
        ax3.set_yticks(y_pos)
        ax3.set_yticklabels(list(normal_ranges.keys()))
        ax3.set_title('正常値との比較')
        ax3.set_xlabel('値')
        ax3.legend()
        
        # パラメータテーブル
        table_data = [
            ['パラメータ', '値', '単位', '評価'],
            ['歩行速度', f'{params.gait_speed_ms:.2f}', 'm/s', params.speed_evaluation or 'N/A'],
            ['ケイデンス', f'{params.cadence_steps_per_min}', '歩/分', 'N/A'],
            ['ストライド長', f'{params.stride_length_m:.2f}', 'm', 'N/A'],
            ['ストライド時間', f'{params.stride_time_s:.2f}', 's', 'N/A'],
        ]
        
        ax4.axis('tight')
        ax4.axis('off')
        table = ax4.table(cellText=table_data[1:], colLabels=table_data[0],
                         cellLoc='center', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.2, 1.5)
        ax4.set_title('詳細パラメータ')
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _create_symmetry_page(
        self, 
        pdf: PdfPages, 
        symmetry: SymmetryIndices
    ):
        """対称性分析ページ作成"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(11, 8))
        fig.suptitle('歩行対称性分析', fontsize=16, fontweight='bold')
        
        # 対称性レーダーチャート
        self._plot_symmetry_radar(ax1, symmetry)
        
        # 対称性スコア比較
        symmetry_metrics = [
            '歩幅対称性', '立脚時間対称性', '遊脚時間対称性',
            '股関節対称性', '膝関節対称性', '足関節対称性'
        ]
        symmetry_values = [
            symmetry.step_length_symmetry_percent,
            symmetry.stance_time_symmetry_percent,
            symmetry.swing_time_symmetry_percent,
            symmetry.hip_flexion_symmetry_percent,
            symmetry.knee_flexion_symmetry_percent,
            symmetry.ankle_dorsiflexion_symmetry_percent
        ]
        
        # 対称性基準（非対称性%が低いほど良い）
        colors = [self._get_symmetry_color(val) for val in symmetry_values]
        bars = ax2.barh(symmetry_metrics, symmetry_values, color=colors)
        ax2.set_title('対称性指標 (非対称性%)')
        ax2.set_xlabel('非対称性 (%)')
        
        # 基準線を追加
        ax2.axvline(x=5, color='green', linestyle='--', alpha=0.7, label='優秀 (<5%)')
        ax2.axvline(x=10, color='orange', linestyle='--', alpha=0.7, label='要注意 (>10%)')
        ax2.legend()
        
        # 総合対称性スコア
        score_data = [symmetry.overall_symmetry_score, 100 - symmetry.overall_symmetry_score]
        colors_score = [self._get_score_color(symmetry.overall_symmetry_score), 'lightgray']
        ax3.pie(score_data, labels=['対称性スコア', ''], colors=colors_score, 
                autopct='%1.1f%%', startangle=90)
        ax3.set_title(f'総合対称性スコア\n{symmetry.overall_symmetry_score:.1f}点')
        
        # 対称性評価テーブル
        evaluation_data = [
            ['指標', '非対称性%', '評価'],
            ['歩幅', f'{symmetry.step_length_symmetry_percent:.1f}', 
             self._get_symmetry_evaluation(symmetry.step_length_symmetry_percent)],
            ['立脚時間', f'{symmetry.stance_time_symmetry_percent:.1f}', 
             self._get_symmetry_evaluation(symmetry.stance_time_symmetry_percent)],
            ['遊脚時間', f'{symmetry.swing_time_symmetry_percent:.1f}', 
             self._get_symmetry_evaluation(symmetry.swing_time_symmetry_percent)],
        ]
        
        ax4.axis('tight')
        ax4.axis('off')
        table2 = ax4.table(cellText=evaluation_data[1:], colLabels=evaluation_data[0],
                          cellLoc='center', loc='center')
        table2.auto_set_font_size(False)
        table2.set_fontsize(9)
        table2.scale(1.2, 1.5)
        ax4.set_title('対称性評価')
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _create_joint_angles_page(
        self, 
        pdf: PdfPages, 
        joint_angles: JointAngles
    ):
        """関節角度分析ページ作成"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(11, 8))
        fig.suptitle('関節角度分析', fontsize=16, fontweight='bold')
        
        if joint_angles.frame_timestamps and len(joint_angles.frame_timestamps) > 0:
            timestamps = joint_angles.frame_timestamps
            
            # 股関節角度
            if joint_angles.hip_flexion_deg:
                ax1.plot(timestamps, joint_angles.hip_flexion_deg, 
                        color=self.COLORS['primary'], linewidth=2)
                ax1.set_title('股関節屈曲角度')
                ax1.set_xlabel('時間 (秒)')
                ax1.set_ylabel('角度 (度)')
                ax1.grid(True, alpha=0.3)
            
            # 膝関節角度
            if joint_angles.knee_flexion_deg:
                ax2.plot(timestamps, joint_angles.knee_flexion_deg, 
                        color=self.COLORS['secondary'], linewidth=2)
                ax2.set_title('膝関節屈曲角度')
                ax2.set_xlabel('時間 (秒)')
                ax2.set_ylabel('角度 (度)')
                ax2.grid(True, alpha=0.3)
            
            # 足関節角度
            if joint_angles.ankle_dorsiflexion_deg:
                ax3.plot(timestamps, joint_angles.ankle_dorsiflexion_deg, 
                        color=self.COLORS['success'], linewidth=2)
                ax3.set_title('足関節背屈角度')
                ax3.set_xlabel('時間 (秒)')
                ax3.set_ylabel('角度 (度)')
                ax3.grid(True, alpha=0.3)
            
            # 関節角度統計
            self._plot_joint_statistics(ax4, joint_angles)
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _create_recommendations_page(
        self, 
        pdf: PdfPages, 
        recommendations: List[str]
    ):
        """改善提案ページ作成"""
        fig, ax = plt.subplots(1, 1, figsize=(11, 8))
        fig.suptitle('改善提案', fontsize=16, fontweight='bold')
        
        if recommendations:
            # 改善提案をテキストとして表示
            recommendations_text = ""
            for i, rec in enumerate(recommendations, 1):
                recommendations_text += f"{i}. {rec}\n\n"
            
            ax.text(0.05, 0.95, recommendations_text, transform=ax.transAxes,
                   fontsize=12, verticalalignment='top', wrap=True,
                   bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.7))
        else:
            ax.text(0.5, 0.5, "改善提案はありません", transform=ax.transAxes,
                   fontsize=14, ha='center', va='center')
        
        ax.axis('off')
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _plot_overall_score(self, ax, score: float):
        """総合スコア円グラフ"""
        score_data = [score, 100 - score]
        colors = [self._get_score_color(score), 'lightgray']
        wedges, texts, autotexts = ax.pie(score_data, labels=['', ''], colors=colors, 
                                         autopct='', startangle=90)
        
        # 中央にスコアを表示
        ax.text(0, 0, f'{score:.1f}', ha='center', va='center', 
               fontsize=24, fontweight='bold')
        ax.text(0, -0.3, '総合スコア', ha='center', va='center', fontsize=12)
        ax.set_title('総合歩行スコア')
    
    def _plot_symmetry_radar(self, ax, symmetry: SymmetryIndices):
        """対称性レーダーチャート"""
        categories = ['歩幅', '立脚時間', '遊脚時間', '股関節', '膝関節', '足関節']
        values = [
            100 - symmetry.step_length_symmetry_percent,  # 対称性に変換
            100 - symmetry.stance_time_symmetry_percent,
            100 - symmetry.swing_time_symmetry_percent,
            100 - symmetry.hip_flexion_symmetry_percent,
            100 - symmetry.knee_flexion_symmetry_percent,
            100 - symmetry.ankle_dorsiflexion_symmetry_percent
        ]
        
        # レーダーチャートの準備
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values += values[:1]  # 円を閉じる
        angles += angles[:1]
        
        ax.plot(angles, values, 'o-', linewidth=2, color=self.COLORS['primary'])
        ax.fill(angles, values, alpha=0.25, color=self.COLORS['primary'])
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 100)
        ax.set_title('対称性レーダー')
        ax.grid(True)
    
    def _plot_quality_metrics(self, ax, analysis_result: GaitAnalysisResponse):
        """品質指標"""
        metrics = ['動画品質', 'ポーズ検出', '歩行周期']
        values = [
            analysis_result.video_quality_score,
            analysis_result.pose_detection_confidence * 100,
            min(100, analysis_result.gait_cycles_detected * 25)  # 4周期で100%
        ]
        
        bars = ax.bar(metrics, values, color=[self.COLORS['primary'], 
                                             self.COLORS['secondary'], 
                                             self.COLORS['success']])
        ax.set_title('分析品質指標')
        ax.set_ylabel('品質スコア (%)')
        ax.set_ylim(0, 100)
        
        # 値をバーの上に表示
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                   f'{value:.1f}%', ha='center', va='bottom')
    
    def _plot_gait_parameters(self, ax, params: SpatiotemporalParameters):
        """歩行パラメータ表示"""
        param_names = ['速度', 'ケイデンス', 'ストライド長']
        param_values = [params.gait_speed_ms, params.cadence_steps_per_min/100, params.stride_length_m]
        
        bars = ax.bar(param_names, param_values, 
                     color=[self.COLORS['primary'], self.COLORS['secondary'], self.COLORS['success']])
        ax.set_title('主要歩行パラメータ')
        ax.set_ylabel('正規化値')
    
    def _plot_joint_summary(self, ax, joint_angles: JointAngles):
        """関節角度サマリー"""
        if joint_angles.hip_flexion_deg and joint_angles.knee_flexion_deg:
            joint_names = ['股関節', '膝関節', '足関節']
            max_angles = [
                max(joint_angles.hip_flexion_deg) if joint_angles.hip_flexion_deg else 0,
                max(joint_angles.knee_flexion_deg) if joint_angles.knee_flexion_deg else 0,
                max(joint_angles.ankle_dorsiflexion_deg) if joint_angles.ankle_dorsiflexion_deg else 0
            ]
            
            bars = ax.bar(joint_names, max_angles, 
                         color=[self.COLORS['primary'], self.COLORS['secondary'], self.COLORS['success']])
            ax.set_title('最大関節角度')
            ax.set_ylabel('角度 (度)')
    
    def _plot_recommendations_summary(self, ax, recommendations: List[str]):
        """推奨事項サマリー"""
        if recommendations:
            summary_text = f"改善提案数: {len(recommendations)}\n\n"
            for i, rec in enumerate(recommendations[:3], 1):  # 最初の3つ
                summary_text += f"{i}. {rec[:30]}...\n"
        else:
            summary_text = "改善提案はありません"
        
        ax.text(0.05, 0.95, summary_text, transform=ax.transAxes,
               fontsize=8, verticalalignment='top', wrap=True)
        ax.set_title('改善提案')
        ax.axis('off')
    
    def _plot_key_metrics_summary(self, ax, params: SpatiotemporalParameters):
        """主要指標サマリー"""
        summary_text = f"""
歩行速度: {params.gait_speed_ms:.2f} m/s
ケイデンス: {params.cadence_steps_per_min} 歩/分
ストライド長: {params.stride_length_m:.2f} m
評価: {params.speed_evaluation or 'N/A'}
"""
        ax.text(0.05, 0.95, summary_text, transform=ax.transAxes,
               fontsize=12, verticalalignment='top',
               bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.7))
        ax.set_title('主要指標')
        ax.axis('off')
    
    def _plot_joint_statistics(self, ax, joint_angles: JointAngles):
        """関節角度統計"""
        stats_data = []
        
        if joint_angles.hip_flexion_deg:
            hip_max = max(joint_angles.hip_flexion_deg)
            hip_min = min(joint_angles.hip_flexion_deg)
            hip_avg = sum(joint_angles.hip_flexion_deg) / len(joint_angles.hip_flexion_deg)
            stats_data.append(['股関節', f'{hip_max:.1f}', f'{hip_min:.1f}', f'{hip_avg:.1f}'])
        
        if joint_angles.knee_flexion_deg:
            knee_max = max(joint_angles.knee_flexion_deg)
            knee_min = min(joint_angles.knee_flexion_deg)
            knee_avg = sum(joint_angles.knee_flexion_deg) / len(joint_angles.knee_flexion_deg)
            stats_data.append(['膝関節', f'{knee_max:.1f}', f'{knee_min:.1f}', f'{knee_avg:.1f}'])
        
        if joint_angles.ankle_dorsiflexion_deg:
            ankle_max = max(joint_angles.ankle_dorsiflexion_deg)
            ankle_min = min(joint_angles.ankle_dorsiflexion_deg)
            ankle_avg = sum(joint_angles.ankle_dorsiflexion_deg) / len(joint_angles.ankle_dorsiflexion_deg)
            stats_data.append(['足関節', f'{ankle_max:.1f}', f'{ankle_min:.1f}', f'{ankle_avg:.1f}'])
        
        if stats_data:
            ax.axis('tight')
            ax.axis('off')
            table = ax.table(cellText=stats_data, 
                           colLabels=['関節', '最大角度(°)', '最小角度(°)', '平均角度(°)'],
                           cellLoc='center', loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1.2, 1.5)
            ax.set_title('関節角度統計')
    
    def _get_score_color(self, score: float) -> str:
        """スコアに基づく色を取得"""
        if score >= 90:
            return self.COLORS['excellent']
        elif score >= 80:
            return self.COLORS['good']
        elif score >= 70:
            return self.COLORS['fair']
        else:
            return self.COLORS['poor']
    
    def _get_symmetry_color(self, asymmetry_percent: float) -> str:
        """非対称性パーセンテージに基づく色を取得"""
        if asymmetry_percent <= 5:
            return self.COLORS['excellent']
        elif asymmetry_percent <= 10:
            return self.COLORS['good']
        elif asymmetry_percent <= 15:
            return self.COLORS['fair']
        else:
            return self.COLORS['poor']
    
    def _get_symmetry_evaluation(self, asymmetry_percent: float) -> str:
        """非対称性評価を取得"""
        if asymmetry_percent <= 5:
            return '優秀'
        elif asymmetry_percent <= 10:
            return '良好'
        elif asymmetry_percent <= 15:
            return '普通'
        else:
            return '要改善'
    
    async def generate_base64_image(
        self, 
        analysis_result: GaitAnalysisResponse
    ) -> str:
        """
        Base64エンコードされた画像を生成（Web表示用）
        
        Returns:
            str: Base64エンコードされた画像データ
        """
        try:
            # PNG画像を生成
            png_path = await self.generate_png_summary(analysis_result)
            
            # Base64エンコード
            with open(png_path, 'rb') as img_file:
                img_data = img_file.read()
                base64_data = base64.b64encode(img_data).decode('utf-8')
            
            # 一時ファイルを削除
            os.remove(png_path)
            
            return f"data:image/png;base64,{base64_data}"
            
        except Exception as e:
            logger.error("Failed to generate base64 image", error=str(e))
            raise