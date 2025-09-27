"""
Advanced Logger Configuration
高機能ログシステムの設定
"""

from app.core.advanced_logger import get_logger, setup_advanced_logging, set_global_context
from app.core.config import settings

# メインアプリケーションロガー
main_logger = get_logger("gait_analysis")

# モジュール別ロガー
api_logger = get_logger("api")
database_logger = get_logger("database") 
auth_logger = get_logger("auth")
gait_logger = get_logger("gait")
mediapipe_logger = get_logger("mediapipe")
report_logger = get_logger("report")

def initialize_logging():
    """ログシステムを初期化"""
    setup_advanced_logging()
    
    # グローバル設定
    set_global_context(
        application="gait_analysis",
        version=getattr(settings, "APP_VERSION", "1.0.0"),
        environment=getattr(settings, "ENVIRONMENT", "development")
    )
    
    main_logger.info("Advanced logging system initialized successfully")

def get_module_logger(module_name: str):
    """モジュール名からロガーを取得"""
    return get_logger(module_name)

# 後方互換性のため
StructuredLogger = get_logger  # 既存コードとの互換性
setup_logging = setup_advanced_logging  # 既存関数との互換性