#!/usr/bin/env python3
"""
Documentation Generation Script
ドキュメンテーション生成スクリプト
"""

import sys
import asyncio
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from main import app
from app.core.docs_generator import generate_api_documentation
from app.core.advanced_logger import get_logger

logger = get_logger("docs_generation")


async def main():
    """ドキュメンテーション生成メイン処理"""
    try:
        print("🚀 Starting API Documentation Generation")
        print("=" * 50)
        
        # ドキュメンテーション生成
        logger.info("Starting API documentation generation...")
        generated_files = generate_api_documentation(app)
        
        print("\n✅ Documentation Generated Successfully!")
        print("\n📁 Generated Files:")
        
        for doc_type, file_path in generated_files.items():
            file_size = file_path.stat().st_size if file_path.exists() else 0
            print(f"   📄 {doc_type}: {file_path} ({file_size:,} bytes)")
        
        print("\n🌐 Available Endpoints:")
        print("   • OpenAPI JSON: /api/v1/docs/openapi.json")
        print("   • OpenAPI YAML: /api/v1/docs/openapi.yaml")
        print("   • Markdown Docs: /api/v1/docs/markdown")
        print("   • Postman Collection: /api/v1/docs/postman")
        print("   • Documentation Info: /api/v1/docs/info")
        print("   • Regenerate (Admin): /api/v1/docs/generate")
        
        print("\n🔗 Interactive Documentation:")
        print("   • Swagger UI: http://localhost:8000/docs")
        print("   • ReDoc: http://localhost:8000/redoc")
        
        print("\n📊 Documentation Statistics:")
        
        # OpenAPI仕様書の統計
        openapi_path = generated_files.get("openapi_json")
        if openapi_path and openapi_path.exists():
            import json
            with open(openapi_path, 'r', encoding='utf-8') as f:
                openapi_spec = json.load(f)
            
            paths = openapi_spec.get("paths", {})
            total_endpoints = sum(len(methods) for methods in paths.values())
            total_paths = len(paths)
            
            print(f"   • Total API Paths: {total_paths}")
            print(f"   • Total Endpoints: {total_endpoints}")
            
            # タグ別の統計
            tags_count = {}
            for path_methods in paths.values():
                for method_details in path_methods.values():
                    tags = method_details.get("tags", ["Untagged"])
                    for tag in tags:
                        tags_count[tag] = tags_count.get(tag, 0) + 1
            
            print(f"   • API Groups: {len(tags_count)}")
            for tag, count in sorted(tags_count.items()):
                print(f"     - {tag}: {count} endpoints")
        
        # マークダウンドキュメントの統計
        markdown_path = generated_files.get("markdown")
        if markdown_path and markdown_path.exists():
            with open(markdown_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            lines = len(markdown_content.split('\n'))
            words = len(markdown_content.split())
            chars = len(markdown_content)
            
            print(f"   • Markdown Documentation:")
            print(f"     - Lines: {lines:,}")
            print(f"     - Words: {words:,}")
            print(f"     - Characters: {chars:,}")
        
        print("\n🎯 Next Steps:")
        print("   1. Start the API server: uvicorn main:app --reload")
        print("   2. Access Swagger UI: http://localhost:8000/docs")
        print("   3. Download Postman collection: /api/v1/docs/postman")
        print("   4. View markdown docs: /api/v1/docs/markdown")
        
        print("\n🎉 Documentation generation completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"Documentation generation failed: {e}")
        print(f"\n❌ Documentation generation failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)