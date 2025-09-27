"""
歩行分析API
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import uuid
import tempfile
import os
from datetime import datetime

from app.models.gait_models import GaitAnalysisRequest, GaitAnalysisResponse
from app.services.gait_service import GaitAnalysisService
from app.services.video_service import VideoProcessingService
from app.core.advanced_logger import get_logger
from app.core.config import settings

router = APIRouter()
logger = get_logger(__name__)

# サービスインスタンス
gait_service = GaitAnalysisService()
video_service = VideoProcessingService()


@router.post("/analyze", response_model=GaitAnalysisResponse)
async def analyze_gait(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    user_height_cm: Optional[float] = None,
    analysis_mode: str = "standard"
):
    """
    歩行動画分析エンドポイント
    
    Args:
        video: アップロードされた歩行動画ファイル
        user_height_cm: ユーザーの身長（cm）
        analysis_mode: 分析モード（standard, detailed, quick）
    
    Returns:
        GaitAnalysisResponse: 歩行分析結果
    """
    analysis_id = str(uuid.uuid4())
    start_time = datetime.utcnow()
    
    # APIコンテキスト設定
    logger.set_context(analysis_id=analysis_id, endpoint="/analyze", method="POST")
    
    with logger.performance_timer("api_gait_analysis"):
        logger.api(
            "Gait analysis API request started",
            analysis_id=analysis_id,
            filename=video.filename,
            content_type=video.content_type,
            analysis_mode=analysis_mode,
            file_size_bytes=video.size if hasattr(video, 'size') else None
        )
    
    try:
        # 入力検証
        await _validate_video_input(video)
        
        # 一時ファイル作成
        temp_video_path = None
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_video_path = temp_file.name
            content = await video.read()
            temp_file.write(content)
        
        # 動画前処理
        processed_video_info = await video_service.preprocess_video(
            temp_video_path,
            target_fps=settings.TARGET_FPS
        )
        
        # 歩行分析実行
        analysis_result = await gait_service.analyze_gait(
            video_path=processed_video_info["path"],
            user_height_cm=user_height_cm,
            analysis_mode=analysis_mode,
            analysis_id=analysis_id
        )
        
        # バックグラウンドでクリーンアップ
        background_tasks.add_task(_cleanup_temp_files, [temp_video_path, processed_video_info["path"]])
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(
            "Gait analysis completed",
            analysis_id=analysis_id,
            processing_time_seconds=processing_time,
            gait_speed=analysis_result.get("gait_speed", 0),
            gait_cycles_detected=len(analysis_result.get("gait_cycles", []))
        )
        
        return GaitAnalysisResponse(
            analysis_id=analysis_id,
            status="completed",
            processing_time_seconds=processing_time,
            **analysis_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Gait analysis failed",
            analysis_id=analysis_id,
            error=str(e)
        )
        
        # エラー時のクリーンアップ
        if temp_video_path and os.path.exists(temp_video_path):
            os.unlink(temp_video_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"歩行分析に失敗しました: {str(e)}"
        )


@router.get("/analysis/{analysis_id}")
async def get_analysis_result(analysis_id: str):
    """
    分析結果取得エンドポイント
    
    Args:
        analysis_id: 分析ID
    
    Returns:
        dict: 分析結果または状態
    """
    try:
        # TODO: データベースから分析結果を取得
        result = await gait_service.get_analysis_result(analysis_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分析結果が見つかりません"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get analysis result", analysis_id=analysis_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分析結果の取得に失敗しました"
        )


@router.get("/supported-formats")
async def get_supported_formats():
    """
    サポートされている動画フォーマット一覧取得
    
    Returns:
        dict: サポートフォーマット情報
    """
    return {
        "supported_formats": settings.SUPPORTED_VIDEO_FORMATS,
        "max_file_size_mb": settings.MAX_VIDEO_SIZE_MB,
        "max_duration_seconds": settings.MAX_VIDEO_DURATION_SECONDS,
        "recommended_fps": settings.TARGET_FPS,
        "recommended_resolution": "1080p",
        "shooting_guidelines": {
            "distance_meters": "3-5",
            "angle": "側方または前方",
            "duration_seconds": "5-10",
            "lighting": "十分な照明",
            "background": "シンプルな背景"
        }
    }


async def _validate_video_input(video: UploadFile) -> None:
    """
    動画入力の検証
    
    Args:
        video: アップロードされた動画ファイル
    
    Raises:
        HTTPException: 検証エラー
    """
    # ファイルサイズチェック
    if video.size and video.size > settings.MAX_VIDEO_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"ファイルサイズが大きすぎます（最大: {settings.MAX_VIDEO_SIZE_MB}MB）"
        )
    
    # ファイル形式チェック
    if not video.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ファイル名が指定されていません"
        )
    
    file_extension = video.filename.split('.')[-1].lower()
    if file_extension not in settings.SUPPORTED_VIDEO_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"サポートされていないファイル形式です。対応形式: {', '.join(settings.SUPPORTED_VIDEO_FORMATS)}"
        )


async def _cleanup_temp_files(file_paths: list) -> None:
    """
    一時ファイルのクリーンアップ
    
    Args:
        file_paths: 削除するファイルパスのリスト
    """
    for path in file_paths:
        try:
            if path and os.path.exists(path):
                os.unlink(path)
                logger.debug("Temp file cleaned up", file_path=path)
        except Exception as e:
            logger.warning("Failed to cleanup temp file", file_path=path, error=str(e))