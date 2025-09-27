"""
歩行分析エンジンのテストスクリプト
"""

import asyncio
import sys
import os
import numpy as np
from typing import List, Dict

# プロジェクトのパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.gait_service import GaitAnalysisService
from app.services.gait_cycle_detector import GaitCycleDetector
from app.services.spatiotemporal_analyzer import SpatiotemporalAnalyzer
from app.services.joint_angle_calculator import JointAngleCalculator
from app.services.symmetry_analyzer import SymmetryAnalyzer
from app.models.gait_models import GaitCycle, JointAngles


def create_mock_landmarks_data(num_frames: int = 100, fps: float = 30.0) -> List[Dict]:
    """テスト用のモック姿勢データ作成"""
    landmarks_data = []
    
    for frame in range(num_frames):
        timestamp = frame / fps
        
        # 33個のMediaPipe Poseランドマークを模擬
        landmarks = []
        for i in range(33):
            # 歩行中の足首の動きを模擬
            if i == 27:  # 左足首
                y_offset = 0.1 * np.sin(timestamp * 2 * np.pi * 1.2)  # 歩行周期約0.8秒
                landmarks.append({
                    'x': 0.3 + 0.02 * timestamp,  # 前進
                    'y': 0.8 + y_offset,  # 上下運動
                    'z': 0.0,
                    'visibility': 0.9
                })
            elif i == 28:  # 右足首
                y_offset = 0.1 * np.sin(timestamp * 2 * np.pi * 1.2 + np.pi)  # 位相反転
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


def create_mock_gait_cycles() -> List[GaitCycle]:
    """テスト用の歩行周期データ作成"""
    gait_cycles = []
    
    # 左脚の歩行周期
    for i in range(3):
        start_frame = i * 25
        end_frame = (i + 1) * 25
        
        cycle = GaitCycle(
            cycle_id=f"L_{i}",
            start_frame=start_frame,
            end_frame=end_frame,
            duration_seconds=0.8 + 0.1 * np.random.random(),
            side="left",
            step_length_m=0.65 + 0.05 * np.random.random(),
            step_width_m=0.1,
            stance_time_seconds=0.5,
            swing_time_seconds=0.3,
            stance_ratio=0.625,
            hip_flexion_peak_deg=30.0,
            knee_flexion_peak_deg=60.0,
            ankle_dorsiflexion_peak_deg=10.0,
            phase_timings={}
        )
        gait_cycles.append(cycle)
    
    # 右脚の歩行周期
    for i in range(3):
        start_frame = i * 25 + 12  # 位相をずらす
        end_frame = (i + 1) * 25 + 12
        
        cycle = GaitCycle(
            cycle_id=f"R_{i}",
            start_frame=start_frame,
            end_frame=end_frame,
            duration_seconds=0.85 + 0.1 * np.random.random(),
            side="right",
            step_length_m=0.63 + 0.05 * np.random.random(),
            step_width_m=0.1,
            stance_time_seconds=0.52,
            swing_time_seconds=0.33,
            stance_ratio=0.612,
            hip_flexion_peak_deg=32.0,
            knee_flexion_peak_deg=58.0,
            ankle_dorsiflexion_peak_deg=8.0,
            phase_timings={}
        )
        gait_cycles.append(cycle)
    
    return gait_cycles


def create_mock_joint_angles(num_frames: int = 100) -> JointAngles:
    """テスト用の関節角度データ作成"""
    timestamps = [i / 30.0 for i in range(num_frames)]
    
    # 歩行中の関節角度パターンを模擬
    hip_flexion = [25 + 15 * np.sin(t * 2 * np.pi * 1.2) for t in timestamps]
    hip_abduction = [5 + 3 * np.cos(t * 2 * np.pi * 1.2) for t in timestamps]
    knee_flexion = [30 + 35 * np.sin(t * 2 * np.pi * 1.2 + np.pi/4) for t in timestamps]
    ankle_dorsiflexion = [5 + 10 * np.sin(t * 2 * np.pi * 1.2 + np.pi/2) for t in timestamps]
    pelvic_drop = [2 * np.sin(t * 2 * np.pi * 1.2 + np.pi/3) for t in timestamps]
    
    return JointAngles(
        hip_flexion_deg=hip_flexion,
        hip_abduction_deg=hip_abduction,
        knee_flexion_deg=knee_flexion,
        ankle_dorsiflexion_deg=ankle_dorsiflexion,
        pelvic_drop_deg=pelvic_drop,
        frame_timestamps=timestamps
    )


async def test_gait_cycle_detector():
    """歩行周期検出器のテスト"""
    print("🧪 Testing Gait Cycle Detector...")
    
    detector = GaitCycleDetector()
    landmarks_data = create_mock_landmarks_data()
    
    try:
        gait_cycles = detector.detect_gait_cycles(landmarks_data, fps=30.0)
        
        print(f"✅ Detected {len(gait_cycles)} gait cycles")
        for cycle in gait_cycles[:3]:  # 最初の3つを表示
            print(f"   - {cycle.cycle_id}: {cycle.duration_seconds:.2f}s, {cycle.side} side")
        
        return True
    except Exception as e:
        print(f"❌ Gait cycle detection failed: {e}")
        return False


async def test_spatiotemporal_analyzer():
    """時空間パラメータ分析器のテスト"""
    print("🧪 Testing Spatiotemporal Analyzer...")
    
    analyzer = SpatiotemporalAnalyzer()
    gait_cycles = create_mock_gait_cycles()
    
    try:
        params = analyzer.analyze_spatiotemporal_parameters(gait_cycles, scale_factor=1.0)
        
        print(f"✅ Spatiotemporal analysis completed")
        print(f"   - Gait speed: {params.gait_speed_ms:.2f} m/s")
        print(f"   - Cadence: {params.cadence_steps_per_min} steps/min")
        print(f"   - Stride length: {params.stride_length_m:.2f} m")
        
        return True
    except Exception as e:
        print(f"❌ Spatiotemporal analysis failed: {e}")
        return False


async def test_joint_angle_calculator():
    """関節角度計算器のテスト"""
    print("🧪 Testing Joint Angle Calculator...")
    
    calculator = JointAngleCalculator()
    landmarks_data = create_mock_landmarks_data()
    
    try:
        joint_angles = calculator.calculate_joint_angles(landmarks_data)
        
        print(f"✅ Joint angle calculation completed")
        print(f"   - Hip flexion peak: {max(joint_angles.hip_flexion_deg):.1f}°")
        print(f"   - Knee flexion peak: {max(joint_angles.knee_flexion_deg):.1f}°")
        print(f"   - Ankle dorsiflexion peak: {max(joint_angles.ankle_dorsiflexion_deg):.1f}°")
        
        return True
    except Exception as e:
        print(f"❌ Joint angle calculation failed: {e}")
        return False


async def test_symmetry_analyzer():
    """対称性分析器のテスト"""
    print("🧪 Testing Symmetry Analyzer...")
    
    analyzer = SymmetryAnalyzer()
    gait_cycles = create_mock_gait_cycles()
    joint_angles = create_mock_joint_angles()
    
    try:
        symmetry = analyzer.analyze_gait_symmetry(gait_cycles, joint_angles)
        
        print(f"✅ Symmetry analysis completed")
        print(f"   - Step length symmetry: {symmetry.step_length_symmetry_percent:.1f}%")
        print(f"   - Stance time symmetry: {symmetry.stance_time_symmetry_percent:.1f}%")
        print(f"   - Overall symmetry score: {symmetry.overall_symmetry_score:.1f}")
        
        return True
    except Exception as e:
        print(f"❌ Symmetry analysis failed: {e}")
        return False


async def test_integrated_analysis():
    """統合分析のテスト"""
    print("🧪 Testing Integrated Gait Analysis...")
    
    # 注意: この統合テストは実際の動画ファイルなしでは完全には動作しません
    # ここでは主要コンポーネントの連携をテストします
    
    try:
        gait_service = GaitAnalysisService()
        
        # 個別コンポーネントの初期化確認
        assert gait_service.gait_detector is not None
        assert gait_service.spatiotemporal_analyzer is not None
        assert gait_service.joint_calculator is not None
        assert gait_service.symmetry_analyzer is not None
        
        print("✅ Integrated analysis service initialized successfully")
        print("   - All components are properly connected")
        
        return True
    except Exception as e:
        print(f"❌ Integrated analysis test failed: {e}")
        return False


async def run_all_tests():
    """全テスト実行"""
    print("🚀 Starting Gait Analysis Engine Tests\n")
    
    tests = [
        ("Gait Cycle Detector", test_gait_cycle_detector),
        ("Spatiotemporal Analyzer", test_spatiotemporal_analyzer),
        ("Joint Angle Calculator", test_joint_angle_calculator),
        ("Symmetry Analyzer", test_symmetry_analyzer),
        ("Integrated Analysis", test_integrated_analysis),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        result = await test_func()
        results.append((test_name, result))
    
    print("\n" + "="*50)
    print("📊 Test Results Summary")
    print("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Gait analysis engine is ready.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    return passed == len(results)


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)