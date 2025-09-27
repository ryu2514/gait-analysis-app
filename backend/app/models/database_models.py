"""
データベースモデル定義
SQLAlchemyを使用したORMモデル
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

Base = declarative_base()


class User(Base):
    """ユーザーテーブル"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)  # Firebaseユーザーの場合はNull可能
    hashed_password = Column(String(255), nullable=True)  # Firebaseユーザーの場合はNull
    full_name = Column(String(200))
    
    # プロフィール情報
    height_cm = Column(Float)
    weight_kg = Column(Float)
    age = Column(Integer)
    gender = Column(String(10))  # male, female, other
    
    # アカウント設定
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    user_type = Column(String(20), default="standard")  # standard, premium, professional, admin
    
    # Firebase認証関連
    firebase_uid = Column(String(128), unique=True, nullable=True, index=True)
    
    # 設定
    timezone = Column(String(50), default="Asia/Tokyo")
    language = Column(String(10), default="ja")
    
    # タイムスタンプ
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)
    
    # リレーション
    gait_analyses = relationship("GaitAnalysis", back_populates="user", cascade="all, delete-orphan")
    patient_profiles = relationship("PatientProfile", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    login_history = relationship("LoginHistory", back_populates="user", cascade="all, delete-orphan")


class PatientProfile(Base):
    """患者プロフィールテーブル（理学療法士用）"""
    __tablename__ = "patient_profiles"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # 基本情報
    patient_id = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(DateTime)
    
    # 医療情報
    diagnosis = Column(Text)  # 診断名
    medical_history = Column(Text)  # 病歴
    medications = Column(Text)  # 服薬情報
    allergies = Column(Text)  # アレルギー情報
    
    # 身体測定
    height_cm = Column(Float)
    weight_kg = Column(Float)
    bmi = Column(Float)
    
    # 歩行関連情報
    mobility_aids = Column(String(200))  # 歩行補助具
    previous_gait_issues = Column(Text)  # 過去の歩行問題
    therapy_goals = Column(Text)  # 治療目標
    
    # 担当者情報
    therapist_name = Column(String(200))
    facility_name = Column(String(200))
    
    # メタデータ
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # リレーション
    user = relationship("User", back_populates="patient_profiles")


class GaitAnalysis(Base):
    """歩行分析結果テーブル"""
    __tablename__ = "gait_analyses"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    analysis_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # 分析メタデータ
    analysis_date = Column(DateTime, default=func.now())
    processing_time_seconds = Column(Float)
    analysis_mode = Column(String(20))  # basic, standard, detailed
    
    # 動画情報
    video_filename = Column(String(500))
    video_duration_seconds = Column(Float)
    video_resolution = Column(String(20))
    video_fps = Column(Float)
    video_quality_score = Column(Float)
    
    # 分析設定
    user_height_cm = Column(Float)
    scale_factor = Column(Float)
    model_complexity = Column(Integer)
    
    # 品質指標
    pose_detection_confidence = Column(Float)
    gait_cycles_detected = Column(Integer)
    
    # スコア
    overall_gait_score = Column(Float)
    
    # 時空間パラメータ（JSON形式で保存）
    spatiotemporal_params = Column(JSON)
    
    # 対称性指標（JSON形式で保存）
    symmetry_indices = Column(JSON)
    
    # 関節角度データ（JSON形式で保存）
    joint_angles = Column(JSON)
    
    # 歩行周期データ（JSON形式で保存）
    gait_cycles = Column(JSON)
    
    # 推奨事項
    recommendations = Column(JSON)
    
    # ファイルパス
    video_file_path = Column(String(1000))
    report_pdf_path = Column(String(1000))
    report_png_path = Column(String(1000))
    
    # タイムスタンプ
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # リレーション
    user = relationship("User", back_populates="gait_analyses")
    reports = relationship("AnalysisReport", back_populates="gait_analysis", cascade="all, delete-orphan")


class AnalysisReport(Base):
    """生成されたレポートテーブル"""
    __tablename__ = "analysis_reports"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    gait_analysis_id = Column(String(36), ForeignKey("gait_analyses.id"), nullable=False)
    
    # レポート情報
    report_type = Column(String(20), nullable=False)  # pdf, png, base64
    report_format = Column(String(10), nullable=False)  # PDF, PNG
    template_id = Column(String(50))
    
    # ファイル情報
    file_path = Column(String(1000))
    file_size_bytes = Column(Integer)
    file_hash = Column(String(64))  # SHA-256ハッシュ
    
    # 生成設定
    generation_settings = Column(JSON)
    
    # 患者情報（レポート生成時の情報）
    patient_info = Column(JSON)
    
    # メタデータ
    generated_at = Column(DateTime, default=func.now())
    downloaded_at = Column(DateTime)
    download_count = Column(Integer, default=0)
    
    # リレーション
    gait_analysis = relationship("GaitAnalysis", back_populates="reports")


class AnalysisSession(Base):
    """分析セッションテーブル（進行中の分析を追跡）"""
    __tablename__ = "analysis_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # セッション状態
    status = Column(String(20), default="initiated")  # initiated, uploading, processing, completed, failed
    progress_percentage = Column(Float, default=0.0)
    current_step = Column(String(100))
    
    # エラー情報
    error_message = Column(Text)
    error_details = Column(JSON)
    
    # 処理時間
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    
    # 結果ID（完了時）
    result_analysis_id = Column(String(36))
    
    # タイムスタンプ
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class SystemMetrics(Base):
    """システムメトリクステーブル（監視・分析用）"""
    __tablename__ = "system_metrics"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # メトリクス情報
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20))
    metric_tags = Column(JSON)  # 追加のタグ情報
    
    # 関連分析ID
    analysis_id = Column(String(100), index=True)
    
    # タイムスタンプ
    timestamp = Column(DateTime, default=func.now(), index=True)


class UserPreferences(Base):
    """ユーザー設定テーブル"""
    __tablename__ = "user_preferences"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)
    
    # UI設定
    theme = Column(String(20), default="light")  # light, dark
    language = Column(String(10), default="ja")  # ja, en
    
    # 分析設定
    default_analysis_mode = Column(String(20), default="standard")
    auto_save_reports = Column(Boolean, default=True)
    notification_preferences = Column(JSON)
    
    # レポート設定
    default_report_format = Column(String(10), default="pdf")
    include_recommendations = Column(Boolean, default=True)
    report_template_id = Column(String(50))
    
    # プライバシー設定
    data_retention_days = Column(Integer, default=365)
    allow_anonymous_analytics = Column(Boolean, default=True)
    
    # タイムスタンプ
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class RefreshToken(Base):
    """リフレッシュトークンテーブル"""
    __tablename__ = "refresh_tokens"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    is_revoked = Column(Boolean, default=False)
    device_info = Column(Text, nullable=True)  # デバイス情報（JSON）
    
    # リレーション
    user = relationship("User", back_populates="refresh_tokens")


class PasswordResetToken(Base):
    """パスワードリセットトークンテーブル"""
    __tablename__ = "password_reset_tokens"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    is_used = Column(Boolean, default=False)


class EmailVerificationToken(Base):
    """メール認証トークンテーブル"""
    __tablename__ = "email_verification_tokens"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    is_used = Column(Boolean, default=False)


class LoginHistory(Base):
    """ログイン履歴テーブル"""
    __tablename__ = "login_history"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    login_timestamp = Column(DateTime, default=func.now())
    ip_address = Column(String(45), nullable=True)  # IPv6対応
    user_agent = Column(Text, nullable=True)
    login_method = Column(String(50), nullable=False)  # jwt, firebase, google, etc.
    success = Column(Boolean, default=True)
    failure_reason = Column(String(100), nullable=True)
    
    # リレーション
    user = relationship("User", back_populates="login_history")


class UserSession(Base):
    """ユーザーセッションテーブル"""
    __tablename__ = "user_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    session_token = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=func.now())
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)


class AuditLog(Base):
    """監査ログテーブル"""
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # ユーザー情報
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    username = Column(String(100))
    user_ip = Column(String(45))  # IPv6対応
    
    # アクション情報
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(36))
    
    # 詳細情報
    details = Column(JSON)
    old_values = Column(JSON)  # 変更前の値
    new_values = Column(JSON)  # 変更後の値
    
    # 結果
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    
    # タイムスタンプ
    timestamp = Column(DateTime, default=func.now(), index=True)


# インデックス定義
from sqlalchemy import Index

# よく使用される複合インデックス
Index('idx_gait_analysis_user_date', GaitAnalysis.user_id, GaitAnalysis.analysis_date)
Index('idx_analysis_session_user_status', AnalysisSession.user_id, AnalysisSession.status)
Index('idx_system_metrics_name_timestamp', SystemMetrics.metric_name, SystemMetrics.timestamp)
Index('idx_audit_log_user_action_timestamp', AuditLog.user_id, AuditLog.action, AuditLog.timestamp)

# 認証関連インデックス
Index('idx_refresh_token_user_expires', RefreshToken.user_id, RefreshToken.expires_at)
Index('idx_login_history_user_timestamp', LoginHistory.user_id, LoginHistory.login_timestamp)
Index('idx_user_session_user_active', UserSession.user_id, UserSession.is_active)
Index('idx_password_reset_token_expires', PasswordResetToken.expires_at, PasswordResetToken.is_used)
Index('idx_email_verification_token_expires', EmailVerificationToken.expires_at, EmailVerificationToken.is_used)