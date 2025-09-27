"""
拡張歩行分析APIのテスト
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


@patch('app.services.gait_service.GaitAnalysisService.analyze_gait_optimized')
def test_analyze_enhanced_success(mock_analyze_opt, client: TestClient):
    """拡張歩行分析API 正常系"""
    # モック戻り値（最低限のキー）
    mock_analyze_opt.return_value = {
        "overall_gait_score": 88.0,
        "video_quality_score": 92.0,
        "gait_cycles": [],
        "enhanced_spatiotemporal_params": {
            "gait_speed_ms": 1.2,
            "cadence_steps_per_min": 110
        },
        "balance_metrics": {"balance_stability_score": 85.0},
        "compensation_alerts": [],
        "video_info": {"fps": 60},
    }

    files = {"video": ("test.mp4", b"fake video data", "video/mp4")}
    params = {
        "analysis_mode": "detailed",
        "target_fps": 60,
        "device_type": "mobile",
    }

    response = client.post(
        "/api/v1/gait-analysis/analyze-enhanced",
        files=files,
        params=params,
    )

    assert response.status_code == 200
    data = response.json()
    # レスポンスの基本キー
    assert data["status"] == "completed"
    assert "analysis_id" in data
    assert "processing_time_seconds" in data
    # 拡張キー
    assert "spatiotemporal_parameters" in data
    assert "balance_metrics" in data
    assert "scores" in data


def test_analyze_enhanced_invalid_mode(client: TestClient):
    """無効な分析モードのバリデーション"""
    files = {"video": ("test.mp4", b"fake video data", "video/mp4")}
    params = {
        "analysis_mode": "invalid_mode",
    }

    response = client.post(
        "/api/v1/gait-analysis/analyze-enhanced",
        files=files,
        params=params,
    )

    assert response.status_code == 400
    assert "無効な分析モード" in response.json().get("detail", "")


def test_enhanced_capabilities(client: TestClient):
    """拡張機能一覧の取得"""
    response = client.get("/api/v1/gait-analysis/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert "enhanced_features" in data
    assert "analysis_modes" in data
    assert "performance_specs" in data

