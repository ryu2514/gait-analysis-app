"""
レポート生成API エンドポイント
"""

import os
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse, JSONResponse
from datetime import datetime

from app.services.report_generator import ReportGenerator
from app.models.gait_models import GaitAnalysisResponse
from app.core.logging import StructuredLogger
from app.core.config import settings

logger = StructuredLogger(__name__)
router = APIRouter()


@router.post("/generate/pdf")
async def generate_pdf_report(
    analysis_result: GaitAnalysisResponse,
    patient_info: Optional[Dict[str, Any]] = None,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    PDF形式の詳細レポートを生成
    
    Args:
        analysis_result: 歩行分析結果データ
        patient_info: 患者情報（オプション）
        background_tasks: バックグラウンドタスク
        
    Returns:
        FileResponse: 生成されたPDFファイル
    """
    try:
        logger.info("PDF report generation requested", 
                   analysis_id=analysis_result.analysis_id)
        
        report_generator = ReportGenerator()
        pdf_path = await report_generator.generate_pdf_report(
            analysis_result, patient_info
        )
        
        if not os.path.exists(pdf_path):
            raise HTTPException(
                status_code=500, 
                detail="PDFファイルの生成に失敗しました"
            )
        
        # ファイル削除をバックグラウンドタスクに追加
        background_tasks.add_task(_cleanup_file, pdf_path)
        
        # ファイル名を生成
        filename = f"gait_analysis_report_{analysis_result.analysis_id[:8]}.pdf"
        
        return FileResponse(
            path=pdf_path,
            filename=filename,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error("Failed to generate PDF report", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"PDFレポート生成エラー: {str(e)}"
        )


@router.post("/generate/png")
async def generate_png_summary(
    analysis_result: GaitAnalysisResponse,
    width: int = 1200,
    height: int = 800,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    PNG形式のサマリー画像を生成
    
    Args:
        analysis_result: 歩行分析結果データ
        width: 画像幅（ピクセル）
        height: 画像高さ（ピクセル）
        background_tasks: バックグラウンドタスク
        
    Returns:
        FileResponse: 生成されたPNG画像ファイル
    """
    try:
        logger.info("PNG summary generation requested", 
                   analysis_id=analysis_result.analysis_id)
        
        report_generator = ReportGenerator()
        png_path = await report_generator.generate_png_summary(
            analysis_result, size=(width, height)
        )
        
        if not os.path.exists(png_path):
            raise HTTPException(
                status_code=500, 
                detail="PNG画像の生成に失敗しました"
            )
        
        # ファイル削除をバックグラウンドタスクに追加
        background_tasks.add_task(_cleanup_file, png_path)
        
        # ファイル名を生成
        filename = f"gait_summary_{analysis_result.analysis_id[:8]}.png"
        
        return FileResponse(
            path=png_path,
            filename=filename,
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error("Failed to generate PNG summary", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"PNG画像生成エラー: {str(e)}"
        )


@router.post("/generate/base64")
async def generate_base64_image(
    analysis_result: GaitAnalysisResponse
):
    """
    Base64エンコードされた画像を生成（Web表示用）
    
    Args:
        analysis_result: 歩行分析結果データ
        
    Returns:
        JSONResponse: Base64エンコードされた画像データ
    """
    try:
        logger.info("Base64 image generation requested", 
                   analysis_id=analysis_result.analysis_id)
        
        report_generator = ReportGenerator()
        base64_data = await report_generator.generate_base64_image(analysis_result)
        
        return JSONResponse(
            content={
                "status": "success",
                "analysis_id": analysis_result.analysis_id,
                "image_data": base64_data,
                "generated_at": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Failed to generate base64 image", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Base64画像生成エラー: {str(e)}"
        )


@router.get("/templates")
async def get_report_templates():
    """
    利用可能なレポートテンプレート一覧を取得
    
    Returns:
        JSONResponse: テンプレート情報
    """
    try:
        templates = [
            {
                "id": "standard_pdf",
                "name": "標準PDFレポート",
                "description": "詳細な分析結果を含む5ページのPDFレポート",
                "format": "PDF",
                "pages": 5,
                "sections": [
                    "概要とスコア",
                    "時空間パラメータ",
                    "対称性分析",
                    "関節角度分析",
                    "改善提案"
                ]
            },
            {
                "id": "summary_png",
                "name": "サマリー画像",
                "description": "主要指標を一枚にまとめた画像レポート",
                "format": "PNG",
                "sections": [
                    "総合スコア",
                    "対称性レーダー",
                    "品質指標",
                    "歩行パラメータ",
                    "関節角度サマリー",
                    "改善提案"
                ]
            },
            {
                "id": "web_display",
                "name": "Web表示用画像",
                "description": "ブラウザ表示用のBase64エンコード画像",
                "format": "Base64",
                "sections": ["サマリー情報"]
            }
        ]
        
        return JSONResponse(
            content={
                "status": "success",
                "templates": templates,
                "total_count": len(templates)
            }
        )
        
    except Exception as e:
        logger.error("Failed to get report templates", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"テンプレート取得エラー: {str(e)}"
        )


@router.post("/generate/custom")
async def generate_custom_report(
    analysis_result: GaitAnalysisResponse,
    template_config: Dict[str, Any],
    patient_info: Optional[Dict[str, Any]] = None,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    カスタムレポートを生成
    
    Args:
        analysis_result: 歩行分析結果データ
        template_config: レポート設定
        patient_info: 患者情報（オプション）
        background_tasks: バックグラウンドタスク
        
    Returns:
        FileResponse: 生成されたレポートファイル
    """
    try:
        logger.info("Custom report generation requested", 
                   analysis_id=analysis_result.analysis_id,
                   template_config=template_config)
        
        report_generator = ReportGenerator()
        
        # テンプレート設定に基づいてレポート生成
        report_format = template_config.get("format", "pdf").lower()
        
        if report_format == "pdf":
            file_path = await report_generator.generate_pdf_report(
                analysis_result, patient_info
            )
            media_type = "application/pdf"
            extension = "pdf"
        elif report_format == "png":
            size = template_config.get("size", (1200, 800))
            file_path = await report_generator.generate_png_summary(
                analysis_result, size=size
            )
            media_type = "image/png"
            extension = "png"
        else:
            raise HTTPException(
                status_code=400,
                detail=f"サポートされていないフォーマット: {report_format}"
            )
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=500,
                detail="レポートファイルの生成に失敗しました"
            )
        
        # ファイル削除をバックグラウンドタスクに追加
        background_tasks.add_task(_cleanup_file, file_path)
        
        # ファイル名を生成
        filename = f"custom_report_{analysis_result.analysis_id[:8]}.{extension}"
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error("Failed to generate custom report", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"カスタムレポート生成エラー: {str(e)}"
        )


@router.get("/status/{analysis_id}")
async def get_report_status(analysis_id: str):
    """
    レポート生成状況を確認
    
    Args:
        analysis_id: 分析ID
        
    Returns:
        JSONResponse: レポート状況
    """
    try:
        # TODO: データベースからレポート生成履歴を取得
        # 現在は簡易的な実装
        
        return JSONResponse(
            content={
                "status": "success",
                "analysis_id": analysis_id,
                "reports_generated": [],
                "available_formats": ["pdf", "png", "base64"],
                "last_generated": None
            }
        )
        
    except Exception as e:
        logger.error("Failed to get report status", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"レポート状況取得エラー: {str(e)}"
        )


def _cleanup_file(file_path: str):
    """
    ファイルをクリーンアップ（バックグラウンドタスク用）
    
    Args:
        file_path: 削除するファイルのパス
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info("Temporary file cleaned up", file_path=file_path)
    except Exception as e:
        logger.warning("Failed to cleanup file", file_path=file_path, error=str(e))