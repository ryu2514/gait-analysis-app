"""
データ管理サービス
分析結果の保存・取得・履歴管理
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
import json
import hashlib

from app.models.database_models import (
    User, GaitAnalysis, AnalysisReport, AnalysisSession, 
    PatientProfile, UserPreferences, AuditLog
)
from app.models.gait_models import GaitAnalysisResponse
from app.database.connection import db_manager
from app.core.logging import StructuredLogger

logger = StructuredLogger(__name__)


class DataService:
    """データ管理サービス"""
    
    def __init__(self):
        self.db_manager = db_manager
    
    async def save_analysis_result(
        self, 
        user_id: str, 
        analysis_result: GaitAnalysisResponse,
        video_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        分析結果をデータベースに保存
        
        Args:
            user_id: ユーザーID
            analysis_result: 分析結果
            video_info: 動画情報
            
        Returns:
            str: 保存された分析のID
        """
        try:
            async with self.db_manager.get_async_session() as session:
                # GaitAnalysisレコード作成
                gait_analysis = GaitAnalysis(
                    user_id=user_id,
                    analysis_id=analysis_result.analysis_id,
                    analysis_date=analysis_result.timestamp,
                    processing_time_seconds=analysis_result.processing_time_seconds,
                    analysis_mode=analysis_result.analysis_settings.get('analysis_mode', 'standard'),
                    
                    # 動画情報
                    video_filename=video_info.get('filename') if video_info else None,
                    video_duration_seconds=video_info.get('duration_seconds') if video_info else None,
                    video_resolution=video_info.get('resolution') if video_info else None,
                    video_fps=video_info.get('fps') if video_info else None,
                    video_quality_score=analysis_result.video_quality_score,
                    
                    # 分析設定
                    user_height_cm=analysis_result.analysis_settings.get('user_height_cm'),
                    scale_factor=analysis_result.analysis_settings.get('scale_factor'),
                    model_complexity=analysis_result.analysis_settings.get('model_complexity'),
                    
                    # 品質指標
                    pose_detection_confidence=analysis_result.pose_detection_confidence,
                    gait_cycles_detected=analysis_result.gait_cycles_detected,
                    
                    # スコア
                    overall_gait_score=analysis_result.overall_gait_score,
                    
                    # JSON形式で保存
                    spatiotemporal_params=analysis_result.spatiotemporal_params.dict() if analysis_result.spatiotemporal_params else None,
                    symmetry_indices=analysis_result.symmetry_indices.dict() if analysis_result.symmetry_indices else None,
                    joint_angles=analysis_result.joint_angles.dict() if analysis_result.joint_angles else None,
                    gait_cycles=[cycle.dict() for cycle in analysis_result.gait_cycles],
                    recommendations=analysis_result.recommendations
                )
                
                session.add(gait_analysis)
                await session.flush()  # IDを取得するためflush
                
                # 監査ログ記録
                await self._log_action(
                    session, user_id, "create", "gait_analysis", 
                    gait_analysis.id, {"analysis_id": analysis_result.analysis_id}
                )
                
                logger.info("Analysis result saved", 
                           user_id=user_id, 
                           analysis_id=analysis_result.analysis_id)
                
                return gait_analysis.id
                
        except Exception as e:
            logger.error("Failed to save analysis result", 
                        user_id=user_id, 
                        analysis_id=analysis_result.analysis_id, 
                        error=str(e))
            raise
    
    async def get_analysis_result(
        self, 
        user_id: str, 
        analysis_id: str
    ) -> Optional[GaitAnalysisResponse]:
        """
        分析結果を取得
        
        Args:
            user_id: ユーザーID
            analysis_id: 分析ID
            
        Returns:
            GaitAnalysisResponse: 分析結果（存在しない場合はNone）
        """
        try:
            async with self.db_manager.get_async_session() as session:
                gait_analysis = session.query(GaitAnalysis).filter(
                    and_(
                        GaitAnalysis.user_id == user_id,
                        GaitAnalysis.analysis_id == analysis_id
                    )
                ).first()
                
                if not gait_analysis:
                    return None
                
                # データベースのデータをGaitAnalysisResponseに変換
                return self._convert_to_response(gait_analysis)
                
        except Exception as e:
            logger.error("Failed to get analysis result", 
                        user_id=user_id, 
                        analysis_id=analysis_id, 
                        error=str(e))
            raise
    
    async def get_user_analysis_history(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        ユーザーの分析履歴を取得
        
        Args:
            user_id: ユーザーID
            limit: 取得件数制限
            offset: オフセット
            start_date: 開始日時
            end_date: 終了日時
            
        Returns:
            List[Dict]: 分析履歴のリスト
        """
        try:
            async with self.db_manager.get_async_session() as session:
                query = session.query(GaitAnalysis).filter(GaitAnalysis.user_id == user_id)
                
                # 日付フィルタ
                if start_date:
                    query = query.filter(GaitAnalysis.analysis_date >= start_date)
                if end_date:
                    query = query.filter(GaitAnalysis.analysis_date <= end_date)
                
                # 並び順とページング
                analyses = query.order_by(desc(GaitAnalysis.analysis_date)).offset(offset).limit(limit).all()
                
                # 履歴リストに変換
                history = []
                for analysis in analyses:
                    history.append({
                        'id': analysis.id,
                        'analysis_id': analysis.analysis_id,
                        'analysis_date': analysis.analysis_date.isoformat(),
                        'overall_gait_score': analysis.overall_gait_score,
                        'video_quality_score': analysis.video_quality_score,
                        'gait_cycles_detected': analysis.gait_cycles_detected,
                        'analysis_mode': analysis.analysis_mode,
                        'processing_time_seconds': analysis.processing_time_seconds,
                        'has_reports': len(analysis.reports) > 0
                    })
                
                logger.info("Analysis history retrieved", 
                           user_id=user_id, 
                           count=len(history))
                
                return history
                
        except Exception as e:
            logger.error("Failed to get analysis history", 
                        user_id=user_id, 
                        error=str(e))
            raise
    
    async def delete_analysis(self, user_id: str, analysis_id: str) -> bool:
        """
        分析結果を削除
        
        Args:
            user_id: ユーザーID
            analysis_id: 分析ID
            
        Returns:
            bool: 削除成功かどうか
        """
        try:
            async with self.db_manager.get_async_session() as session:
                gait_analysis = session.query(GaitAnalysis).filter(
                    and_(
                        GaitAnalysis.user_id == user_id,
                        GaitAnalysis.analysis_id == analysis_id
                    )
                ).first()
                
                if not gait_analysis:
                    return False
                
                # 関連ファイルの削除（実装必要）
                # await self._cleanup_analysis_files(gait_analysis)
                
                # 監査ログ記録
                await self._log_action(
                    session, user_id, "delete", "gait_analysis", 
                    gait_analysis.id, {"analysis_id": analysis_id}
                )
                
                # データベースから削除
                session.delete(gait_analysis)
                
                logger.info("Analysis deleted", 
                           user_id=user_id, 
                           analysis_id=analysis_id)
                
                return True
                
        except Exception as e:
            logger.error("Failed to delete analysis", 
                        user_id=user_id, 
                        analysis_id=analysis_id, 
                        error=str(e))
            raise
    
    async def save_analysis_report(
        self,
        gait_analysis_id: str,
        report_type: str,
        file_path: str,
        file_size: int,
        generation_settings: Optional[Dict[str, Any]] = None,
        patient_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成されたレポートを保存
        
        Args:
            gait_analysis_id: 歩行分析ID
            report_type: レポートタイプ
            file_path: ファイルパス
            file_size: ファイルサイズ
            generation_settings: 生成設定
            patient_info: 患者情報
            
        Returns:
            str: レポートID
        """
        try:
            async with self.db_manager.get_async_session() as session:
                # ファイルハッシュ計算
                file_hash = await self._calculate_file_hash(file_path)
                
                report = AnalysisReport(
                    gait_analysis_id=gait_analysis_id,
                    report_type=report_type,
                    report_format=report_type.upper(),
                    file_path=file_path,
                    file_size_bytes=file_size,
                    file_hash=file_hash,
                    generation_settings=generation_settings,
                    patient_info=patient_info
                )
                
                session.add(report)
                await session.flush()
                
                logger.info("Analysis report saved", 
                           gait_analysis_id=gait_analysis_id,
                           report_id=report.id,
                           report_type=report_type)
                
                return report.id
                
        except Exception as e:
            logger.error("Failed to save analysis report", 
                        gait_analysis_id=gait_analysis_id,
                        error=str(e))
            raise
    
    async def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        ユーザーの統計情報を取得
        
        Args:
            user_id: ユーザーID
            
        Returns:
            Dict: 統計情報
        """
        try:
            async with self.db_manager.get_async_session() as session:
                # 基本統計
                total_analyses = session.query(GaitAnalysis).filter(GaitAnalysis.user_id == user_id).count()
                
                # 今月の分析数
                current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                this_month_analyses = session.query(GaitAnalysis).filter(
                    and_(
                        GaitAnalysis.user_id == user_id,
                        GaitAnalysis.analysis_date >= current_month_start
                    )
                ).count()
                
                # 平均スコア
                avg_score_result = session.query(GaitAnalysis.overall_gait_score).filter(
                    GaitAnalysis.user_id == user_id
                ).all()
                avg_score = sum(score[0] for score in avg_score_result if score[0]) / len(avg_score_result) if avg_score_result else 0
                
                # 最新分析
                latest_analysis = session.query(GaitAnalysis).filter(
                    GaitAnalysis.user_id == user_id
                ).order_by(desc(GaitAnalysis.analysis_date)).first()
                
                # 傾向分析（直近10回）
                recent_analyses = session.query(GaitAnalysis).filter(
                    GaitAnalysis.user_id == user_id
                ).order_by(desc(GaitAnalysis.analysis_date)).limit(10).all()
                
                trend_data = []
                for analysis in reversed(recent_analyses):
                    if analysis.overall_gait_score:
                        trend_data.append({
                            'date': analysis.analysis_date.isoformat(),
                            'score': analysis.overall_gait_score
                        })
                
                statistics = {
                    'total_analyses': total_analyses,
                    'this_month_analyses': this_month_analyses,
                    'average_score': round(avg_score, 1),
                    'latest_analysis_date': latest_analysis.analysis_date.isoformat() if latest_analysis else None,
                    'latest_score': latest_analysis.overall_gait_score if latest_analysis else None,
                    'score_trend': trend_data
                }
                
                return statistics
                
        except Exception as e:
            logger.error("Failed to get user statistics", 
                        user_id=user_id, 
                        error=str(e))
            raise
    
    async def cleanup_old_data(self, days_to_keep: int = 365) -> int:
        """
        古いデータのクリーンアップ
        
        Args:
            days_to_keep: 保持日数
            
        Returns:
            int: 削除された件数
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_count = 0
            
            async with self.db_manager.get_async_session() as session:
                # 古い分析結果を取得
                old_analyses = session.query(GaitAnalysis).filter(
                    GaitAnalysis.analysis_date < cutoff_date
                ).all()
                
                for analysis in old_analyses:
                    # 関連ファイルの削除
                    # await self._cleanup_analysis_files(analysis)
                    
                    # データベースから削除
                    session.delete(analysis)
                    deleted_count += 1
                
                logger.info("Old data cleanup completed", 
                           deleted_count=deleted_count,
                           cutoff_date=cutoff_date.isoformat())
                
                return deleted_count
                
        except Exception as e:
            logger.error("Failed to cleanup old data", error=str(e))
            raise
    
    def _convert_to_response(self, gait_analysis: GaitAnalysis) -> GaitAnalysisResponse:
        """データベースレコードをレスポンスモデルに変換"""
        from app.models.gait_models import (
            SpatiotemporalParameters, SymmetryIndices, 
            JointAngles, GaitCycle
        )
        
        # JSON データを復元
        spatiotemporal_params = None
        if gait_analysis.spatiotemporal_params:
            spatiotemporal_params = SpatiotemporalParameters(**gait_analysis.spatiotemporal_params)
        
        symmetry_indices = None
        if gait_analysis.symmetry_indices:
            symmetry_indices = SymmetryIndices(**gait_analysis.symmetry_indices)
        
        joint_angles = None
        if gait_analysis.joint_angles:
            joint_angles = JointAngles(**gait_analysis.joint_angles)
        
        gait_cycles = []
        if gait_analysis.gait_cycles:
            gait_cycles = [GaitCycle(**cycle_data) for cycle_data in gait_analysis.gait_cycles]
        
        return GaitAnalysisResponse(
            analysis_id=gait_analysis.analysis_id,
            timestamp=gait_analysis.analysis_date,
            processing_time_seconds=gait_analysis.processing_time_seconds,
            spatiotemporal_params=spatiotemporal_params,
            symmetry_indices=symmetry_indices,
            gait_cycles=gait_cycles,
            joint_angles=joint_angles,
            video_quality_score=gait_analysis.video_quality_score,
            pose_detection_confidence=gait_analysis.pose_detection_confidence,
            gait_cycles_detected=gait_analysis.gait_cycles_detected,
            overall_gait_score=gait_analysis.overall_gait_score,
            recommendations=gait_analysis.recommendations or [],
            video_info={
                'duration_seconds': gait_analysis.video_duration_seconds,
                'resolution': gait_analysis.video_resolution,
                'fps': gait_analysis.video_fps
            },
            analysis_settings={
                'analysis_mode': gait_analysis.analysis_mode,
                'user_height_cm': gait_analysis.user_height_cm,
                'scale_factor': gait_analysis.scale_factor,
                'model_complexity': gait_analysis.model_complexity
            }
        )
    
    async def _log_action(
        self, 
        session: Session, 
        user_id: str, 
        action: str, 
        resource_type: str, 
        resource_id: str, 
        details: Dict[str, Any]
    ):
        """監査ログ記録"""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            success=True
        )
        session.add(audit_log)
    
    async def _calculate_file_hash(self, file_path: str) -> str:
        """ファイルハッシュ計算"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except FileNotFoundError:
            return ""


# グローバルデータサービス
data_service = DataService()