"""
拡張動画処理器
Enhanced Video Processor for slow-motion skeleton overlay and time-series graphs
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
import mediapipe as mp
from typing import List, Dict, Any, Optional, Tuple
import os
import tempfile
import time
from pathlib import Path

from app.models.gait_models import (
    JointAngles, DetailedSpatiotemporalParameters, 
    CompensationAlert, BalanceMetrics, EnhancedOutputData
)
from app.core.advanced_logger import get_logger

logger = get_logger(__name__)


class EnhancedVideoProcessor:
    """拡張動画処理クラス"""
    
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # 色設定
        self.colors = {
            'normal': (0, 255, 0),      # 緑
            'warning': (0, 165, 255),   # オレンジ
            'alert': (0, 0, 255),       # 赤
            'skeleton': (255, 255, 255), # 白
            'background': (0, 0, 0)     # 黒
        }
        
        # 出力設定
        self.output_settings = {
            'slow_motion_factor': 0.5,  # スローモーション倍率
            'target_fps': 30,
            'video_quality': 95,
            'graph_dpi': 300,
            'pdf_quality': 'high'
        }
    
    def create_enhanced_output(
        self,
        video_path: str,
        landmarks_data: List[Dict],
        joint_angles: JointAngles,
        spatiotemporal_params: DetailedSpatiotemporalParameters,
        balance_metrics: BalanceMetrics,
        compensation_alerts: List[CompensationAlert],
        output_dir: str = None
    ) -> EnhancedOutputData:
        """
        拡張出力データ作成メイン処理
        
        Args:
            video_path: 元動画パス
            landmarks_data: ランドマークデータ
            joint_angles: 関節角度データ
            spatiotemporal_params: 時空間パラメータ
            balance_metrics: バランス指標
            compensation_alerts: 代償動作アラート
            output_dir: 出力ディレクトリ
            
        Returns:
            EnhancedOutputData: 拡張出力データ
        """
        start_time = time.time()
        
        if not output_dir:
            output_dir = tempfile.mkdtemp()
        
        logger.info("Starting enhanced output creation", output_dir=output_dir)
        
        # 1. 正規化時間波形データ生成
        normalized_time_series = self._generate_normalized_time_series(
            joint_angles, spatiotemporal_params, balance_metrics
        )
        
        # 2. スローモーション骨格動画生成
        slow_motion_video_path = self._create_slow_motion_skeleton_video(
            video_path, landmarks_data, compensation_alerts, output_dir
        )
        
        # 3. カラー判定PDFレポート生成
        pdf_report_path = self._create_color_coded_pdf_report(
            joint_angles, spatiotemporal_params, balance_metrics,
            compensation_alerts, normalized_time_series, output_dir
        )
        
        total_processing_time = time.time() - start_time
        
        enhanced_output = EnhancedOutputData(
            normalized_time_series=normalized_time_series,
            slow_motion_skeleton_video_path=slow_motion_video_path,
            color_coded_pdf_report_path=pdf_report_path,
            total_processing_time_seconds=total_processing_time,
            target_processing_time_seconds=30
        )
        
        logger.info("Enhanced output creation completed",
                   processing_time=total_processing_time,
                   video_path=slow_motion_video_path,
                   pdf_path=pdf_report_path)
        
        return enhanced_output
    
    def _generate_normalized_time_series(
        self,
        joint_angles: JointAngles,
        spatiotemporal_params: DetailedSpatiotemporalParameters,
        balance_metrics: BalanceMetrics
    ) -> Dict[str, List[float]]:
        """正規化時間波形データ生成（1歩行周期で正規化）"""
        
        # 歩行周期長（フレーム数）の推定
        if joint_angles.frame_timestamps:
            total_duration = max(joint_angles.frame_timestamps)
            # 1歩行周期 ≈ 60/ケイデンス 秒
            cycle_duration = 60.0 / spatiotemporal_params.cadence_steps_per_min if spatiotemporal_params.cadence_steps_per_min > 0 else 1.0
            frames_per_cycle = int(cycle_duration * 30)  # 30fps想定
        else:
            frames_per_cycle = 30  # デフォルト
        
        normalized_series = {}
        
        # 関節角度データの正規化
        if len(joint_angles.hip_flexion_deg) >= frames_per_cycle:
            # 1歩行周期分のデータを抽出
            cycle_data = {
                'hip_flexion': joint_angles.hip_flexion_deg[:frames_per_cycle],
                'hip_extension': joint_angles.hip_extension_deg[:frames_per_cycle] if joint_angles.hip_extension_deg else [0] * frames_per_cycle,
                'knee_flexion': joint_angles.knee_flexion_deg[:frames_per_cycle],
                'ankle_dorsiflexion': joint_angles.ankle_dorsiflexion_deg[:frames_per_cycle],
                'ankle_plantarflexion': joint_angles.ankle_plantarflexion_deg[:frames_per_cycle] if joint_angles.ankle_plantarflexion_deg else [0] * frames_per_cycle,
                'pelvic_drop': joint_angles.pelvic_drop_deg[:frames_per_cycle],
            }
            
            # 0-100%に正規化
            for param_name, values in cycle_data.items():
                if values:
                    normalized_percent = np.linspace(0, 100, len(values)).tolist()
                    normalized_series[f'{param_name}_percent'] = normalized_percent
                    normalized_series[f'{param_name}_values'] = values
        
        # 重心移動データの正規化
        if balance_metrics.com_lateral_displacement_cm:
            com_cycle_data = balance_metrics.com_lateral_displacement_cm[:frames_per_cycle]
            if com_cycle_data:
                normalized_series['com_lateral_percent'] = np.linspace(0, 100, len(com_cycle_data)).tolist()
                normalized_series['com_lateral_values'] = com_cycle_data
        
        if balance_metrics.com_vertical_displacement_cm:
            com_vertical_data = balance_metrics.com_vertical_displacement_cm[:frames_per_cycle]
            if com_vertical_data:
                normalized_series['com_vertical_percent'] = np.linspace(0, 100, len(com_vertical_data)).tolist()
                normalized_series['com_vertical_values'] = com_vertical_data
        
        return normalized_series
    
    def _create_slow_motion_skeleton_video(
        self,
        video_path: str,
        landmarks_data: List[Dict],
        compensation_alerts: List[CompensationAlert],
        output_dir: str
    ) -> str:
        """スローモーション骨格動画生成"""
        
        output_path = os.path.join(output_dir, "slow_motion_skeleton.mp4")
        
        # 元動画読み込み
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error("Cannot open video file", path=video_path)
            return ""
        
        # 動画情報取得
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 出力動画設定
        output_fps = fps * self.output_settings['slow_motion_factor']
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, output_fps, (width, height))
        
        # アラートのフレーム範囲マップ
        alert_frames = self._create_alert_frame_map(compensation_alerts)
        
        frame_idx = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # 骨格描画
            if frame_idx < len(landmarks_data) and landmarks_data[frame_idx]:
                frame_with_skeleton = self._draw_enhanced_skeleton(
                    frame, landmarks_data[frame_idx]['landmarks'], 
                    alert_frames.get(frame_idx, [])
                )
            else:
                frame_with_skeleton = frame
            
            # フレーム情報オーバーレイ
            frame_with_info = self._add_frame_info_overlay(
                frame_with_skeleton, frame_idx, alert_frames.get(frame_idx, [])
            )
            
            out.write(frame_with_info)
            frame_idx += 1
        
        cap.release()
        out.release()
        
        logger.info("Slow motion skeleton video created", path=output_path)
        return output_path
    
    def _create_alert_frame_map(
        self, 
        compensation_alerts: List[CompensationAlert]
    ) -> Dict[int, List[CompensationAlert]]:
        """アラートのフレーム範囲マップ作成"""
        alert_map = {}
        
        for alert in compensation_alerts:
            start_frame, end_frame = alert.frame_range
            for frame_idx in range(start_frame, end_frame + 1):
                if frame_idx not in alert_map:
                    alert_map[frame_idx] = []
                alert_map[frame_idx].append(alert)
        
        return alert_map
    
    def _draw_enhanced_skeleton(
        self,
        frame: np.ndarray,
        landmarks: List[Dict],
        alerts: List[CompensationAlert]
    ) -> np.ndarray:
        """拡張骨格描画"""
        
        # MediaPipe結果形式に変換
        mp_landmarks = self._convert_to_mp_landmarks(landmarks)
        
        if mp_landmarks:
            # アラートに基づく色選択
            if any(alert.severity in ['high', 'critical'] for alert in alerts):
                color = self.colors['alert']
            elif any(alert.severity == 'medium' for alert in alerts):
                color = self.colors['warning']
            else:
                color = self.colors['normal']
            
            # 骨格描画
            self.mp_drawing.draw_landmarks(
                frame,
                mp_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing.DrawingSpec(
                    color=color, thickness=2, circle_radius=3
                ),
                connection_drawing_spec=self.mp_drawing.DrawingSpec(
                    color=color, thickness=2
                )
            )
        
        return frame
    
    def _convert_to_mp_landmarks(self, landmarks: List[Dict]):
        """MediaPipeランドマーク形式に変換"""
        try:
            # 簡易実装（実際はより詳細な変換が必要）
            class MockLandmark:
                def __init__(self, x, y, z, visibility):
                    self.x = x
                    self.y = y
                    self.z = z
                    self.visibility = visibility
            
            class MockLandmarkList:
                def __init__(self, landmarks):
                    self.landmark = [
                        MockLandmark(lm['x'], lm['y'], lm['z'], lm['visibility'])
                        for lm in landmarks
                    ]
            
            return MockLandmarkList(landmarks)
        
        except Exception:
            return None
    
    def _add_frame_info_overlay(
        self,
        frame: np.ndarray,
        frame_idx: int,
        alerts: List[CompensationAlert]
    ) -> np.ndarray:
        """フレーム情報オーバーレイ"""
        
        # フレーム番号表示
        cv2.putText(frame, f"Frame: {frame_idx}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # アラート表示
        if alerts:
            y_offset = 60
            for alert in alerts:
                alert_text = f"⚠ {alert.alert_type}: {alert.measured_value:.1f}"
                color = self.colors['alert'] if alert.severity in ['high', 'critical'] else self.colors['warning']
                cv2.putText(frame, alert_text, (10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                y_offset += 25
        
        return frame
    
    def _create_color_coded_pdf_report(
        self,
        joint_angles: JointAngles,
        spatiotemporal_params: DetailedSpatiotemporalParameters,
        balance_metrics: BalanceMetrics,
        compensation_alerts: List[CompensationAlert],
        normalized_time_series: Dict[str, List[float]],
        output_dir: str
    ) -> str:
        """カラー判定PDFレポート生成"""
        
        output_path = os.path.join(output_dir, "gait_analysis_color_report.pdf")
        
        # 日本語フォント設定
        plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'Hiragino Sans']
        
        with PdfPages(output_path) as pdf:
            # ページ1: 概要とアラート
            self._create_summary_page(
                pdf, spatiotemporal_params, balance_metrics, compensation_alerts
            )
            
            # ページ2: 正規化時間波形グラフ
            self._create_time_series_page(pdf, normalized_time_series)
            
            # ページ3: 関節角度詳細
            self._create_joint_angles_page(pdf, joint_angles)
            
            # ページ4: バランス・重心分析
            self._create_balance_analysis_page(pdf, balance_metrics)
            
            # ページ5: 代償動作詳細
            if compensation_alerts:
                self._create_compensation_details_page(pdf, compensation_alerts)
        
        logger.info("Color-coded PDF report created", path=output_path)
        return output_path
    
    def _create_summary_page(
        self,
        pdf: PdfPages,
        spatiotemporal_params: DetailedSpatiotemporalParameters,
        balance_metrics: BalanceMetrics,
        compensation_alerts: List[CompensationAlert]
    ):
        """概要ページ作成"""
        fig, ax = plt.subplots(2, 2, figsize=(11, 8))
        fig.suptitle('Gait Analysis Summary Report', fontsize=16, fontweight='bold')
        
        # 時空間パラメータサマリー
        ax[0, 0].axis('off')
        ax[0, 0].set_title('Spatiotemporal Parameters', fontweight='bold')
        
        params_text = [
            f"Gait Speed: {spatiotemporal_params.gait_speed_ms:.2f} m/s",
            f"Cadence: {spatiotemporal_params.cadence_steps_per_min} steps/min",
            f"Stride Length: {spatiotemporal_params.stride_length_cm:.1f} cm",
            f"Stance Time: {spatiotemporal_params.stance_time_percent:.1f}%",
            f"Swing Time: {spatiotemporal_params.swing_time_percent:.1f}%"
        ]
        
        for i, text in enumerate(params_text):
            color = self._get_parameter_color(text)
            ax[0, 0].text(0.1, 0.8 - i*0.15, text, fontsize=12, color=color)
        
        # バランス指標
        ax[0, 1].axis('off')
        ax[0, 1].set_title('Balance Metrics', fontweight='bold')
        
        balance_text = [
            f"Lateral Displacement: {balance_metrics.lateral_displacement_max_cm:.1f} cm",
            f"Vertical Displacement: {balance_metrics.vertical_displacement_max_cm:.1f} cm",
            f"Balance Stability: {balance_metrics.balance_stability_score:.1f}/100"
        ]
        
        for i, text in enumerate(balance_text):
            color = self._get_balance_color(text, balance_metrics)
            ax[0, 1].text(0.1, 0.8 - i*0.2, text, fontsize=12, color=color)
        
        # アラート一覧
        ax[1, 0].axis('off')
        ax[1, 0].set_title('Compensation Alerts', fontweight='bold')
        
        if compensation_alerts:
            for i, alert in enumerate(compensation_alerts[:5]):  # 最大5個
                severity_color = 'red' if alert.severity in ['high', 'critical'] else 'orange'
                ax[1, 0].text(0.1, 0.8 - i*0.15, f"⚠ {alert.message}", 
                             fontsize=10, color=severity_color)
        else:
            ax[1, 0].text(0.1, 0.5, "No significant compensation detected", 
                         fontsize=12, color='green')
        
        # 総合評価
        ax[1, 1].axis('off')
        ax[1, 1].set_title('Overall Assessment', fontweight='bold')
        overall_score = self._calculate_overall_score(
            spatiotemporal_params, balance_metrics, compensation_alerts
        )
        score_color = 'green' if overall_score >= 80 else 'orange' if overall_score >= 60 else 'red'
        ax[1, 1].text(0.1, 0.6, f"Overall Score: {overall_score:.0f}/100", 
                     fontsize=14, fontweight='bold', color=score_color)
        
        plt.tight_layout()
        pdf.savefig(fig, dpi=self.output_settings['graph_dpi'])
        plt.close(fig)
    
    def _create_time_series_page(
        self, 
        pdf: PdfPages, 
        normalized_time_series: Dict[str, List[float]]
    ):
        """正規化時間波形ページ作成"""
        fig, axes = plt.subplots(3, 2, figsize=(11, 8))
        fig.suptitle('Normalized Time Series (% Gait Cycle)', fontsize=16, fontweight='bold')
        
        # 関節角度グラフ
        angles_to_plot = [
            ('hip_flexion', 'Hip Flexion', axes[0, 0]),
            ('knee_flexion', 'Knee Flexion', axes[0, 1]),
            ('ankle_dorsiflexion', 'Ankle Dorsiflexion', axes[1, 0]),
            ('ankle_plantarflexion', 'Ankle Plantarflexion', axes[1, 1]),
            ('com_lateral', 'COM Lateral Displacement', axes[2, 0]),
            ('com_vertical', 'COM Vertical Displacement', axes[2, 1])
        ]
        
        for angle_key, title, ax in angles_to_plot:
            percent_key = f'{angle_key}_percent'
            values_key = f'{angle_key}_values'
            
            if percent_key in normalized_time_series and values_key in normalized_time_series:
                x_data = normalized_time_series[percent_key]
                y_data = normalized_time_series[values_key]
                
                ax.plot(x_data, y_data, 'b-', linewidth=2)
                ax.set_title(title, fontweight='bold')
                ax.set_xlabel('% Gait Cycle')
                ax.set_ylabel('Degrees' if 'flexion' in angle_key else 'cm')
                ax.grid(True, alpha=0.3)
                ax.set_xlim(0, 100)
            else:
                ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
                ax.set_title(title, fontweight='bold')
        
        plt.tight_layout()
        pdf.savefig(fig, dpi=self.output_settings['graph_dpi'])
        plt.close(fig)
    
    def _create_joint_angles_page(self, pdf: PdfPages, joint_angles: JointAngles):
        """関節角度詳細ページ作成"""
        fig, axes = plt.subplots(2, 2, figsize=(11, 8))
        fig.suptitle('Joint Angles Analysis', fontsize=16, fontweight='bold')
        
        # 股関節ROM
        axes[0, 0].axis('off')
        axes[0, 0].set_title('Hip Joint ROM', fontweight='bold')
        axes[0, 0].text(0.1, 0.7, f"Hip ROM: {joint_angles.hip_rom_deg:.1f}°", 
                       fontsize=14, color=self._get_rom_color(joint_angles.hip_rom_deg, 'hip'))
        axes[0, 0].text(0.1, 0.5, f"Normal Range: 20-40°", fontsize=12, color='gray')
        
        # 膝関節詳細
        axes[0, 1].axis('off')
        axes[0, 1].set_title('Knee Joint Analysis', fontweight='bold')
        axes[0, 1].text(0.1, 0.7, f"Max Flexion: {joint_angles.knee_max_flexion_deg:.1f}°", 
                       fontsize=14, color=self._get_rom_color(joint_angles.knee_max_flexion_deg, 'knee'))
        axes[0, 1].text(0.1, 0.5, f"Heel Contact: {joint_angles.knee_heel_contact_deg:.1f}°", 
                       fontsize=12)
        
        # 足関節詳細
        axes[1, 0].axis('off')
        axes[1, 0].set_title('Ankle Joint Analysis', fontweight='bold')
        axes[1, 0].text(0.1, 0.7, f"Toe-off Angle: {joint_angles.ankle_toe_off_deg:.1f}°", 
                       fontsize=14)
        
        # 骨盤・体幹
        axes[1, 1].axis('off')
        axes[1, 1].set_title('Pelvic & Trunk Analysis', fontweight='bold')
        if joint_angles.pelvic_drop_deg:
            max_pelvic_drop = max([abs(x) for x in joint_angles.pelvic_drop_deg])
            axes[1, 1].text(0.1, 0.7, f"Max Pelvic Drop: {max_pelvic_drop:.1f}°", 
                           fontsize=14, color=self._get_pelvic_color(max_pelvic_drop))
        
        plt.tight_layout()
        pdf.savefig(fig, dpi=self.output_settings['graph_dpi'])
        plt.close(fig)
    
    def _create_balance_analysis_page(self, pdf: PdfPages, balance_metrics: BalanceMetrics):
        """バランス分析ページ作成"""
        fig, axes = plt.subplots(2, 2, figsize=(11, 8))
        fig.suptitle('Balance & COM Analysis', fontsize=16, fontweight='bold')
        
        # 重心投影線2Dマップ
        if balance_metrics.com_projection_x and balance_metrics.com_projection_y:
            axes[0, 0].scatter(balance_metrics.com_projection_x, 
                             balance_metrics.com_projection_y, 
                             alpha=0.6, s=20)
            axes[0, 0].set_title('COM Trajectory (2D Map)', fontweight='bold')
            axes[0, 0].set_xlabel('Lateral (cm)')
            axes[0, 0].set_ylabel('Anterior-Posterior (cm)')
            axes[0, 0].grid(True, alpha=0.3)
        
        # 左右移動パターン
        if balance_metrics.com_lateral_displacement_cm:
            axes[0, 1].plot(balance_metrics.com_lateral_displacement_cm, 'b-', linewidth=2)
            axes[0, 1].set_title('Lateral COM Displacement', fontweight='bold')
            axes[0, 1].set_ylabel('Displacement (cm)')
            axes[0, 1].grid(True, alpha=0.3)
        
        # 上下移動パターン
        if balance_metrics.com_vertical_displacement_cm:
            axes[1, 0].plot(balance_metrics.com_vertical_displacement_cm, 'g-', linewidth=2)
            axes[1, 0].set_title('Vertical COM Displacement', fontweight='bold')
            axes[1, 0].set_ylabel('Displacement (cm)')
            axes[1, 0].grid(True, alpha=0.3)
        
        # バランス安定性スコア
        axes[1, 1].axis('off')
        axes[1, 1].set_title('Balance Stability', fontweight='bold')
        score_color = 'green' if balance_metrics.balance_stability_score >= 80 else 'orange' if balance_metrics.balance_stability_score >= 60 else 'red'
        axes[1, 1].text(0.1, 0.6, f"Stability Score: {balance_metrics.balance_stability_score:.1f}/100", 
                       fontsize=16, fontweight='bold', color=score_color)
        
        plt.tight_layout()
        pdf.savefig(fig, dpi=self.output_settings['graph_dpi'])
        plt.close(fig)
    
    def _create_compensation_details_page(
        self, 
        pdf: PdfPages, 
        compensation_alerts: List[CompensationAlert]
    ):
        """代償動作詳細ページ作成"""
        fig, ax = plt.subplots(1, 1, figsize=(11, 8))
        fig.suptitle('Compensation Movement Details', fontsize=16, fontweight='bold')
        
        ax.axis('off')
        
        y_pos = 0.9
        for alert in compensation_alerts:
            severity_color = 'red' if alert.severity in ['high', 'critical'] else 'orange'
            
            ax.text(0.05, y_pos, f"⚠ {alert.alert_type.upper()}", 
                   fontsize=14, fontweight='bold', color=severity_color)
            ax.text(0.1, y_pos - 0.03, alert.message, fontsize=12)
            ax.text(0.1, y_pos - 0.06, f"Measured: {alert.measured_value:.1f} | Threshold: {alert.threshold_value:.1f}", 
                   fontsize=10, color='gray')
            ax.text(0.1, y_pos - 0.09, f"Severity: {alert.severity.upper()}", 
                   fontsize=10, color=severity_color)
            
            y_pos -= 0.15
            
            if y_pos < 0.1:
                break
        
        plt.tight_layout()
        pdf.savefig(fig, dpi=self.output_settings['graph_dpi'])
        plt.close(fig)
    
    def _get_parameter_color(self, text: str) -> str:
        """パラメータテキストに基づく色判定"""
        # 簡易実装：実際はより詳細な判定が必要
        if "Gait Speed" in text:
            value = float(text.split(":")[1].split()[0])
            return 'green' if 1.2 <= value <= 1.4 else 'orange' if 1.0 <= value < 1.2 or 1.4 < value <= 1.6 else 'red'
        return 'black'
    
    def _get_balance_color(self, text: str, balance_metrics: BalanceMetrics) -> str:
        """バランス指標に基づく色判定"""
        if "Lateral Displacement" in text:
            return 'green' if balance_metrics.lateral_displacement_max_cm < 3 else 'orange' if balance_metrics.lateral_displacement_max_cm < 5 else 'red'
        elif "Balance Stability" in text:
            return 'green' if balance_metrics.balance_stability_score >= 80 else 'orange' if balance_metrics.balance_stability_score >= 60 else 'red'
        return 'black'
    
    def _get_rom_color(self, value: float, joint: str) -> str:
        """関節可動域に基づく色判定"""
        if joint == 'hip':
            return 'green' if 20 <= value <= 40 else 'orange' if 15 <= value < 20 or 40 < value <= 50 else 'red'
        elif joint == 'knee':
            return 'green' if 40 <= value <= 70 else 'orange' if 30 <= value < 40 or 70 < value <= 80 else 'red'
        return 'black'
    
    def _get_pelvic_color(self, value: float) -> str:
        """骨盤傾斜に基づく色判定"""
        return 'green' if value <= 3 else 'orange' if value <= 5 else 'red'
    
    def _calculate_overall_score(
        self,
        spatiotemporal_params: DetailedSpatiotemporalParameters,
        balance_metrics: BalanceMetrics,
        compensation_alerts: List[CompensationAlert]
    ) -> float:
        """総合スコア計算"""
        # 簡易実装
        speed_score = 100 if 1.2 <= spatiotemporal_params.gait_speed_ms <= 1.4 else 70
        balance_score = balance_metrics.balance_stability_score
        alert_penalty = len([a for a in compensation_alerts if a.severity in ['high', 'critical']]) * 10
        
        overall = (speed_score * 0.4 + balance_score * 0.6) - alert_penalty
        return max(0, min(100, overall))