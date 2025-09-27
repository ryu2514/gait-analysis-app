"""
データベース機能のテストスクリプト
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# プロジェクトのパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import db_manager, init_database
from app.services.data_service import data_service
from app.models.gait_models import (
    GaitAnalysisResponse, SpatiotemporalParameters, 
    SymmetryIndices, JointAngles, GaitCycle
)


def create_test_analysis_result(analysis_id: str = "TEST_001") -> GaitAnalysisResponse:
    """テスト用の分析結果を作成"""
    
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
        analysis_id=analysis_id,
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


async def test_database_initialization():
    """データベース初期化テスト"""
    print("🧪 Testing Database Initialization...")
    
    try:
        await init_database()
        
        # 接続確認
        health_status = db_manager.health_check()
        
        if health_status:
            print("✅ Database initialized and connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


async def test_save_analysis_result():
    """分析結果保存テスト"""
    print("🧪 Testing Save Analysis Result...")
    
    try:
        user_id = "test_user_001"
        analysis_result = create_test_analysis_result("SAVE_TEST_001")
        
        saved_id = await data_service.save_analysis_result(
            user_id=user_id,
            analysis_result=analysis_result,
            video_info={
                "filename": "test_video.mp4",
                "duration_seconds": 5.0,
                "resolution": "1920x1080",
                "fps": 30
            }
        )
        
        if saved_id:
            print(f"✅ Analysis result saved successfully")
            print(f"   - Saved ID: {saved_id}")
            print(f"   - Analysis ID: {analysis_result.analysis_id}")
            return True
        else:
            print("❌ Failed to save analysis result")
            return False
            
    except Exception as e:
        print(f"❌ Save analysis result failed: {e}")
        return False


async def test_get_analysis_result():
    """分析結果取得テスト"""
    print("🧪 Testing Get Analysis Result...")
    
    try:
        user_id = "test_user_001"
        analysis_id = "SAVE_TEST_001"
        
        retrieved_result = await data_service.get_analysis_result(
            user_id=user_id,
            analysis_id=analysis_id
        )
        
        if retrieved_result:
            print(f"✅ Analysis result retrieved successfully")
            print(f"   - Analysis ID: {retrieved_result.analysis_id}")
            print(f"   - Overall Score: {retrieved_result.overall_gait_score}")
            print(f"   - Gait Cycles: {len(retrieved_result.gait_cycles)}")
            return True
        else:
            print("❌ Analysis result not found")
            return False
            
    except Exception as e:
        print(f"❌ Get analysis result failed: {e}")
        return False


async def test_analysis_history():
    """分析履歴取得テスト"""
    print("🧪 Testing Analysis History...")
    
    try:
        user_id = "test_user_001"
        
        # 複数の分析結果を保存
        for i in range(3):
            analysis_result = create_test_analysis_result(f"HISTORY_TEST_{i:03d}")
            # 時間をずらす
            analysis_result.timestamp = datetime.now() - timedelta(days=i)
            
            await data_service.save_analysis_result(
                user_id=user_id,
                analysis_result=analysis_result
            )
        
        # 履歴取得
        history = await data_service.get_user_analysis_history(
            user_id=user_id,
            limit=10
        )
        
        if len(history) >= 3:
            print(f"✅ Analysis history retrieved successfully")
            print(f"   - History count: {len(history)}")
            print(f"   - Latest analysis: {history[0]['analysis_id']}")
            return True
        else:
            print(f"❌ Insufficient history entries: {len(history)}")
            return False
            
    except Exception as e:
        print(f"❌ Analysis history test failed: {e}")
        return False


async def test_user_statistics():
    """ユーザー統計テスト"""
    print("🧪 Testing User Statistics...")
    
    try:
        user_id = "test_user_001"
        
        statistics = await data_service.get_user_statistics(user_id=user_id)
        
        if statistics:
            print(f"✅ User statistics retrieved successfully")
            print(f"   - Total analyses: {statistics['total_analyses']}")
            print(f"   - This month analyses: {statistics['this_month_analyses']}")
            print(f"   - Average score: {statistics['average_score']}")
            return True
        else:
            print("❌ Failed to retrieve user statistics")
            return False
            
    except Exception as e:
        print(f"❌ User statistics test failed: {e}")
        return False


async def test_delete_analysis():
    """分析結果削除テスト"""
    print("🧪 Testing Delete Analysis...")
    
    try:
        user_id = "test_user_001"
        analysis_id = "HISTORY_TEST_002"
        
        # 削除実行
        success = await data_service.delete_analysis(
            user_id=user_id,
            analysis_id=analysis_id
        )
        
        if success:
            # 削除確認
            deleted_result = await data_service.get_analysis_result(
                user_id=user_id,
                analysis_id=analysis_id
            )
            
            if deleted_result is None:
                print(f"✅ Analysis deleted successfully")
                print(f"   - Deleted analysis ID: {analysis_id}")
                return True
            else:
                print("❌ Analysis was not actually deleted")
                return False
        else:
            print("❌ Failed to delete analysis")
            return False
            
    except Exception as e:
        print(f"❌ Delete analysis test failed: {e}")
        return False


async def test_database_performance():
    """データベースパフォーマンステスト"""
    print("🧪 Testing Database Performance...")
    
    try:
        user_id = "performance_user"
        start_time = datetime.now()
        
        # 100件の分析結果を保存
        for i in range(100):
            analysis_result = create_test_analysis_result(f"PERF_TEST_{i:03d}")
            await data_service.save_analysis_result(
                user_id=user_id,
                analysis_result=analysis_result
            )
        
        save_time = datetime.now() - start_time
        
        # 履歴取得パフォーマンス
        start_time = datetime.now()
        history = await data_service.get_user_analysis_history(
            user_id=user_id,
            limit=50
        )
        query_time = datetime.now() - start_time
        
        print(f"✅ Database performance test completed")
        print(f"   - Save 100 records: {save_time.total_seconds():.2f} seconds")
        print(f"   - Query 50 records: {query_time.total_seconds():.2f} seconds")
        print(f"   - Records retrieved: {len(history)}")
        
        # パフォーマンス基準チェック
        if save_time.total_seconds() < 30 and query_time.total_seconds() < 1:
            return True
        else:
            print("⚠️  Performance below expected thresholds")
            return False
            
    except Exception as e:
        print(f"❌ Database performance test failed: {e}")
        return False


async def run_all_tests():
    """全テスト実行"""
    print("🚀 Starting Database Tests\n")
    
    tests = [
        ("Database Initialization", test_database_initialization),
        ("Save Analysis Result", test_save_analysis_result),
        ("Get Analysis Result", test_get_analysis_result),
        ("Analysis History", test_analysis_history),
        ("User Statistics", test_user_statistics),
        ("Delete Analysis", test_delete_analysis),
        ("Database Performance", test_database_performance),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        result = await test_func()
        results.append((test_name, result))
    
    print("\n" + "="*50)
    print("📊 Database Test Results")
    print("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All database tests passed!")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    return passed == len(results)


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)