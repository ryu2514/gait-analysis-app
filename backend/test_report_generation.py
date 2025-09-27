"""
レポート生成機能のテストスクリプト
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any

# プロジェクトのパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.report_generator import ReportGenerator
from app.models.gait_models import (
    GaitAnalysisResponse, SpatiotemporalParameters, 
    SymmetryIndices, JointAngles, GaitCycle
)


def create_mock_analysis_result() -> GaitAnalysisResponse:
    """テスト用の分析結果を作成"""
    
    # 時空間パラメータ
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
        double_support_time_s=0.12
    )
    
    # 対称性指標
    symmetry_indices = SymmetryIndices(
        step_length_symmetry_percent=3.2,
        stance_time_symmetry_percent=4.1,
        swing_time_symmetry_percent=2.8,
        hip_flexion_symmetry_percent=6.5,
        knee_flexion_symmetry_percent=5.2,
        ankle_dorsiflexion_symmetry_percent=7.8,
        overall_symmetry_score=87.5
    )
    
    # 関節角度
    joint_angles = JointAngles(
        hip_flexion_deg=[25, 30, 35, 40, 35, 30, 25, 20, 25],
        hip_abduction_deg=[5, 8, 6, 4, 7, 9, 5, 6, 5],
        knee_flexion_deg=[15, 45, 60, 55, 40, 25, 15, 10, 15],
        ankle_dorsiflexion_deg=[0, 5, 10, 8, 2, -5, 0, 2, 0],
        pelvic_drop_deg=[1, 2, 1, -1, 2, 3, 1, 0, 1],
        frame_timestamps=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6]
    )
    
    # 歩行周期
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
    
    # 推奨事項
    recommendations = [
        "歩行対称性は良好です。現在の活動レベルを維持してください",
        "左右の歩幅差が軽度あります。バランス訓練を検討してください",
        "関節可動域は正常範囲内です",
        "歩行速度は標準的です。継続的な運動を推奨します"
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


async def test_pdf_generation():
    """PDFレポート生成テスト"""
    print("🧪 Testing PDF Report Generation...")
    
    try:
        report_generator = ReportGenerator()
        analysis_result = create_mock_analysis_result()
        
        patient_info = {
            "patient_id": "TEST_001",
            "height_cm": 170,
            "age": 30,
            "gender": "male"
        }
        
        pdf_path = await report_generator.generate_pdf_report(
            analysis_result, patient_info
        )
        
        if os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path)
            print(f"✅ PDF report generated successfully")
            print(f"   - File path: {pdf_path}")
            print(f"   - File size: {file_size / 1024:.1f} KB")
            return True
        else:
            print("❌ PDF file was not created")
            return False
            
    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        return False


async def test_png_generation():
    """PNG画像生成テスト"""
    print("🧪 Testing PNG Summary Generation...")
    
    try:
        report_generator = ReportGenerator()
        analysis_result = create_mock_analysis_result()
        
        png_path = await report_generator.generate_png_summary(
            analysis_result, size=(1200, 800)
        )
        
        if os.path.exists(png_path):
            file_size = os.path.getsize(png_path)
            print(f"✅ PNG summary generated successfully")
            print(f"   - File path: {png_path}")
            print(f"   - File size: {file_size / 1024:.1f} KB")
            return True
        else:
            print("❌ PNG file was not created")
            return False
            
    except Exception as e:
        print(f"❌ PNG generation failed: {e}")
        return False


async def test_base64_generation():
    """Base64画像生成テスト"""
    print("🧪 Testing Base64 Image Generation...")
    
    try:
        report_generator = ReportGenerator()
        analysis_result = create_mock_analysis_result()
        
        base64_data = await report_generator.generate_base64_image(analysis_result)
        
        if base64_data and base64_data.startswith("data:image/png;base64,"):
            data_size = len(base64_data)
            print(f"✅ Base64 image generated successfully")
            print(f"   - Data size: {data_size / 1024:.1f} KB")
            print(f"   - Format: PNG (Base64 encoded)")
            return True
        else:
            print("❌ Base64 data was not generated properly")
            return False
            
    except Exception as e:
        print(f"❌ Base64 generation failed: {e}")
        return False


async def test_report_initialization():
    """レポート生成器の初期化テスト"""
    print("🧪 Testing Report Generator Initialization...")
    
    try:
        report_generator = ReportGenerator()
        
        # 必要なディレクトリが作成されているか確認
        if os.path.exists(report_generator.output_dir):
            print("✅ Report generator initialized successfully")
            print(f"   - Output directory: {report_generator.output_dir}")
            print(f"   - Colors configured: {len(report_generator.COLORS)} colors")
            return True
        else:
            print("❌ Output directory was not created")
            return False
            
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False


async def run_all_tests():
    """全テスト実行"""
    print("🚀 Starting Report Generation Tests\n")
    
    tests = [
        ("Report Generator Initialization", test_report_initialization),
        ("PDF Report Generation", test_pdf_generation),
        ("PNG Summary Generation", test_png_generation),
        ("Base64 Image Generation", test_base64_generation),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        result = await test_func()
        results.append((test_name, result))
    
    print("\n" + "="*50)
    print("📊 Report Generation Test Results")
    print("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All report generation tests passed!")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    return passed == len(results)


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)