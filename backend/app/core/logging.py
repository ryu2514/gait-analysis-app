"""
ログ設定
"""

import logging
import sys
from typing import Dict, Any
from app.core.config import settings


def setup_logging() -> None:
    """ログシステムの初期化"""
    
    # ログレベル設定
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # ログフォーマット設定
    formatter = logging.Formatter(
        fmt=settings.LOG_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # ルートロガー設定
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # 既存のハンドラーをクリア
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    
    # MediaPipeのログレベルを調整（冗長なログを減らす）
    logging.getLogger("mediapipe").setLevel(logging.WARNING)
    logging.getLogger("opencv").setLevel(logging.WARNING)
    

def get_logger(name: str) -> logging.Logger:
    """名前付きロガーの取得"""
    return logging.getLogger(name)


class StructuredLogger:
    """構造化ログ出力クラス"""
    
    def __init__(self, name: str):
        self.logger = get_logger(name)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """情報ログ出力"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """警告ログ出力"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """エラーログ出力"""
        self._log(logging.ERROR, message, **kwargs)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """デバッグログ出力"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs: Any) -> None:
        """ログ出力の内部実装"""
        if kwargs:
            extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            full_message = f"{message} | {extra_info}"
        else:
            full_message = message
        
        self.logger.log(level, full_message)