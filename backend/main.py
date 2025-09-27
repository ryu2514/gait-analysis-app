"""
MediaPipe 動的歩行分析アプリ - メインアプリケーション
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from contextlib import asynccontextmanager

from app.api import gait_analysis, health, enhanced_gait_analysis
from app.core.config import settings
from app.core.logger_config import initialize_logging
from app.core.advanced_logger import get_logger
from app.core.performance_config import init_performance_systems

# メインアプリケーションロガー
logger = get_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    # 起動時の処理
    initialize_logging()
    init_performance_systems()
    
    # APIドキュメンテーション自動生成（軽量モードではスキップ）
    from app.core.config import settings as _settings
    if not getattr(_settings, 'LIGHT_MODE', False):
        try:
            from app.core.docs_generator import generate_api_documentation
            generated_docs = generate_api_documentation(app)
            logger.info("📚 API documentation generated", files=list(generated_docs.keys()))
            print("📚 API documentation generated automatically")
        except Exception as e:
            logger.warning("📚 API documentation generation failed", error=str(e))
            print(f"⚠️  API documentation generation failed: {e}")
    else:
        logger.info("Skipping docs generation in LIGHT_MODE")
    
    logger.info("🚀 Gait Analysis API starting up...")
    print("🚀 Gait Analysis API starting up...")
    print("📊 Performance optimization systems initialized")
    
    yield
    
    # 終了時の処理
    logger.info("🛑 Gait Analysis API shutting down...")
    print("🛑 Gait Analysis API shutting down...")


# FastAPIアプリケーション初期化
app = FastAPI(
    title="Enhanced MediaPipe Gait Analysis API",
    description="""
    ## Enhanced MediaPipe歩行分析API v2.0

    スマートフォンで撮影した動画から歩行パターンを分析し、
    理学療法士や医療従事者向けの詳細なレポートを生成する拡張APIです。

    ### 🚀 新機能（v2.0 Enhanced）
    - **30秒高速処理**: 撮影からレポート出力まで30秒以内
    - **33ランドマーク活用**: MediaPipe Pose v0.10の全機能
    - **代償動作検出**: 自動アラート機能付き
    - **重心・バランス分析**: COM軌跡とバランス安定性評価
    - **拡張出力**: 正規化波形グラフ、スローモーション動画、カラーPDFレポート
    - **iPad/iPhone最適化**: 60fps対応、横・後方撮影モード

    ### 📊 詳細分析機能
    - **スパイオテンポラル指標**: ピッチ、歩幅/ストライド長、立脚/遊脚時間、対称性指標
    - **キネマティクス**: 股関節ROM、膝関節詳細角度、足関節背屈/底屈、骨盤・体幹回旋
    - **代償動作アラート**: アウト/イントゥーイング、膝外反/内反、トレンデレンブルグ、ペルビックドロップ
    - **バランス指標**: COM水平/垂直移動幅、重心投影線2Dマップ

    ### 🎯 対象ユーザー
    - **理学療法士**: 詳細な歩行評価と治療計画立案
    - **作業療法士**: 日常生活動作の評価
    - **医師**: 診断支援と経過観察
    - **研究者**: 歩行データの定量的解析
    - **アスリート・トレーナー**: パフォーマンス向上

    ### ⚙️ 技術仕様（Enhanced）
    - **バックエンド**: FastAPI + Python 3.11+
    - **AI処理**: MediaPipe Pose v0.10 + 最高精度モデル
    - **並列処理**: マルチコア活用による高速化
    - **データベース**: PostgreSQL + Redis キャッシュ
    - **認証**: Firebase Auth + JWT
    - **監視**: リアルタイムパフォーマンス監視
    - **出力**: PDF/MP4/JSON/CSV 多形式対応
    """,
    version="2.0.0-enhanced",
    contact={
        "name": "Gait Analysis API Support",
        "url": "https://gaitanalysis.com/support",
        "email": "support@gaitanalysis.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    terms_of_service="https://gaitanalysis.com/terms",
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.gaitanalysis.com",
            "description": "Production server"
        }
    ],
    openapi_tags=[
        {
            "name": "health",
            "description": "ヘルスチェックとシステム状態監視"
        },
        {
            "name": "gait-analysis", 
            "description": "歩行分析のメイン機能"
        },
        {
            "name": "enhanced-gait-analysis",
            "description": "拡張歩行分析機能（30秒処理、代償動作検出、バランス分析）"
        },
        {
            "name": "auth",
            "description": "認証とユーザー管理"
        },
        {
            "name": "reports",
            "description": "分析レポートの生成とダウンロード"
        },
        {
            "name": "history",
            "description": "分析履歴の管理と検索"
        },
        {
            "name": "performance",
            "description": "パフォーマンス監視とシステム最適化"
        },
        {
            "name": "documentation",
            "description": "APIドキュメンテーションの管理"
        },
        {
            "name": "monitoring",
            "description": "リアルタイムシステム監視とWebSocketダッシュボード"
        }
    ],
    lifespan=lifespan
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静的ファイル配信
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# ルーター登録
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(gait_analysis.router, prefix="/api/v1/gait-analysis", tags=["gait-analysis"])
app.include_router(enhanced_gait_analysis.router, prefix="/api/v1/gait-analysis", tags=["enhanced-gait-analysis"])

# v1 APIルーター
from app.api.v1 import reports, history, auth
from app.api import performance_dashboard, documentation, monitoring_dashboard
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(history.router, prefix="/api/v1/history", tags=["history"])
app.include_router(performance_dashboard.router, prefix="/api/v1/performance", tags=["performance"])
app.include_router(documentation.router, prefix="/api/v1/docs", tags=["documentation"])
app.include_router(monitoring_dashboard.router, prefix="/api/v1/monitoring", tags=["monitoring"])


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Enhanced MediaPipe Gait Analysis API",
        "version": "2.0.0-enhanced",
        "status": "running",
        "features": {
            "30_second_processing": True,
            "33_landmarks_detection": True,
            "compensation_alerts": True,
            "balance_analysis": True,
            "enhanced_output": True,
            "parallel_processing": True
        },
        "endpoints": {
            "enhanced_analysis": "/api/v1/gait-analysis/analyze-enhanced",
            "capabilities": "/api/v1/gait-analysis/capabilities",
            "demo_data": "/api/v1/gait-analysis/demo-data",
            "health": "/api/v1/health",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
