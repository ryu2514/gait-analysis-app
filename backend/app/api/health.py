"""
ヘルスチェックAPI
"""

from fastapi import APIRouter, status
from datetime import datetime
import psutil
import os
from app.core.config import settings
from app.core.logging import StructuredLogger

router = APIRouter()
logger = StructuredLogger(__name__)


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    システムヘルスチェック
    
    Returns:
        dict: システム状態情報
    """
    try:
        # システム情報取得
        cpu_percent = psutil.cpu_percent(interval=0 if getattr(settings, 'LIGHT_MODE', False) else 1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.APP_VERSION,
            "system": {
                "cpu_usage_percent": cpu_percent,
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_percent": round((disk.used / disk.total) * 100, 2)
                }
            },
            "mediapipe": {
                "model_complexity": settings.MEDIAPIPE_MODEL_COMPLEXITY,
                "min_detection_confidence": settings.MEDIAPIPE_MIN_DETECTION_CONFIDENCE,
                "min_tracking_confidence": settings.MEDIAPIPE_MIN_TRACKING_CONFIDENCE
            }
        }
        
        logger.info("Health check completed", status="healthy")
        return health_data
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """
    レディネスチェック（Kubernetes用）
    
    Returns:
        dict: サービス準備状態
    """
    try:
        # 重要なリソースの可用性チェック
        checks = {
            "mediapipe": _check_mediapipe(),
            "storage": _check_storage(),
            "memory": _check_memory()
        }
        
        all_ready = all(checks.values())
        
        return {
            "ready": all_ready,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks
        }
        
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        return {
            "ready": False,
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


def _check_mediapipe() -> bool:
    """MediaPipeの動作確認"""
    try:
        if getattr(settings, 'LIGHT_MODE', False):
            # 軽量モード時はMediaPipeチェックをスキップ
            return True
        import mediapipe as mp
        mp_pose = mp.solutions.pose
        return True
    except Exception:
        return False


def _check_storage() -> bool:
    """ストレージアクセス確認"""
    try:
        # 一時ファイル作成でディスク書き込み確認
        test_file = "/tmp/health_check_test"
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        return True
    except Exception:
        return False


def _check_memory() -> bool:
    """メモリ使用量確認"""
    try:
        memory = psutil.virtual_memory()
        # 使用率が90%以下であることを確認
        return memory.percent < 90
    except Exception:
        return False
