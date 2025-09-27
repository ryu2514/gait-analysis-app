"""
アプリケーション設定
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """アプリケーション設定クラス"""
    
    # アプリケーション基本設定
    APP_NAME: str = "MediaPipe Gait Analysis API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API設定
    API_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # JWT設定
    JWT_SECRET_KEY: str = "your-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24時間
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # CORS設定
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080", 
        "https://localhost:3000",
        "https://localhost:8080"
    ]
    
    # データベース設定
    DATABASE_URL: Optional[str] = None
    DATABASE_PATH: str = "data/gait_analysis.db"
    DATABASE_ECHO: bool = False
    
    # Firebase設定
    FIREBASE_PROJECT_ID: Optional[str] = None
    FIREBASE_PRIVATE_KEY_ID: Optional[str] = None
    FIREBASE_PRIVATE_KEY: Optional[str] = None
    FIREBASE_CLIENT_EMAIL: Optional[str] = None
    FIREBASE_CLIENT_ID: Optional[str] = None
    FIREBASE_AUTH_URI: str = "https://accounts.google.com/o/oauth2/auth"
    FIREBASE_TOKEN_URI: str = "https://oauth2.googleapis.com/token"
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
    
    # 認証設定
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGITS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = False
    
    # セッション設定
    SESSION_EXPIRE_HOURS: int = 24
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    
    # Google Cloud Storage設定
    GCS_BUCKET_NAME: Optional[str] = None
    GCS_CREDENTIALS_PATH: Optional[str] = None
    
    # MediaPipe設定
    MEDIAPIPE_MODEL_COMPLEXITY: int = 1  # 0, 1, 2
    MEDIAPIPE_MIN_DETECTION_CONFIDENCE: float = 0.5
    MEDIAPIPE_MIN_TRACKING_CONFIDENCE: float = 0.5
    MEDIAPIPE_ENABLE_SEGMENTATION: bool = False
    
    # 動画処理設定
    MAX_VIDEO_SIZE_MB: int = 100
    SUPPORTED_VIDEO_FORMATS: List[str] = ["mp4", "mov", "avi", "webm"]
    MAX_VIDEO_DURATION_SECONDS: int = 30
    TARGET_FPS: int = 30
    
    # 歩行分析設定
    MIN_GAIT_CYCLES: int = 2
    MAX_GAIT_CYCLES: int = 10
    SYMMETRY_THRESHOLD_PERCENT: float = 10.0
    
    # ログ設定
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # キャッシュ設定
    CACHE_TTL_SECONDS: int = 3600

    # 軽量モード/起動制御
    LIGHT_MODE: bool = False  # True の場合、MediaPipe等の重い依存を無効化しモックで応答
    DISABLE_TASK_QUEUE: bool = False  # True の場合、非同期タスクキューを起動しない
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# グローバル設定インスタンス
settings = Settings()
