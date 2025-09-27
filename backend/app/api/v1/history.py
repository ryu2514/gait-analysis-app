"""
履歴管理API エンドポイント
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.services.data_service import data_service
from app.database.connection import get_database_session
from app.models.gait_models import GaitAnalysisResponse
from app.core.logging import StructuredLogger

logger = StructuredLogger(__name__)
router = APIRouter()


@router.get("/analyses")
async def get_analysis_history(
    user_id: str = Query(..., description="ユーザーID"),
    limit: int = Query(20, ge=1, le=100, description="取得件数制限"),
    offset: int = Query(0, ge=0, description="オフセット"),
    start_date: Optional[str] = Query(None, description="開始日時（ISO8601形式）"),
    end_date: Optional[str] = Query(None, description="終了日時（ISO8601形式）"),
    db: Session = Depends(get_database_session)
):
    """
    ユーザーの分析履歴を取得
    
    Args:
        user_id: ユーザーID
        limit: 取得件数制限（1-100）
        offset: オフセット
        start_date: 開始日時
        end_date: 終了日時
        
    Returns:
        JSONResponse: 分析履歴リスト
    """
    try:
        # 日付パラメータの変換
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail="無効な開始日時形式です。ISO8601形式を使用してください。"
                )
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail="無効な終了日時形式です。ISO8601形式を使用してください。"
                )
        
        # 履歴取得
        history = await data_service.get_user_analysis_history(
            user_id=user_id,
            limit=limit,
            offset=offset,
            start_date=start_dt,
            end_date=end_dt
        )
        
        return JSONResponse(
            content={
                "status": "success",
                "data": {
                    "analyses": history,
                    "total_count": len(history),
                    "limit": limit,
                    "offset": offset,
                    "has_more": len(history) == limit
                }
            }
        )
        
    except Exception as e:
        logger.error("Failed to get analysis history", 
                    user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"履歴取得エラー: {str(e)}"
        )


@router.get("/analyses/{analysis_id}")
async def get_analysis_detail(
    analysis_id: str,
    user_id: str = Query(..., description="ユーザーID"),
    db: Session = Depends(get_database_session)
):
    """
    特定の分析結果の詳細を取得
    
    Args:
        analysis_id: 分析ID
        user_id: ユーザーID
        
    Returns:
        JSONResponse: 分析結果詳細
    """
    try:
        analysis_result = await data_service.get_analysis_result(
            user_id=user_id,
            analysis_id=analysis_id
        )
        
        if not analysis_result:
            raise HTTPException(
                status_code=404,
                detail="指定された分析結果が見つかりません"
            )
        
        return JSONResponse(
            content={
                "status": "success",
                "data": analysis_result.dict()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get analysis detail", 
                    analysis_id=analysis_id, 
                    user_id=user_id, 
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"分析詳細取得エラー: {str(e)}"
        )


@router.delete("/analyses/{analysis_id}")
async def delete_analysis(
    analysis_id: str,
    user_id: str = Query(..., description="ユーザーID"),
    db: Session = Depends(get_database_session)
):
    """
    分析結果を削除
    
    Args:
        analysis_id: 分析ID
        user_id: ユーザーID
        
    Returns:
        JSONResponse: 削除結果
    """
    try:
        success = await data_service.delete_analysis(
            user_id=user_id,
            analysis_id=analysis_id
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="指定された分析結果が見つかりません"
            )
        
        return JSONResponse(
            content={
                "status": "success",
                "message": "分析結果が正常に削除されました",
                "analysis_id": analysis_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete analysis", 
                    analysis_id=analysis_id, 
                    user_id=user_id, 
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"分析削除エラー: {str(e)}"
        )


@router.get("/statistics")
async def get_user_statistics(
    user_id: str = Query(..., description="ユーザーID"),
    db: Session = Depends(get_database_session)
):
    """
    ユーザーの統計情報を取得
    
    Args:
        user_id: ユーザーID
        
    Returns:
        JSONResponse: 統計情報
    """
    try:
        statistics = await data_service.get_user_statistics(user_id=user_id)
        
        return JSONResponse(
            content={
                "status": "success",
                "data": statistics
            }
        )
        
    except Exception as e:
        logger.error("Failed to get user statistics", 
                    user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"統計情報取得エラー: {str(e)}"
        )


@router.post("/analyses/{analysis_id}/save")
async def save_analysis_to_history(
    analysis_id: str,
    analysis_result: GaitAnalysisResponse,
    user_id: str = Query(..., description="ユーザーID"),
    video_info: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_database_session)
):
    """
    分析結果を履歴に保存
    
    Args:
        analysis_id: 分析ID
        user_id: ユーザーID
        analysis_result: 分析結果データ
        video_info: 動画情報
        
    Returns:
        JSONResponse: 保存結果
    """
    try:
        # 分析IDの一致確認
        if analysis_result.analysis_id != analysis_id:
            raise HTTPException(
                status_code=400,
                detail="パラメータの分析IDと結果の分析IDが一致しません"
            )
        
        # 既存の分析結果確認
        existing_analysis = await data_service.get_analysis_result(
            user_id=user_id,
            analysis_id=analysis_id
        )
        
        if existing_analysis:
            return JSONResponse(
                content={
                    "status": "success",
                    "message": "この分析結果は既に保存されています",
                    "analysis_id": analysis_id,
                    "saved_at": existing_analysis.timestamp.isoformat()
                }
            )
        
        # 新しい分析結果を保存
        saved_id = await data_service.save_analysis_result(
            user_id=user_id,
            analysis_result=analysis_result,
            video_info=video_info
        )
        
        return JSONResponse(
            content={
                "status": "success",
                "message": "分析結果が正常に保存されました",
                "analysis_id": analysis_id,
                "saved_id": saved_id,
                "saved_at": analysis_result.timestamp.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to save analysis to history", 
                    analysis_id=analysis_id, 
                    user_id=user_id, 
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"履歴保存エラー: {str(e)}"
        )


@router.get("/analyses/{analysis_id}/compare")
async def compare_with_previous(
    analysis_id: str,
    user_id: str = Query(..., description="ユーザーID"),
    compare_with: Optional[str] = Query(None, description="比較対象の分析ID"),
    db: Session = Depends(get_database_session)
):
    """
    過去の分析結果と比較
    
    Args:
        analysis_id: 現在の分析ID
        user_id: ユーザーID
        compare_with: 比較対象の分析ID（未指定の場合は直前の分析）
        
    Returns:
        JSONResponse: 比較結果
    """
    try:
        # 現在の分析結果取得
        current_analysis = await data_service.get_analysis_result(
            user_id=user_id,
            analysis_id=analysis_id
        )
        
        if not current_analysis:
            raise HTTPException(
                status_code=404,
                detail="指定された分析結果が見つかりません"
            )
        
        # 比較対象取得
        if compare_with:
            previous_analysis = await data_service.get_analysis_result(
                user_id=user_id,
                analysis_id=compare_with
            )
        else:
            # 直前の分析を取得
            history = await data_service.get_user_analysis_history(
                user_id=user_id,
                limit=2
            )
            
            previous_analysis = None
            for h in history:
                if h['analysis_id'] != analysis_id:
                    previous_analysis = await data_service.get_analysis_result(
                        user_id=user_id,
                        analysis_id=h['analysis_id']
                    )
                    break
        
        if not previous_analysis:
            return JSONResponse(
                content={
                    "status": "success",
                    "message": "比較対象の分析結果がありません",
                    "comparison": None
                }
            )
        
        # 比較データ生成
        comparison = _generate_comparison_data(current_analysis, previous_analysis)
        
        return JSONResponse(
            content={
                "status": "success",
                "data": {
                    "current_analysis": {
                        "analysis_id": current_analysis.analysis_id,
                        "timestamp": current_analysis.timestamp.isoformat(),
                        "overall_score": current_analysis.overall_gait_score
                    },
                    "previous_analysis": {
                        "analysis_id": previous_analysis.analysis_id,
                        "timestamp": previous_analysis.timestamp.isoformat(),
                        "overall_score": previous_analysis.overall_gait_score
                    },
                    "comparison": comparison
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to compare analyses", 
                    analysis_id=analysis_id, 
                    user_id=user_id, 
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"比較処理エラー: {str(e)}"
        )


def _generate_comparison_data(
    current: GaitAnalysisResponse, 
    previous: GaitAnalysisResponse
) -> Dict[str, Any]:
    """分析結果の比較データを生成"""
    comparison = {
        "overall_score_change": 0,
        "spatiotemporal_changes": {},
        "symmetry_changes": {},
        "recommendations_comparison": {
            "current": current.recommendations,
            "previous": previous.recommendations,
            "new_recommendations": [],
            "resolved_issues": []
        }
    }
    
    # 総合スコア比較
    if current.overall_gait_score and previous.overall_gait_score:
        comparison["overall_score_change"] = current.overall_gait_score - previous.overall_gait_score
    
    # 時空間パラメータ比較
    if current.spatiotemporal_params and previous.spatiotemporal_params:
        current_params = current.spatiotemporal_params
        previous_params = previous.spatiotemporal_params
        
        comparison["spatiotemporal_changes"] = {
            "gait_speed_change": current_params.gait_speed_ms - previous_params.gait_speed_ms,
            "cadence_change": current_params.cadence_steps_per_min - previous_params.cadence_steps_per_min,
            "stride_length_change": current_params.stride_length_m - previous_params.stride_length_m
        }
    
    # 対称性比較
    if current.symmetry_indices and previous.symmetry_indices:
        current_symmetry = current.symmetry_indices
        previous_symmetry = previous.symmetry_indices
        
        comparison["symmetry_changes"] = {
            "overall_symmetry_change": current_symmetry.overall_symmetry_score - previous_symmetry.overall_symmetry_score,
            "step_length_symmetry_change": current_symmetry.step_length_symmetry_percent - previous_symmetry.step_length_symmetry_percent,
            "stance_time_symmetry_change": current_symmetry.stance_time_symmetry_percent - previous_symmetry.stance_time_symmetry_percent
        }
    
    # 推奨事項比較
    current_recs = set(current.recommendations)
    previous_recs = set(previous.recommendations)
    
    comparison["recommendations_comparison"]["new_recommendations"] = list(current_recs - previous_recs)
    comparison["recommendations_comparison"]["resolved_issues"] = list(previous_recs - current_recs)
    
    return comparison