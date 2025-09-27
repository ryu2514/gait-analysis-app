"""
API Documentation Endpoints
APIドキュメンテーションエンドポイント
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from typing import Dict, Any
from pathlib import Path
import json

from app.core.docs_generator import generate_api_documentation
from app.core.advanced_logger import get_logger
from app.core.auth import get_current_user
from app.models.user_models import UserResponse

router = APIRouter()
logger = get_logger("documentation")


@router.get("/openapi.json")
async def get_openapi_json():
    """OpenAPI仕様書をJSON形式で取得"""
    try:
        docs_dir = Path("docs")
        json_path = docs_dir / "openapi.json"
        
        if not json_path.exists():
            raise HTTPException(status_code=404, detail="OpenAPI JSON not found")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            openapi_spec = json.load(f)
        
        return JSONResponse(content=openapi_spec)
        
    except Exception as e:
        logger.error("Failed to get OpenAPI JSON", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve OpenAPI specification")


@router.get("/openapi.yaml")
async def get_openapi_yaml():
    """OpenAPI仕様書をYAML形式で取得"""
    try:
        docs_dir = Path("docs")
        yaml_path = docs_dir / "openapi.yaml"
        
        if not yaml_path.exists():
            raise HTTPException(status_code=404, detail="OpenAPI YAML not found")
        
        return FileResponse(
            path=yaml_path,
            media_type="application/x-yaml",
            filename="openapi.yaml"
        )
        
    except Exception as e:
        logger.error("Failed to get OpenAPI YAML", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve OpenAPI YAML")


@router.get("/markdown")
async def get_markdown_documentation():
    """マークダウン形式のAPIドキュメントを取得"""
    try:
        docs_dir = Path("docs")
        md_path = docs_dir / "API_DOCUMENTATION.md"
        
        if not md_path.exists():
            raise HTTPException(status_code=404, detail="Markdown documentation not found")
        
        return FileResponse(
            path=md_path,
            media_type="text/markdown",
            filename="API_DOCUMENTATION.md"
        )
        
    except Exception as e:
        logger.error("Failed to get Markdown documentation", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve Markdown documentation")


@router.get("/postman")
async def get_postman_collection():
    """Postmanコレクションを取得"""
    try:
        docs_dir = Path("docs")
        postman_path = docs_dir / "postman_collection.json"
        
        if not postman_path.exists():
            raise HTTPException(status_code=404, detail="Postman collection not found")
        
        return FileResponse(
            path=postman_path,
            media_type="application/json",
            filename="gait_analysis_api.postman_collection.json"
        )
        
    except Exception as e:
        logger.error("Failed to get Postman collection", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve Postman collection")


@router.post("/generate")
async def regenerate_documentation(
    current_user: UserResponse = Depends(get_current_user)
):
    """APIドキュメンテーションを再生成"""
    # 管理者権限チェック
    if current_user.user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    try:
        from main import app  # メインアプリケーションをインポート
        
        logger.info("Regenerating API documentation", user_id=current_user.id)
        
        # ドキュメンテーション生成
        generated_files = generate_api_documentation(app)
        
        result = {
            "message": "Documentation regenerated successfully",
            "generated_files": {
                name: str(path) for name, path in generated_files.items()
            },
            "endpoints": {
                "openapi_json": "/api/v1/docs/openapi.json",
                "openapi_yaml": "/api/v1/docs/openapi.yaml",
                "markdown": "/api/v1/docs/markdown",
                "postman": "/api/v1/docs/postman"
            }
        }
        
        logger.info("Documentation regeneration completed", 
                   files_generated=len(generated_files))
        
        return result
        
    except Exception as e:
        logger.error("Documentation regeneration failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to regenerate documentation")


@router.get("/info")
async def get_documentation_info():
    """ドキュメンテーション情報を取得"""
    try:
        docs_dir = Path("docs")
        
        # 各ファイルの存在確認
        files_status = {}
        file_checks = {
            "openapi_json": "openapi.json",
            "openapi_yaml": "openapi.yaml", 
            "markdown": "API_DOCUMENTATION.md",
            "postman": "postman_collection.json"
        }
        
        for key, filename in file_checks.items():
            file_path = docs_dir / filename
            files_status[key] = {
                "exists": file_path.exists(),
                "path": str(file_path),
                "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
                "last_modified": file_path.stat().st_mtime if file_path.exists() else None
            }
        
        return {
            "documentation_directory": str(docs_dir),
            "files": files_status,
            "available_endpoints": {
                "openapi_json": "/api/v1/docs/openapi.json",
                "openapi_yaml": "/api/v1/docs/openapi.yaml",
                "markdown": "/api/v1/docs/markdown",
                "postman": "/api/v1/docs/postman",
                "regenerate": "/api/v1/docs/generate (POST, Admin only)"
            },
            "external_docs": {
                "swagger_ui": "/docs",
                "redoc": "/redoc"
            }
        }
        
    except Exception as e:
        logger.error("Failed to get documentation info", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve documentation information")