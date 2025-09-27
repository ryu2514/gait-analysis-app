"""
歩行分析データモデル
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class AnalysisMode(str, Enum):
    """分析モード"""
    QUICK = "quick"      # 高速分析（基本指標のみ）
    STANDARD = "standard"  # 標準分析（全指標）
    DETAILED = "detailed"  # 詳細分析（波形データ含む）


class GaitCyclePhase(str, Enum):
    """歩行周期フェーズ"""
    HEEL_STRIKE = "heel_strike"
    LOADING_RESPONSE = "loading_response"
    MID_STANCE = "mid_stance"
    TERMINAL_STANCE = "terminal_stance"
    PRE_SWING = "pre_swing"
    INITIAL_SWING = "initial_swing"
    MID_SWING = "mid_swing"
    TERMINAL_SWING = "terminal_swing"


class LandmarkPoint(BaseModel):
    """MediaPose ランドマーク点"""
    x: float = Field(..., description="X座標（正規化）")
    y: float = Field(..., description="Y座標（正規化）")
    z: float = Field(..., description="Z座標（正規化）")
    visibility: float = Field(..., description="可視性スコア")


class GaitCycle(BaseModel):
    """歩行周期データ"""
    cycle_id: str = Field(..., description="周期ID")
    start_frame: int = Field(..., description="開始フレーム")
    end_frame: int = Field(..., description="終了フレーム")
    duration_seconds: float = Field(..., description="周期時間（秒）")
    side: str = Field(..., description="左右（left/right）")
    
    # 時空間パラメータ
    step_length_m: float = Field(..., description="歩幅（m）")
    step_width_m: float = Field(..., description="歩隔（m）")
    stance_time_seconds: float = Field(..., description="立脚時間（秒）")
    swing_time_seconds: float = Field(..., description="遊脚時間（秒）")
    stance_ratio: float = Field(..., description="立脚比率")
    
    # 関節角度ピーク値
    hip_flexion_peak_deg: float = Field(..., description="股関節最大屈曲角度")
    knee_flexion_peak_deg: float = Field(..., description="膝関節最大屈曲角度")
    ankle_dorsiflexion_peak_deg: float = Field(..., description="足関節最大背屈角度")
    
    # フェーズタイミング
    phase_timings: Dict[str, float] = Field(default_factory=dict, description="フェーズタイミング")


class SpatiotemporalParameters(BaseModel):
    """時空間パラメータ"""
    gait_speed_ms: float = Field(..., description="歩行速度（m/s）")
    cadence_steps_per_min: int = Field(..., description="ケイデンス（歩/分）")
    stride_length_m: float = Field(..., description="歩幅（m）")
    stride_time_s: float = Field(..., description="歩行周期時間（秒）")
    
    # 左右別パラメータ
    left_step_length_m: float = Field(..., description="左脚歩幅（m）")
    right_step_length_m: float = Field(..., description="右脚歩幅（m）")
    left_stance_time_s: float = Field(..., description="左脚立脚時間（秒）")
    right_stance_time_s: float = Field(..., description="右脚立脚時間（秒）")
    
    double_support_time_s: float = Field(..., description="両脚支持時間（秒）")


class SymmetryIndices(BaseModel):
    """対称性指標"""
    step_length_symmetry_percent: float = Field(..., description="歩幅対称性（%）")
    stance_time_symmetry_percent: float = Field(..., description="立脚時間対称性（%）")
    swing_time_symmetry_percent: float = Field(..., description="遊脚時間対称性（%）")
    
    # 関節角度対称性
    hip_flexion_symmetry_percent: float = Field(..., description="股関節屈曲対称性（%）")
    knee_flexion_symmetry_percent: float = Field(..., description="膝関節屈曲対称性（%）")
    ankle_dorsiflexion_symmetry_percent: float = Field(..., description="足関節背屈対称性（%）")
    
    overall_symmetry_score: float = Field(..., description="総合対称性スコア（0-100）")


class JointAngles(BaseModel):
    """関節角度データ"""
    # 股関節
    hip_flexion_deg: List[float] = Field(default_factory=list, description="股関節屈曲角度時系列")
    hip_extension_deg: List[float] = Field(default_factory=list, description="股関節伸展角度時系列")
    hip_abduction_deg: List[float] = Field(default_factory=list, description="股関節外転角度時系列")
    hip_rom_deg: float = Field(default=0.0, description="股関節可動域")
    
    # 膝関節
    knee_flexion_deg: List[float] = Field(default_factory=list, description="膝関節屈曲角度時系列")
    knee_heel_contact_deg: float = Field(default=0.0, description="ヒールコンタクト時膝関節角度")
    knee_max_flexion_deg: float = Field(default=0.0, description="膝関節最大屈曲角度")
    
    # 足関節
    ankle_dorsiflexion_deg: List[float] = Field(default_factory=list, description="足関節背屈角度時系列")
    ankle_plantarflexion_deg: List[float] = Field(default_factory=list, description="足関節底屈角度時系列")
    ankle_toe_off_deg: float = Field(default=0.0, description="トーオフ時足関節角度")
    
    # 骨盤・体幹
    pelvic_drop_deg: List[float] = Field(default_factory=list, description="骨盤傾斜角度時系列")
    pelvic_list_deg: List[float] = Field(default_factory=list, description="骨盤リスト（左右傾き）")
    trunk_rotation_deg: List[float] = Field(default_factory=list, description="体幹回旋角度時系列")
    
    frame_timestamps: List[float] = Field(default_factory=list, description="フレームタイムスタンプ")


class GaitAnalysisRequest(BaseModel):
    """歩行分析リクエスト"""
    user_height_cm: Optional[float] = Field(None, description="ユーザー身長（cm）")
    analysis_mode: AnalysisMode = Field(AnalysisMode.STANDARD, description="分析モード")
    calibration_object_height_cm: Optional[float] = Field(None, description="較正オブジェクト高さ（cm）")


class GaitAnalysisResponse(BaseModel):
    """歩行分析レスポンス"""
    analysis_id: str = Field(..., description="分析ID")
    status: str = Field(..., description="分析状態")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="分析完了時刻")
    processing_time_seconds: float = Field(..., description="処理時間（秒）")
    
    # 分析結果
    spatiotemporal_params: Optional[SpatiotemporalParameters] = None
    symmetry_indices: Optional[SymmetryIndices] = None
    gait_cycles: List[GaitCycle] = Field(default_factory=list, description="検出された歩行周期")
    joint_angles: Optional[JointAngles] = None
    
    # 品質指標
    video_quality_score: float = Field(..., description="動画品質スコア（0-100）")
    pose_detection_confidence: float = Field(..., description="姿勢検出信頼度")
    gait_cycles_detected: int = Field(..., description="検出された歩行周期数")
    
    # 総合評価
    overall_gait_score: float = Field(..., description="総合歩行スコア（0-100）")
    recommendations: List[str] = Field(default_factory=list, description="改善提案")
    
    # メタデータ
    video_info: Dict[str, Any] = Field(default_factory=dict, description="動画情報")
    analysis_settings: Dict[str, Any] = Field(default_factory=dict, description="分析設定")

    @field_validator("overall_gait_score", "video_quality_score", mode="before")
    @classmethod
    def validate_score_range(cls, v):
        """スコアの範囲チェック（0-100）"""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("スコアは0-100の範囲である必要があります")
        return v


class GaitAnalysisHistory(BaseModel):
    """歩行分析履歴"""
    user_id: str = Field(..., description="ユーザーID")
    analysis_id: str = Field(..., description="分析ID")
    timestamp: datetime = Field(..., description="分析日時")
    gait_speed_ms: float = Field(..., description="歩行速度")
    overall_score: float = Field(..., description="総合スコア")
    symmetry_score: float = Field(..., description="対称性スコア")
    notes: Optional[str] = Field(None, description="メモ")

    @field_validator("gait_speed_ms", mode="before")
    @classmethod
    def validate_gait_speed(cls, v):
        """歩行速度の妥当性チェック"""
        if v is not None and (v < 0 or v > 5.0):  # 0-5 m/s の範囲
            raise ValueError("歩行速度が妥当な範囲を超えています")
        return v


class BalanceMetrics(BaseModel):
    """重心・バランス指標"""
    # 重心移動指標
    com_lateral_displacement_cm: List[float] = Field(default_factory=list, description="重心左右移動幅（cm）")
    com_anterior_posterior_cm: List[float] = Field(default_factory=list, description="重心前後移動幅（cm）")
    com_vertical_displacement_cm: List[float] = Field(default_factory=list, description="重心上下変位（cm）")
    
    # 重心投影線データ
    com_projection_x: List[float] = Field(default_factory=list, description="重心投影線X座標")
    com_projection_y: List[float] = Field(default_factory=list, description="重心投影線Y座標")
    
    # バランス指標
    lateral_displacement_max_cm: float = Field(default=0.0, description="最大左右移動幅（cm）")
    vertical_displacement_max_cm: float = Field(default=0.0, description="最大上下変位（cm）")
    balance_stability_score: float = Field(default=0.0, description="バランス安定性スコア（0-100）")


class CompensationAlert(BaseModel):
    """代償動作アラート"""
    alert_type: str = Field(..., description="アラートタイプ")
    severity: str = Field(..., description="重要度（low/medium/high/critical）")
    message: str = Field(..., description="アラートメッセージ")
    frame_range: tuple[int, int] = Field(..., description="発生フレーム範囲")
    threshold_value: float = Field(..., description="しきい値")
    measured_value: float = Field(..., description="測定値")
    
    
class DetailedSpatiotemporalParameters(BaseModel):
    """詳細時空間パラメータ"""
    # 基本パラメータ（継承）
    gait_speed_ms: float = Field(..., description="歩行速度（m/s）")
    cadence_steps_per_min: int = Field(..., description="ケイデンス（歩/分）")
    
    # 拡張パラメータ
    step_length_cm: float = Field(..., description="歩幅（cm）")
    stride_length_cm: float = Field(..., description="ストライド長（cm）")
    
    # 時間パラメータ（歩行周期%）
    stance_time_percent: float = Field(..., description="立脚時間（% gait cycle）")
    swing_time_percent: float = Field(..., description="遊脚時間（% gait cycle）")
    double_support_percent: float = Field(..., description="両脚支持時間（% gait cycle）")
    
    # 左右別速度・対称性
    left_side_speed_ms: float = Field(..., description="左側平均速度（m/s）")
    right_side_speed_ms: float = Field(..., description="右側平均速度（m/s）")
    stance_time_asymmetry_percent: float = Field(..., description="立脚時間非対称性（%）")
    
    
class EnhancedOutputData(BaseModel):
    """拡張出力データ"""
    # 正規化時間波形データ
    normalized_time_series: Dict[str, List[float]] = Field(default_factory=dict, description="正規化時間波形データ")
    
    # 動画出力パス
    slow_motion_skeleton_video_path: Optional[str] = Field(None, description="スローモーション骨格動画パス")
    
    # レポートパス
    color_coded_pdf_report_path: Optional[str] = Field(None, description="カラー判定PDFレポートパス")
    
    # 処理時間情報
    total_processing_time_seconds: float = Field(..., description="総処理時間（秒）")
    target_processing_time_seconds: int = Field(default=30, description="目標処理時間（秒）")