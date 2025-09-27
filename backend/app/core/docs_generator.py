"""
API Documentation Generator
APIドキュメンテーション自動生成
"""

import json
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import inspect
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute

from app.core.advanced_logger import get_logger

logger = get_logger("docs_generator")


class APIDocumentationGenerator:
    """API ドキュメンテーション自動生成クラス"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.docs_dir = Path("docs")
        self.docs_dir.mkdir(exist_ok=True)
        
    def generate_openapi_spec(self) -> Dict[str, Any]:
        """OpenAPI仕様書を生成"""
        logger.info("Generating OpenAPI specification...")
        
        openapi_schema = get_openapi(
            title=self.app.title,
            version=self.app.version,
            description=self.app.description,
            routes=self.app.routes,
        )
        
        # カスタム拡張を追加
        openapi_schema["info"]["contact"] = {
            "name": "Gait Analysis API Support",
            "email": "support@gaitanalysis.com"
        }
        
        openapi_schema["info"]["license"] = {
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT"
        }
        
        # サーバー情報を追加
        openapi_schema["servers"] = [
            {
                "url": "http://localhost:8000",
                "description": "Development server"
            },
            {
                "url": "https://api.gaitanalysis.com",
                "description": "Production server"
            }
        ]
        
        # セキュリティスキームを追加
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            },
            "FirebaseAuth": {
                "type": "oauth2",
                "flows": {
                    "implicit": {
                        "authorizationUrl": "https://accounts.google.com/o/oauth2/auth",
                        "scopes": {
                            "openid": "OpenID Connect",
                            "email": "Email access",
                            "profile": "Profile access"
                        }
                    }
                }
            }
        }
        
        return openapi_schema
    
    def save_openapi_json(self, openapi_schema: Dict[str, Any]) -> Path:
        """OpenAPI仕様をJSONファイルとして保存"""
        json_path = self.docs_dir / "openapi.json"
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
        
        logger.info(f"OpenAPI JSON saved to {json_path}")
        return json_path
    
    def save_openapi_yaml(self, openapi_schema: Dict[str, Any]) -> Path:
        """OpenAPI仕様をYAMLファイルとして保存"""
        yaml_path = self.docs_dir / "openapi.yaml"
        
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(openapi_schema, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"OpenAPI YAML saved to {yaml_path}")
        return yaml_path
    
    def generate_markdown_docs(self, openapi_schema: Dict[str, Any]) -> Path:
        """マークダウン形式のAPIドキュメントを生成"""
        logger.info("Generating Markdown documentation...")
        
        md_content = self._create_markdown_content(openapi_schema)
        md_path = self.docs_dir / "API_DOCUMENTATION.md"
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"Markdown documentation saved to {md_path}")
        return md_path
    
    def _create_markdown_content(self, openapi_schema: Dict[str, Any]) -> str:
        """マークダウンコンテンツを作成"""
        info = openapi_schema.get("info", {})
        paths = openapi_schema.get("paths", {})
        components = openapi_schema.get("components", {})
        
        md_content = f"""# {info.get('title', 'API Documentation')}

**Version:** {info.get('version', '1.0.0')}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Description

{info.get('description', 'API documentation for the Gait Analysis application.')}

## Base URLs

- **Development:** http://localhost:8000
- **Production:** https://api.gaitanalysis.com

## Authentication

This API supports multiple authentication methods:

### Bearer Token (JWT)
```
Authorization: Bearer <your-jwt-token>
```

### Firebase Authentication
OAuth2 flow with Google accounts:
- **Authorization URL:** https://accounts.google.com/o/oauth2/auth
- **Scopes:** openid, email, profile

## API Endpoints

"""
        
        # グループ別にエンドポイントを整理
        grouped_paths = self._group_paths_by_tags(paths)
        
        for tag, endpoints in grouped_paths.items():
            md_content += f"### {tag}\n\n"
            
            for path, methods in endpoints.items():
                for method, details in methods.items():
                    md_content += self._format_endpoint_markdown(path, method, details)
                    md_content += "\n---\n\n"
        
        # データモデルの追加
        if "schemas" in components:
            md_content += "## Data Models\n\n"
            for model_name, model_schema in components["schemas"].items():
                md_content += self._format_model_markdown(model_name, model_schema)
                md_content += "\n"
        
        # エラーコードの追加
        md_content += """## Error Codes

| Code | Description |
|------|-------------|
| 200  | OK - Request successful |
| 201  | Created - Resource created successfully |
| 400  | Bad Request - Invalid request parameters |
| 401  | Unauthorized - Authentication required |
| 403  | Forbidden - Insufficient permissions |
| 404  | Not Found - Resource not found |
| 422  | Validation Error - Request validation failed |
| 500  | Internal Server Error - Server error occurred |

## Rate Limiting

- **Standard Users:** 100 requests per minute
- **Professional Users:** 500 requests per minute
- **Admin Users:** Unlimited

## Support

For API support, please contact:
- **Email:** support@gaitanalysis.com
- **Documentation:** [API Reference](https://docs.gaitanalysis.com)
- **Status Page:** [System Status](https://status.gaitanalysis.com)

"""
        
        return md_content
    
    def _group_paths_by_tags(self, paths: Dict[str, Any]) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """パスをタグ別にグループ化"""
        grouped = {}
        
        for path, methods in paths.items():
            for method, details in methods.items():
                tags = details.get("tags", ["Default"])
                tag = tags[0] if tags else "Default"
                
                if tag not in grouped:
                    grouped[tag] = {}
                
                if path not in grouped[tag]:
                    grouped[tag][path] = {}
                
                grouped[tag][path][method.upper()] = details
        
        return grouped
    
    def _format_endpoint_markdown(self, path: str, method: str, details: Dict[str, Any]) -> str:
        """エンドポイントのマークダウンを生成"""
        summary = details.get("summary", "No summary")
        description = details.get("description", "")
        parameters = details.get("parameters", [])
        request_body = details.get("requestBody", {})
        responses = details.get("responses", {})
        
        md = f"#### `{method.upper()} {path}`\n\n"
        md += f"**Summary:** {summary}\n\n"
        
        if description:
            md += f"**Description:** {description}\n\n"
        
        # パラメータ
        if parameters:
            md += "**Parameters:**\n\n"
            md += "| Name | Type | Location | Required | Description |\n"
            md += "|------|------|----------|----------|-------------|\n"
            
            for param in parameters:
                name = param.get("name", "")
                param_type = param.get("schema", {}).get("type", "string")
                location = param.get("in", "query")
                required = "Yes" if param.get("required", False) else "No"
                desc = param.get("description", "")
                
                md += f"| {name} | {param_type} | {location} | {required} | {desc} |\n"
            
            md += "\n"
        
        # リクエストボディ
        if request_body:
            md += "**Request Body:**\n\n"
            content = request_body.get("content", {})
            if "application/json" in content:
                schema = content["application/json"].get("schema", {})
                md += "```json\n"
                md += json.dumps(self._generate_example_from_schema(schema), indent=2)
                md += "\n```\n\n"
        
        # レスポンス
        if responses:
            md += "**Responses:**\n\n"
            for status_code, response_details in responses.items():
                description = response_details.get("description", "")
                md += f"**{status_code}:** {description}\n\n"
                
                content = response_details.get("content", {})
                if "application/json" in content:
                    schema = content["application/json"].get("schema", {})
                    if schema:
                        md += "```json\n"
                        md += json.dumps(self._generate_example_from_schema(schema), indent=2)
                        md += "\n```\n\n"
        
        return md
    
    def _format_model_markdown(self, model_name: str, model_schema: Dict[str, Any]) -> str:
        """データモデルのマークダウンを生成"""
        md = f"### {model_name}\n\n"
        
        description = model_schema.get("description", "")
        if description:
            md += f"{description}\n\n"
        
        properties = model_schema.get("properties", {})
        required = model_schema.get("required", [])
        
        if properties:
            md += "| Field | Type | Required | Description |\n"
            md += "|-------|------|----------|-------------|\n"
            
            for field_name, field_schema in properties.items():
                field_type = field_schema.get("type", "unknown")
                is_required = "Yes" if field_name in required else "No"
                field_desc = field_schema.get("description", "")
                
                md += f"| {field_name} | {field_type} | {is_required} | {field_desc} |\n"
            
            md += "\n"
        
        # 例を追加
        md += "**Example:**\n\n"
        md += "```json\n"
        md += json.dumps(self._generate_example_from_schema(model_schema), indent=2)
        md += "\n```\n\n"
        
        return md
    
    def _generate_example_from_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """スキーマから例を生成"""
        if not schema:
            return {}
        
        schema_type = schema.get("type", "object")
        
        if schema_type == "object":
            properties = schema.get("properties", {})
            example = {}
            
            for prop_name, prop_schema in properties.items():
                example[prop_name] = self._generate_example_value(prop_schema)
            
            return example
        
        elif schema_type == "array":
            items_schema = schema.get("items", {})
            return [self._generate_example_value(items_schema)]
        
        else:
            return self._generate_example_value(schema)
    
    def _generate_example_value(self, schema: Dict[str, Any]):
        """スキーマから例の値を生成"""
        schema_type = schema.get("type", "string")
        
        # 例が定義されている場合はそれを使用
        if "example" in schema:
            return schema["example"]
        
        # デフォルト値が定義されている場合はそれを使用
        if "default" in schema:
            return schema["default"]
        
        # 型に基づいて例を生成
        if schema_type == "string":
            return "string"
        elif schema_type == "integer":
            return 0
        elif schema_type == "number":
            return 0.0
        elif schema_type == "boolean":
            return True
        elif schema_type == "array":
            items_schema = schema.get("items", {})
            return [self._generate_example_value(items_schema)]
        elif schema_type == "object":
            return self._generate_example_from_schema(schema)
        else:
            return None
    
    def generate_postman_collection(self, openapi_schema: Dict[str, Any]) -> Path:
        """Postmanコレクションを生成"""
        logger.info("Generating Postman collection...")
        
        collection = {
            "info": {
                "name": openapi_schema.get("info", {}).get("title", "API Collection"),
                "description": openapi_schema.get("info", {}).get("description", ""),
                "version": openapi_schema.get("info", {}).get("version", "1.0.0"),
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "auth": {
                "type": "bearer",
                "bearer": [
                    {
                        "key": "token",
                        "value": "{{access_token}}",
                        "type": "string"
                    }
                ]
            },
            "variable": [
                {
                    "key": "base_url",
                    "value": "http://localhost:8000",
                    "type": "string"
                },
                {
                    "key": "access_token",
                    "value": "",
                    "type": "string"
                }
            ],
            "item": []
        }
        
        # エンドポイントをPostmanアイテムに変換
        paths = openapi_schema.get("paths", {})
        for path, methods in paths.items():
            for method, details in methods.items():
                item = self._create_postman_item(path, method, details)
                collection["item"].append(item)
        
        # Postmanコレクションを保存
        postman_path = self.docs_dir / "postman_collection.json"
        with open(postman_path, 'w', encoding='utf-8') as f:
            json.dump(collection, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Postman collection saved to {postman_path}")
        return postman_path
    
    def _create_postman_item(self, path: str, method: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Postmanアイテムを作成"""
        item = {
            "name": details.get("summary", f"{method.upper()} {path}"),
            "request": {
                "method": method.upper(),
                "header": [
                    {
                        "key": "Content-Type",
                        "value": "application/json",
                        "type": "text"
                    }
                ],
                "url": {
                    "raw": f"{{{{base_url}}}}{path}",
                    "host": ["{{base_url}}"],
                    "path": path.strip("/").split("/") if path != "/" else []
                }
            }
        }
        
        # リクエストボディがある場合
        request_body = details.get("requestBody", {})
        if request_body:
            content = request_body.get("content", {})
            if "application/json" in content:
                schema = content["application/json"].get("schema", {})
                example = self._generate_example_from_schema(schema)
                item["request"]["body"] = {
                    "mode": "raw",
                    "raw": json.dumps(example, indent=2),
                    "options": {
                        "raw": {
                            "language": "json"
                        }
                    }
                }
        
        # パラメータがある場合
        parameters = details.get("parameters", [])
        query_params = []
        for param in parameters:
            if param.get("in") == "query":
                query_params.append({
                    "key": param.get("name", ""),
                    "value": str(self._generate_example_value(param.get("schema", {}))),
                    "description": param.get("description", "")
                })
        
        if query_params:
            item["request"]["url"]["query"] = query_params
        
        return item
    
    def generate_all_documentation(self) -> Dict[str, Path]:
        """すべてのドキュメンテーションを生成"""
        logger.info("Starting comprehensive documentation generation...")
        
        generated_files = {}
        
        try:
            # OpenAPI仕様を生成
            openapi_schema = self.generate_openapi_spec()
            
            # 各形式で保存
            generated_files["openapi_json"] = self.save_openapi_json(openapi_schema)
            generated_files["openapi_yaml"] = self.save_openapi_yaml(openapi_schema)
            generated_files["markdown"] = self.generate_markdown_docs(openapi_schema)
            generated_files["postman"] = self.generate_postman_collection(openapi_schema)
            
            logger.info("Documentation generation completed successfully")
            logger.info(f"Generated files: {list(generated_files.keys())}")
            
            return generated_files
            
        except Exception as e:
            logger.error(f"Documentation generation failed: {e}")
            raise


def generate_api_documentation(app: FastAPI) -> Dict[str, Path]:
    """API ドキュメンテーション生成の便利関数"""
    generator = APIDocumentationGenerator(app)
    return generator.generate_all_documentation()