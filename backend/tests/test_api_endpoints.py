"""
APIエンドポイントのテスト
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestHealthEndpoints:
    """ヘルスチェックエンドポイントのテスト"""
    
    def test_health_check(self, client: TestClient):
        """ヘルスチェックエンドポイントのテスト"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_health_detailed(self, client: TestClient):
        """詳細ヘルスチェックのテスト"""
        response = client.get("/api/v1/health/detailed")
        assert response.status_code == 200
        
        data = response.json()
        assert "api" in data
        assert "database" in data
        assert "mediapipe" in data


class TestGaitAnalysisEndpoints:
    """歩行分析エンドポイントのテスト"""
    
    @patch('app.services.gait_service.GaitAnalysisService.analyze_gait')
    def test_analyze_gait_success(self, mock_analyze, client: TestClient, sample_gait_analysis_response):
        """歩行分析APIの正常系テスト"""
        # モックの設定
        mock_analyze.return_value = sample_gait_analysis_response.dict()
        
        # テストファイルのアップロード（モック）
        files = {"video": ("test.mp4", b"fake video data", "video/mp4")}
        data = {
            "user_height_cm": "170",
            "analysis_mode": "standard"
        }
        
        response = client.post("/api/v1/gait-analysis/analyze", files=files, data=data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["status"] in ["completed", "success"]
        assert result["analysis_id"] == "TEST_ANALYSIS_001"
        assert "processing_time_seconds" in result
        assert "gait_cycles_detected" in result
    
    def test_analyze_gait_missing_file(self, client: TestClient):
        """動画ファイルが未提供の場合のテスト"""
        data = {"user_height_cm": "170"}
        
        response = client.post("/api/v1/gait-analysis/analyze", data=data)
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_analyze_gait_invalid_file_type(self, client: TestClient):
        """無効なファイル形式のテスト"""
        files = {"video": ("test.txt", b"not a video", "text/plain")}
        data = {"user_height_cm": "170"}
        
        response = client.post("/api/v1/gait-analysis/analyze", files=files, data=data)
        assert response.status_code == 400
        
        result = response.json()
        assert "サポートされていないファイル形式" in result["detail"]
    
    @patch('app.services.gait_service.GaitAnalysisService.analyze_gait')
    def test_analyze_gait_processing_error(self, mock_analyze, client: TestClient):
        """分析処理エラーのテスト"""
        # エラーを発生させるモック
        mock_analyze.side_effect = Exception("MediaPipe processing failed")
        
        files = {"video": ("test.mp4", b"fake video data", "video/mp4")}
        data = {"user_height_cm": "170"}
        
        response = client.post("/api/v1/gait-analysis/analyze", files=files, data=data)
        assert response.status_code == 500
        # 詳細メッセージは実装依存のため省略


class TestReportsEndpoints:
    """レポート生成エンドポイントのテスト"""
    
    @patch('app.services.report_generator.ReportGenerator.generate_pdf_report')
    def test_generate_pdf_report_success(self, mock_generate, client: TestClient, sample_gait_analysis_response):
        """PDFレポート生成の正常系テスト"""
        # モックPDFファイルパス
        mock_generate.return_value = "/tmp/test_report.pdf"
        
        # PDFファイルの存在をモック
        with patch('os.path.exists', return_value=True):
            with patch('fastapi.responses.FileResponse') as mock_file_response:
                mock_file_response.return_value = MagicMock()
                
                response = client.post(
                    "/api/v1/reports/generate/pdf",
                    json=sample_gait_analysis_response.dict()
                )
                
                # モックが呼ばれたことを確認
                mock_generate.assert_called_once()
    
    @patch('app.services.report_generator.ReportGenerator.generate_png_summary')
    def test_generate_png_summary_success(self, mock_generate, client: TestClient, sample_gait_analysis_response):
        """PNG画像生成の正常系テスト"""
        mock_generate.return_value = "/tmp/test_summary.png"
        
        with patch('os.path.exists', return_value=True):
            with patch('fastapi.responses.FileResponse') as mock_file_response:
                mock_file_response.return_value = MagicMock()
                
                response = client.post(
                    "/api/v1/reports/generate/png",
                    json=sample_gait_analysis_response.dict()
                )
                
                mock_generate.assert_called_once()
    
    @patch('app.services.report_generator.ReportGenerator.generate_base64_image')
    def test_generate_base64_image_success(self, mock_generate, client: TestClient, sample_gait_analysis_response):
        """Base64画像生成の正常系テスト"""
        mock_generate.return_value = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        response = client.post(
            "/api/v1/reports/generate/base64",
            json=sample_gait_analysis_response.dict()
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "success"
        assert "image_data" in result
        assert result["image_data"].startswith("data:image/png;base64,")
    
    def test_get_report_templates(self, client: TestClient):
        """レポートテンプレート一覧取得のテスト"""
        response = client.get("/api/v1/reports/templates")
        assert response.status_code == 200
        
        result = response.json()
        assert result["status"] == "success"
        assert "templates" in result
        assert len(result["templates"]) > 0
        
        # テンプレート構造の確認
        template = result["templates"][0]
        required_fields = ["id", "name", "description", "format", "sections"]
        for field in required_fields:
            assert field in template


class TestHistoryEndpoints:
    """履歴管理エンドポイントのテスト"""
    
    @patch('app.services.data_service.data_service.get_user_analysis_history')
    def test_get_analysis_history_success(self, mock_get_history, client: TestClient):
        """分析履歴取得の正常系テスト"""
        mock_history = [
            {
                "id": "hist_001",
                "analysis_id": "ANALYSIS_001",
                "analysis_date": "2024-01-01T10:00:00",
                "overall_gait_score": 85.5,
                "video_quality_score": 90.0,
                "gait_cycles_detected": 3,
                "analysis_mode": "standard",
                "processing_time_seconds": 2.5,
                "has_reports": True
            }
        ]
        mock_get_history.return_value = mock_history
        
        response = client.get("/api/v1/history/analyses?user_id=test_user_001")
        assert response.status_code == 200
        
        result = response.json()
        assert result["status"] == "success"
        assert "data" in result
        assert len(result["data"]["analyses"]) == 1
    
    def test_get_analysis_history_missing_user_id(self, client: TestClient):
        """ユーザーID未指定の場合のテスト"""
        response = client.get("/api/v1/history/analyses")
        assert response.status_code == 422  # Validation error
    
    @patch('app.services.data_service.data_service.get_analysis_result')
    def test_get_analysis_detail_success(self, mock_get_result, client: TestClient, sample_gait_analysis_response):
        """分析詳細取得の正常系テスト"""
        mock_get_result.return_value = sample_gait_analysis_response
        
        response = client.get("/api/v1/history/analyses/TEST_ANALYSIS_001?user_id=test_user_001")
        assert response.status_code == 200
        
        result = response.json()
        assert result["status"] == "success"
        assert result["data"]["analysis_id"] == "TEST_ANALYSIS_001"
    
    @patch('app.services.data_service.data_service.get_analysis_result')
    def test_get_analysis_detail_not_found(self, mock_get_result, client: TestClient):
        """存在しない分析詳細取得のテスト"""
        mock_get_result.return_value = None
        
        response = client.get("/api/v1/history/analyses/NONEXISTENT?user_id=test_user_001")
        assert response.status_code == 404
        
        result = response.json()
        assert "見つかりません" in result["detail"]
    
    @patch('app.services.data_service.data_service.delete_analysis')
    def test_delete_analysis_success(self, mock_delete, client: TestClient):
        """分析削除の正常系テスト"""
        mock_delete.return_value = True
        
        response = client.delete("/api/v1/history/analyses/TEST_ANALYSIS_001?user_id=test_user_001")
        assert response.status_code == 200
        
        result = response.json()
        assert result["status"] == "success"
        assert "削除されました" in result["message"]
    
    @patch('app.services.data_service.data_service.delete_analysis')
    def test_delete_analysis_not_found(self, mock_delete, client: TestClient):
        """存在しない分析削除のテスト"""
        mock_delete.return_value = False
        
        response = client.delete("/api/v1/history/analyses/NONEXISTENT?user_id=test_user_001")
        assert response.status_code == 404
    
    @patch('app.services.data_service.data_service.get_user_statistics')
    def test_get_user_statistics_success(self, mock_get_stats, client: TestClient):
        """ユーザー統計取得の正常系テスト"""
        mock_stats = {
            "total_analyses": 10,
            "this_month_analyses": 3,
            "average_score": 82.5,
            "latest_analysis_date": "2024-01-01T10:00:00",
            "latest_score": 85.0,
            "score_trend": [
                {"date": "2024-01-01T10:00:00", "score": 85.0},
                {"date": "2024-01-02T10:00:00", "score": 87.0}
            ]
        }
        mock_get_stats.return_value = mock_stats
        
        response = client.get("/api/v1/history/statistics?user_id=test_user_001")
        assert response.status_code == 200
        
        result = response.json()
        assert result["status"] == "success"
        assert result["data"]["total_analyses"] == 10
        assert result["data"]["average_score"] == 82.5


class TestErrorHandling:
    """エラーハンドリングのテスト"""
    
    def test_invalid_endpoint(self, client: TestClient):
        """存在しないエンドポイントのテスト"""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
    
    def test_invalid_method(self, client: TestClient):
        """無効なHTTPメソッドのテスト"""
        response = client.patch("/api/v1/health")  # PATCHメソッドは未対応
        assert response.status_code == 405
    
    def test_malformed_json(self, client: TestClient):
        """不正なJSONのテスト"""
        response = client.post(
            "/api/v1/reports/generate/base64",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


class TestSecurityHeaders:
    """セキュリティヘッダーのテスト"""
    
    def test_cors_headers(self, client: TestClient):
        """CORSヘッダーのテスト"""
        response = client.options("/api/v1/health")
        
        # CORS関連ヘッダーの確認
        assert "access-control-allow-origin" in response.headers or \
               "Access-Control-Allow-Origin" in response.headers
    
    def test_security_headers_present(self, client: TestClient):
        """基本的なセキュリティヘッダーの確認"""
        response = client.get("/api/v1/health")
        
        # Content-Typeヘッダーの確認
        assert "application/json" in response.headers.get("content-type", "")
