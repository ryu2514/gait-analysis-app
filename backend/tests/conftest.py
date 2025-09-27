"""
Pytestの共通設定とフィクスチャ
"""

import pytest
import asyncio
import tempfile
import os
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# プロジェクトのパスを追加
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from app.database.connection import db_manager, get_database_session
from app.models.database_models import Base
from app.models.gait_models import (
    GaitAnalysisResponse, SpatiotemporalParameters, 
    SymmetryIndices, JointAngles, GaitCycle
)
from datetime import datetime


@pytest.fixture(scope="session")
def event_loop():
    """セッション全体で共有するイベントループ"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def temp_db():
    """テスト用の一時データベース"""
    # 一時ファイル作成
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    
    # テスト用エンジン作成
    test_engine = create_engine(
        f"sqlite:///{temp_file.name}",
        connect_args={"check_same_thread": False}
    )
    
    # テーブル作成
    Base.metadata.create_all(bind=test_engine)
    
    # テスト用セッションファクトリ
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    yield TestingSessionLocal
    
    # クリーンアップ
    try:
        os.unlink(temp_file.name)
    except OSError:
        pass


@pytest.fixture
def test_db_session(temp_db):
    """テスト用データベースセッション"""
    session = temp_db()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def override_get_db(test_db_session):
    """データベース依存関数をオーバーライド"""
    def _override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_database_session] = _override_get_db
    yield
    app.dependency_overrides = {}


@pytest.fixture
def client(override_get_db):
    """テスト用FastAPIクライアント"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_gait_analysis_response():
    """サンプル歩行分析レスポンス"""
    spatiotemporal_params = SpatiotemporalParameters(
        gait_speed_ms=1.25,
        gait_speed_kmh=4.5,
        cadence_steps_per_min=110,
        stride_length_m=1.35,
        stride_time_s=1.09,
        left_step_length_m=0.67,
        right_step_length_m=0.68,
        left_stance_time_s=0.65,
        right_stance_time_s=0.67,
        double_support_time_s=0.12,
        speed_evaluation="良好"
    )
    
    symmetry_indices = SymmetryIndices(
        step_length_symmetry_percent=3.2,
        stance_time_symmetry_percent=4.1,
        swing_time_symmetry_percent=2.8,
        hip_flexion_symmetry_percent=6.5,
        knee_flexion_symmetry_percent=5.2,
        ankle_dorsiflexion_symmetry_percent=7.8,
        overall_symmetry_score=87.5
    )
    
    joint_angles = JointAngles(
        hip_flexion_deg=[25, 30, 35, 40, 35, 30, 25, 20, 25],
        hip_abduction_deg=[5, 8, 6, 4, 7, 9, 5, 6, 5],
        knee_flexion_deg=[15, 45, 60, 55, 40, 25, 15, 10, 15],
        ankle_dorsiflexion_deg=[0, 5, 10, 8, 2, -5, 0, 2, 0],
        pelvic_drop_deg=[1, 2, 1, -1, 2, 3, 1, 0, 1],
        frame_timestamps=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6]
    )
    
    gait_cycles = [
        GaitCycle(
            cycle_id="L_001",
            start_frame=0,
            end_frame=30,
            duration_seconds=1.0,
            side="left",
            step_length_m=0.67,
            step_width_m=0.10,
            stance_time_seconds=0.65,
            swing_time_seconds=0.35,
            stance_ratio=0.65,
            hip_flexion_peak_deg=35.0,
            knee_flexion_peak_deg=60.0,
            ankle_dorsiflexion_peak_deg=10.0,
            phase_timings={}
        ),
        GaitCycle(
            cycle_id="R_001",
            start_frame=15,
            end_frame=45,
            duration_seconds=1.0,
            side="right",
            step_length_m=0.68,
            step_width_m=0.10,
            stance_time_seconds=0.67,
            swing_time_seconds=0.33,
            stance_ratio=0.67,
            hip_flexion_peak_deg=33.0,
            knee_flexion_peak_deg=58.0,
            ankle_dorsiflexion_peak_deg=8.0,
            phase_timings={}
        )
    ]
    
    recommendations = [
        "歩行対称性は良好です。現在の活動レベルを維持してください",
        "左右の歩幅差が軽度あります。バランス訓練を検討してください"
    ]
    
    return GaitAnalysisResponse(
        analysis_id="TEST_ANALYSIS_001",
        status="completed",
        timestamp=datetime.now(),
        processing_time_seconds=2.5,
        spatiotemporal_params=spatiotemporal_params,
        symmetry_indices=symmetry_indices,
        gait_cycles=gait_cycles,
        joint_angles=joint_angles,
        video_quality_score=92.5,
        pose_detection_confidence=0.89,
        gait_cycles_detected=2,
        overall_gait_score=88.2,
        recommendations=recommendations,
        video_info={
            "total_frames": 150,
            "duration_seconds": 5.0,
            "resolution": "1920x1080",
            "fps": 30
        },
        analysis_settings={
            "analysis_mode": "standard",
            "user_height_cm": 170,
            "scale_factor": 1.0,
            "model_complexity": 1
        }
    )


@pytest.fixture
def sample_landmarks_data():
    """サンプルランドマークデータ"""
    import numpy as np
    
    num_frames = 60
    fps = 30.0
    landmarks_data = []
    
    for frame in range(num_frames):
        timestamp = frame / fps
        
        # 33個のMediaPipe Poseランドマークを模擬
        landmarks = []
        for i in range(33):
            # 歩行中の足首の動きを模擬
            if i == 27:  # 左足首
                y_offset = 0.1 * np.sin(timestamp * 2 * np.pi * 1.2)
                landmarks.append({
                    'x': 0.3 + 0.02 * timestamp,
                    'y': 0.8 + y_offset,
                    'z': 0.0,
                    'visibility': 0.9
                })
            elif i == 28:  # 右足首
                y_offset = 0.1 * np.sin(timestamp * 2 * np.pi * 1.2 + np.pi)
                landmarks.append({
                    'x': 0.7 + 0.02 * timestamp,
                    'y': 0.8 + y_offset,
                    'z': 0.0,
                    'visibility': 0.9
                })
            else:
                # その他のランドマークは固定位置
                landmarks.append({
                    'x': 0.5 + 0.1 * np.random.normal(0, 0.01),
                    'y': 0.5 + 0.1 * np.random.normal(0, 0.01),
                    'z': 0.0,
                    'visibility': 0.8 + 0.2 * np.random.random()
                })
        
        landmarks_data.append({
            'frame': frame,
            'timestamp': timestamp,
            'landmarks': landmarks
        })
    
    return landmarks_data


@pytest.fixture
def sample_video_file():
    """サンプル動画ファイル（モック）"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    temp_file.write(b'mock video data')
    temp_file.close()
    
    yield temp_file.name
    
    try:
        os.unlink(temp_file.name)
    except OSError:
        pass


@pytest.fixture
def mock_user_data():
    """モックユーザーデータ"""
    return {
        "id": "test_user_001",
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "height_cm": 170.0,
        "weight_kg": 70.0,
        "age": 30,
        "gender": "male"
    }