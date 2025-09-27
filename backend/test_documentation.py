#!/usr/bin/env python3
"""
Documentation Testing Script
ドキュメンテーションテストスクリプト
"""

import asyncio
import json
import yaml
import sys
from pathlib import Path
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from main import app
from app.core.docs_generator import APIDocumentationGenerator
from app.core.advanced_logger import get_logger

logger = get_logger("docs_test")


async def test_openapi_generation():
    """OpenAPI仕様書生成のテスト"""
    logger.info("Testing OpenAPI specification generation...")
    
    try:
        generator = APIDocumentationGenerator(app)
        openapi_schema = generator.generate_openapi_spec()
        
        # 基本構造のチェック
        required_keys = ["openapi", "info", "paths", "components"]
        for key in required_keys:
            if key not in openapi_schema:
                logger.error(f"Missing required key in OpenAPI schema: {key}")
                return False
        
        # info セクションのチェック
        info = openapi_schema.get("info", {})
        if not info.get("title") or not info.get("version"):
            logger.error("Missing title or version in OpenAPI info")
            return False
        
        # paths セクションのチェック
        paths = openapi_schema.get("paths", {})
        if len(paths) == 0:
            logger.error("No paths found in OpenAPI schema")
            return False
        
        logger.info(f"OpenAPI schema validation: PASSED (found {len(paths)} paths)")
        return True
        
    except Exception as e:
        logger.error(f"OpenAPI generation test failed: {e}")
        return False


async def test_file_generation():
    """ファイル生成のテスト"""
    logger.info("Testing file generation...")
    
    try:
        generator = APIDocumentationGenerator(app)
        generated_files = generator.generate_all_documentation()
        
        expected_files = ["openapi_json", "openapi_yaml", "markdown", "postman"]
        
        for file_type in expected_files:
            if file_type not in generated_files:
                logger.error(f"Missing generated file: {file_type}")
                return False
            
            file_path = generated_files[file_type]
            if not file_path.exists():
                logger.error(f"Generated file does not exist: {file_path}")
                return False
            
            if file_path.stat().st_size == 0:
                logger.error(f"Generated file is empty: {file_path}")
                return False
        
        logger.info(f"File generation test: PASSED (generated {len(generated_files)} files)")
        return True
        
    except Exception as e:
        logger.error(f"File generation test failed: {e}")
        return False


async def test_json_validity():
    """JSON形式の妥当性テスト"""
    logger.info("Testing JSON validity...")
    
    try:
        docs_dir = Path("docs")
        json_files = [
            docs_dir / "openapi.json",
            docs_dir / "postman_collection.json"
        ]
        
        for json_file in json_files:
            if not json_file.exists():
                logger.error(f"JSON file not found: {json_file}")
                return False
            
            with open(json_file, 'r', encoding='utf-8') as f:
                try:
                    json.load(f)
                    logger.debug(f"Valid JSON: {json_file.name}")
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in {json_file}: {e}")
                    return False
        
        logger.info("JSON validity test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"JSON validity test failed: {e}")
        return False


async def test_yaml_validity():
    """YAML形式の妥当性テスト"""
    logger.info("Testing YAML validity...")
    
    try:
        docs_dir = Path("docs")
        yaml_file = docs_dir / "openapi.yaml"
        
        if not yaml_file.exists():
            logger.error(f"YAML file not found: {yaml_file}")
            return False
        
        with open(yaml_file, 'r', encoding='utf-8') as f:
            try:
                yaml.safe_load(f)
                logger.debug(f"Valid YAML: {yaml_file.name}")
            except yaml.YAMLError as e:
                logger.error(f"Invalid YAML in {yaml_file}: {e}")
                return False
        
        logger.info("YAML validity test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"YAML validity test failed: {e}")
        return False


async def test_markdown_content():
    """マークダウンコンテンツのテスト"""
    logger.info("Testing Markdown content...")
    
    try:
        docs_dir = Path("docs")
        md_file = docs_dir / "API_DOCUMENTATION.md"
        
        if not md_file.exists():
            logger.error(f"Markdown file not found: {md_file}")
            return False
        
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 基本的なマークダウン構造をチェック
        required_sections = [
            "# MediaPipe Gait Analysis API",
            "## Description",
            "## Authentication", 
            "## API Endpoints",
            "## Data Models",
            "## Error Codes"
        ]
        
        for section in required_sections:
            if section not in content:
                logger.warning(f"Missing section in Markdown: {section}")
        
        # コンテンツの基本統計
        lines = len(content.split('\n'))
        words = len(content.split())
        
        if lines < 50:
            logger.warning(f"Markdown content seems too short: {lines} lines")
        
        if words < 500:
            logger.warning(f"Markdown content seems too brief: {words} words")
        
        logger.info(f"Markdown content test: PASSED ({lines} lines, {words} words)")
        return True
        
    except Exception as e:
        logger.error(f"Markdown content test failed: {e}")
        return False


async def test_postman_collection():
    """Postmanコレクションのテスト"""
    logger.info("Testing Postman collection...")
    
    try:
        docs_dir = Path("docs")
        postman_file = docs_dir / "postman_collection.json"
        
        if not postman_file.exists():
            logger.error(f"Postman collection not found: {postman_file}")
            return False
        
        with open(postman_file, 'r', encoding='utf-8') as f:
            collection = json.load(f)
        
        # Postmanコレクションの基本構造をチェック
        if "info" not in collection:
            logger.error("Missing 'info' in Postman collection")
            return False
        
        if "item" not in collection:
            logger.error("Missing 'item' in Postman collection")
            return False
        
        items = collection.get("item", [])
        if len(items) == 0:
            logger.error("No items in Postman collection")
            return False
        
        # 各アイテムの基本構造をチェック
        for item in items[:5]:  # 最初の5つをチェック
            if "name" not in item or "request" not in item:
                logger.error("Invalid item structure in Postman collection")
                return False
        
        logger.info(f"Postman collection test: PASSED ({len(items)} items)")
        return True
        
    except Exception as e:
        logger.error(f"Postman collection test failed: {e}")
        return False


async def test_documentation_completeness():
    """ドキュメンテーション完全性のテスト"""
    logger.info("Testing documentation completeness...")
    
    try:
        # アプリケーションのルートをチェック
        api_routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                for method in route.methods:
                    if method != 'HEAD':  # HEADメソッドは除外
                        api_routes.append(f"{method} {route.path}")
        
        if len(api_routes) == 0:
            logger.error("No API routes found in application")
            return False
        
        # OpenAPI仕様書と比較
        generator = APIDocumentationGenerator(app)
        openapi_schema = generator.generate_openapi_spec()
        
        documented_endpoints = []
        paths = openapi_schema.get("paths", {})
        for path, methods in paths.items():
            for method in methods.keys():
                documented_endpoints.append(f"{method.upper()} {path}")
        
        # カバレッジ計算
        coverage_ratio = len(documented_endpoints) / len(api_routes) if api_routes else 0
        
        logger.info(f"Documentation coverage: {coverage_ratio:.2%}")
        logger.info(f"Total routes: {len(api_routes)}")
        logger.info(f"Documented endpoints: {len(documented_endpoints)}")
        
        if coverage_ratio < 0.8:
            logger.warning(f"Low documentation coverage: {coverage_ratio:.2%}")
        
        logger.info("Documentation completeness test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"Documentation completeness test failed: {e}")
        return False


async def run_all_tests():
    """すべてのテストを実行"""
    logger.info("🧪 Starting comprehensive documentation tests...")
    
    test_results = {}
    
    tests = [
        ("OpenAPI Generation", test_openapi_generation),
        ("File Generation", test_file_generation),
        ("JSON Validity", test_json_validity),
        ("YAML Validity", test_yaml_validity),
        ("Markdown Content", test_markdown_content),
        ("Postman Collection", test_postman_collection),
        ("Documentation Completeness", test_documentation_completeness)
    ]
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            test_results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {test_name}: {status}")
        except Exception as e:
            test_results[test_name] = False
            print(f"   {test_name}: ❌ ERROR - {e}")
    
    # 結果集計
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"\n📊 Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All documentation tests passed!")
        return True
    else:
        print(f"⚠️  {total_tests - passed_tests} tests failed")
        return False


async def main():
    """メイン実行"""
    try:
        print("🧪 Documentation System Testing")
        print("=" * 50)
        
        success = await run_all_tests()
        
        if success:
            print("\n✅ Documentation system is working correctly!")
            print("\nGenerated documentation files:")
            docs_dir = Path("docs")
            if docs_dir.exists():
                for file_path in docs_dir.glob("*"):
                    if file_path.is_file():
                        size = file_path.stat().st_size
                        print(f"   📄 {file_path.name} ({size:,} bytes)")
        
        return success
        
    except Exception as e:
        logger.error(f"Documentation testing failed: {e}")
        print(f"\n💥 Testing failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)