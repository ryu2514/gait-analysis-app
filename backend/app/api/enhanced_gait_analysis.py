"""
拡張歩行分析API（Enhanced Features）
Enhanced Gait Analysis API with all new features
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, status, BackgroundTasks, Query
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional, Dict, Any, List
import uuid
import tempfile
import os
from datetime import datetime
from pathlib import Path

from app.models.gait_models import (
    GaitAnalysisRequest, GaitAnalysisResponse, 
    DetailedSpatiotemporalParameters, BalanceMetrics, 
    CompensationAlert, EnhancedOutputData
)
from app.services.gait_service import GaitAnalysisService
from app.services.video_service import VideoProcessingService
from app.core.advanced_logger import get_logger
from app.core.config import settings

router = APIRouter()
logger = get_logger(__name__)

# サービスインスタンス
gait_service = GaitAnalysisService()
video_service = VideoProcessingService()


@router.post("/analyze-enhanced", response_model=Dict[str, Any])
async def analyze_gait_enhanced(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    user_height_cm: Optional[float] = Query(None, description="ユーザー身長（cm）"),
    analysis_mode: str = Query("detailed", description="分析モード（standard/detailed/quick）"),
    camera_position: str = Query("side", description="カメラ位置（side/posterior/anterior）"),
    target_fps: int = Query(60, description="目標フレームレート"),
    device_type: str = Query("mobile", description="デバイスタイプ（mobile/tablet/desktop）"),
    enable_30s_optimization: bool = Query(True, description="30秒最適化有効化"),
    enable_compensation_alerts: bool = Query(True, description="代償動作アラート有効化"),
    enable_balance_analysis: bool = Query(True, description="バランス分析有効化"),
    generate_enhanced_output: bool = Query(True, description="拡張出力生成有効化")
):
    """
    拡張歩行分析エンドポイント
    
    新機能を全て統合した最新の歩行分析API
    - 30秒高速処理
    - 33ランドマーク活用
    - 代償動作検出
    - バランス・重心分析
    - 拡張出力（正規化グラフ、動画、PDFレポート）
    """
    analysis_id = str(uuid.uuid4())
    start_time = datetime.utcnow()
    
    logger.set_context(analysis_id=analysis_id, endpoint="/analyze-enhanced", method="POST")
    
    with logger.performance_timer("enhanced_gait_analysis_api"):
        logger.api(
            "Enhanced gait analysis API request started",
            analysis_id=analysis_id,
            filename=video.filename,
            analysis_mode=analysis_mode,
            camera_position=camera_position,
            target_fps=target_fps,
            enable_30s_optimization=enable_30s_optimization,
            enable_compensation_alerts=enable_compensation_alerts,
            enable_balance_analysis=enable_balance_analysis
        )
    
    try:
        # 拡張入力検証
        await _validate_enhanced_input(video, analysis_mode, target_fps)
        
        # 一時ファイル作成
        temp_video_path = None
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_video_path = temp_file.name
            content = await video.read()
            temp_file.write(content)
        
        # 動画前処理（拡張版）
        processed_video_info = await video_service.preprocess_video_enhanced(
            temp_video_path,
            target_fps=target_fps,
            device_optimization=device_type
        )
        
        # 拡張歩行分析実行
        if enable_30s_optimization:
            analysis_result = await gait_service.analyze_gait_optimized(
                video_path=processed_video_info["path"],
                user_height_cm=user_height_cm,
                analysis_mode=analysis_mode,
                analysis_id=analysis_id,
                camera_position=camera_position,
                target_fps=target_fps,
                device_type=device_type,
                enable_30s_optimization=True
            )
        else:
            analysis_result = await gait_service.analyze_gait(
                video_path=processed_video_info["path"],
                user_height_cm=user_height_cm,
                analysis_mode=analysis_mode,
                analysis_id=analysis_id,
                camera_position=camera_position,
                target_fps=target_fps,
                device_type=device_type
            )
        
        # 処理時間計算
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # 拡張結果構造化
        enhanced_response = _structure_enhanced_response(
            analysis_id, analysis_result, processing_time
        )
        
        # バックグラウンドでクリーンアップ
        background_tasks.add_task(
            _cleanup_temp_files, 
            [temp_video_path, processed_video_info["path"]]
        )
        
        logger.info(
            "Enhanced gait analysis completed",
            analysis_id=analysis_id,
            processing_time_seconds=processing_time,
            target_achieved=processing_time <= 30.0,
            spatiotemporal_score=enhanced_response.get("scores", {}).get("spatiotemporal", 0),
            balance_score=enhanced_response.get("scores", {}).get("balance", 0),
            compensation_alerts_count=len(enhanced_response.get("compensation_alerts", []))
        )
        
        return enhanced_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Enhanced gait analysis failed",
            analysis_id=analysis_id,
            error=str(e)
        )
        
        # エラー時のクリーンアップ
        if temp_video_path and os.path.exists(temp_video_path):
            os.unlink(temp_video_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"拡張歩行分析に失敗しました: {str(e)}"
        )


@router.get("/analysis-enhanced/{analysis_id}")
async def get_enhanced_analysis_result(analysis_id: str):
    """拡張分析結果取得エンドポイント"""
    try:
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
        logger.error("Failed to get enhanced analysis result", analysis_id=analysis_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="拡張分析結果の取得に失敗しました"
        )


@router.get("/download-report/{analysis_id}")
async def download_analysis_report(
    analysis_id: str,
    format: str = Query("pdf", description="レポート形式（pdf/video/json）")
):
    """分析レポートダウンロードエンドポイント"""
    try:
        # レポートファイルパスの取得
        report_path = await _get_report_path(analysis_id, format)
        
        if not report_path or not os.path.exists(report_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="レポートファイルが見つかりません"
            )
        
        # ファイル形式に応じたレスポンス
        media_type_map = {
            "pdf": "application/pdf",
            "video": "video/mp4",
            "json": "application/json"
        }
        
        return FileResponse(
            path=report_path,
            media_type=media_type_map.get(format, "application/octet-stream"),
            filename=f"gait_analysis_{analysis_id}.{format}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to download report", analysis_id=analysis_id, format=format, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="レポートダウンロードに失敗しました"
        )


@router.get("/capabilities")
async def get_enhanced_capabilities():
    """拡張機能一覧取得エンドポイント"""
    return {
        "enhanced_features": {
            "30_second_processing": True,
            "33_landmarks_detection": True,
            "compensation_alerts": True,
            "balance_analysis": True,
            "enhanced_output": True,
            "parallel_processing": True,
            "real_time_optimization": True
        },
        "analysis_modes": ["quick", "standard", "detailed"],
        "camera_positions": ["side", "posterior", "anterior"],
        "device_optimizations": ["mobile", "tablet", "desktop"],
        "output_formats": {
            "reports": ["pdf", "json"],
            "videos": ["mp4"],
            "graphs": ["png", "svg"],
            "data": ["csv", "json"]
        },
        "spatiotemporal_parameters": [
            "gait_speed_ms", "cadence_steps_per_min", 
            "step_length_cm", "stride_length_cm",
            "stance_time_percent", "swing_time_percent",
            "stance_time_asymmetry_percent"
        ],
        "kinematic_parameters": [
            "hip_flexion_rom", "knee_max_flexion", 
            "ankle_dorsiflexion", "ankle_plantarflexion",
            "pelvic_drop", "trunk_rotation"
        ],
        "balance_parameters": [
            "com_lateral_displacement", "com_vertical_displacement",
            "balance_stability_score", "com_projection_trajectory"
        ],
        "compensation_alerts": [
            "out_toeing", "in_toeing", "knee_valgus", "knee_varus",
            "trendelenburg_sign", "pelvic_drop", "lateral_sway",
            "excessive_trunk_rotation"
        ],
        "performance_specs": {
            "target_processing_time_sec": 30,
            "max_video_size_mb": 100,
            "max_video_duration_sec": 30,
            "supported_fps": [30, 60, 120],
            "supported_resolutions": ["480p", "720p", "1080p"]
        }
    }


@router.get("/demo-data")
async def get_demo_data():
    """デモ用サンプルデータ取得エンドポイント"""
    try:
        demo_data_path = Path("/app/demo_data")
        
        if not demo_data_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="デモデータが見つかりません"
            )
        
        # サンプル動画ファイル一覧
        sample_videos = list(demo_data_path.glob("videos/*.mp4"))
        
        # サンプル結果ファイル一覧
        sample_reports = list(demo_data_path.glob("reports/*.pdf"))
        
        return {
            "sample_videos": [
                {
                    "filename": video.name,
                    "path": str(video),
                    "size_mb": round(video.stat().st_size / (1024 * 1024), 2),
                    "description": _get_video_description(video.name)
                }
                for video in sample_videos
            ],
            "sample_reports": [
                {
                    "filename": report.name,
                    "path": str(report),
                    "size_mb": round(report.stat().st_size / (1024 * 1024), 2)
                }
                for report in sample_reports
            ],
            "usage_instructions": {
                "video_upload": "POST /api/v1/gait-analysis/analyze-enhanced でサンプル動画をアップロード",
                "parameter_settings": "camera_position=side, analysis_mode=detailed を推奨",
                "expected_processing_time": "15-25秒（30秒目標）",
                "output_formats": "PDF レポート、スローモーション動画、JSON データ"
            }
        }
        
    except Exception as e:
        logger.error("Failed to get demo data", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="デモデータの取得に失敗しました"
        )


# Helper functions

async def _validate_enhanced_input(
    video: UploadFile, 
    analysis_mode: str, 
    target_fps: int
) -> None:
    """拡張入力検証"""
    # 基本検証
    await _validate_video_input(video)
    
    # 拡張検証
    if analysis_mode not in ["quick", "standard", "detailed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無効な分析モードです。quick/standard/detailed から選択してください"
        )
    
    if target_fps not in [30, 60, 120]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無効なフレームレートです。30/60/120 から選択してください"
        )


def _structure_enhanced_response(
    analysis_id: str, 
    analysis_result: Dict[str, Any], 
    processing_time: float
) -> Dict[str, Any]:
    """拡張レスポンス構造化"""
    
    # 基本情報
    response = {
        "analysis_id": analysis_id,
        "status": "completed",
        "processing_time_seconds": processing_time,
        "target_achieved": processing_time <= 30.0,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # 拡張時空間パラメータ
    if "enhanced_spatiotemporal_params" in analysis_result:
        response["spatiotemporal_parameters"] = analysis_result["enhanced_spatiotemporal_params"]
    
    # キネマティクス指標
    if "enhanced_joint_angles" in analysis_result:
        response["kinematic_parameters"] = analysis_result["enhanced_joint_angles"]
    
    # バランス指標
    if "balance_metrics" in analysis_result:
        response["balance_metrics"] = analysis_result["balance_metrics"]
    
    # 代償動作アラート
    if "compensation_alerts" in analysis_result:
        response["compensation_alerts"] = analysis_result["compensation_alerts"]
    
    # 拡張出力
    if "enhanced_output" in analysis_result:
        response["enhanced_output"] = analysis_result["enhanced_output"]
    
    # スコア集約
    response["scores"] = {
        "overall": analysis_result.get("overall_gait_score", 0),
        "spatiotemporal": _calculate_spatiotemporal_score(analysis_result),
        "balance": analysis_result.get("balance_metrics", {}).get("balance_stability_score", 0),
        "quality": analysis_result.get("video_quality_score", 0)
    }
    
    # 改善提案
    response["recommendations"] = analysis_result.get("recommendations", [])
    
    # 最適化情報
    if "optimization_info" in analysis_result:
        response["optimization_info"] = analysis_result["optimization_info"]
    
    return response


def _calculate_spatiotemporal_score(analysis_result: Dict[str, Any]) -> float:
    """時空間パラメータスコア計算"""
    params = analysis_result.get("enhanced_spatiotemporal_params")
    if not params:
        return 0.0
    
    # 簡易スコア計算
    speed_score = min(100, (params.get("gait_speed_ms", 0) / 1.4) * 100)
    cadence_score = 100 if 110 <= params.get("cadence_steps_per_min", 0) <= 130 else 70
    
    return (speed_score + cadence_score) / 2


async def _get_report_path(analysis_id: str, format: str) -> Optional[str]:
    """レポートファイルパス取得"""
    reports_dir = Path("/app/reports")
    
    filename_map = {
        "pdf": f"gait_analysis_report_{analysis_id}.pdf",
        "video": f"slow_motion_skeleton_{analysis_id}.mp4",
        "json": f"analysis_data_{analysis_id}.json"
    }
    
    filename = filename_map.get(format)
    if not filename:
        return None
    
    report_path = reports_dir / filename
    return str(report_path) if report_path.exists() else None


def _get_video_description(filename: str) -> str:
    """動画ファイル説明取得"""
    descriptions = {
        "normal_gait.mp4": "正常歩行のサンプル動画",
        "pathological_gait.mp4": "病的歩行のサンプル動画", 
        "elderly_gait.mp4": "高齢者歩行のサンプル動画",
        "athletic_gait.mp4": "アスリート歩行のサンプル動画"
    }
    return descriptions.get(filename, "サンプル歩行動画")


async def _validate_video_input(video: UploadFile) -> None:
    """動画入力検証（基本版から継承）"""
    # ファイルサイズチェック
    max_size = getattr(settings, 'MAX_VIDEO_SIZE_MB', 100) * 1024 * 1024
    if video.size and video.size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"ファイルサイズが大きすぎます（最大: {max_size // (1024*1024)}MB）"
        )
    
    # ファイル形式チェック
    if not video.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ファイル名が指定されていません"
        )
    
    file_extension = video.filename.split('.')[-1].lower()
    supported_formats = getattr(settings, 'SUPPORTED_VIDEO_FORMATS', ['mp4', 'avi', 'mov'])
    if file_extension not in supported_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"サポートされていないファイル形式です。対応形式: {', '.join(supported_formats)}"
        )


async def _cleanup_temp_files(file_paths: List[str]) -> None:
    """一時ファイルクリーンアップ"""
    for path in file_paths:
        try:
            if path and os.path.exists(path):
                os.unlink(path)
                logger.debug("Temp file cleaned up", file_path=path)
        except Exception as e:
            logger.warning("Failed to cleanup temp file", file_path=path, error=str(e))