"""
サービス層のテスト
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app.services.gait_cycle_detector import GaitCycleDetector
from app.services.spatiotemporal_analyzer import SpatiotemporalAnalyzer
from app.services.joint_angle_calculator import JointAngleCalculator
from app.services.symmetry_analyzer import SymmetryAnalyzer
from app.services.data_service import DataService
from app.services.report_generator import ReportGenerator
from app.models.gait_models import GaitCycle, JointAngles, SymmetryIndices


class TestGaitCycleDetector:
    """歩行周期検出器のテスト"""
    
    def test_detect_gait_cycles_success(self, sample_landmarks_data):
        """歩行周期検出の正常系テスト"""
        detector = GaitCycleDetector()
        
        gait_cycles = detector.detect_gait_cycles(sample_landmarks_data, fps=30.0)
        
        assert isinstance(gait_cycles, list)
        assert len(gait_cycles) > 0
        
        # 最初の歩行周期の検証
        first_cycle = gait_cycles[0]
        assert isinstance(first_cycle, GaitCycle)
        assert first_cycle.cycle_id is not None
        assert first_cycle.duration_seconds > 0
        assert first_cycle.side in ["left", "right"]
    
    def test_detect_gait_cycles_insufficient_data(self):
        """データ不足時の歩行周期検出テスト"""
        detector = GaitCycleDetector()
        
        # 5フレーム分の不十分なデータ
        insufficient_data = [
            {
                'frame': i,
                'timestamp': i / 30.0,
                'landmarks': [{'x': 0.5, 'y': 0.5, 'z': 0.0, 'visibility': 0.9} for _ in range(33)]
            }
            for i in range(5)
        ]
        
        gait_cycles = detector.detect_gait_cycles(insufficient_data, fps=30.0)
        
        # データが不十分な場合は空のリストまたは少ない検出数
        assert isinstance(gait_cycles, list)
    
    def test_detect_gait_cycles_empty_data(self):
        """空データでの歩行周期検出テスト"""
        detector = GaitCycleDetector()
        
        gait_cycles = detector.detect_gait_cycles([], fps=30.0)
        
        assert isinstance(gait_cycles, list)
        assert len(gait_cycles) == 0


class TestSpatiotemporalAnalyzer:
    """時空間パラメータ分析器のテスト"""
    
    def test_analyze_spatiotemporal_parameters_success(self):
        """時空間パラメータ分析の正常系テスト"""
        analyzer = SpatiotemporalAnalyzer()
        
        # テスト用歩行周期データ
        gait_cycles = [
            GaitCycle(
                cycle_id="L_001",
                start_frame=0,
                end_frame=30,
                duration_seconds=1.0,
                side="left",
                step_length_m=0.65,
                step_width_m=0.10,
                stance_time_seconds=0.65,
                swing_time_seconds=0.35,
                stance_ratio=0.65,
                hip_flexion_peak_deg=30.0,
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
                step_length_m=0.67,
                step_width_m=0.10,
                stance_time_seconds=0.67,
                swing_time_seconds=0.33,
                stance_ratio=0.67,
                hip_flexion_peak_deg=32.0,
                knee_flexion_peak_deg=58.0,
                ankle_dorsiflexion_peak_deg=8.0,
                phase_timings={}
            )
        ]
        
        params = analyzer.analyze_spatiotemporal_parameters(gait_cycles, scale_factor=1.0)
        
        assert params is not None
        assert params.gait_speed_ms > 0
        assert params.cadence_steps_per_min > 0
        assert params.stride_length_m > 0
        assert params.left_step_length_m > 0
        assert params.right_step_length_m > 0
    
    def test_analyze_spatiotemporal_parameters_empty_cycles(self):
        """空の歩行周期での分析テスト"""
        analyzer = SpatiotemporalAnalyzer()
        
        # 空のリストでは例外が発生するか、デフォルト値が返される
        with pytest.raises(Exception):
            analyzer.analyze_spatiotemporal_parameters([], scale_factor=1.0)
    
    def test_analyze_spatiotemporal_parameters_single_side(self):
        """片脚のみの歩行周期での分析テスト"""
        analyzer = SpatiotemporalAnalyzer()
        
        # 左脚のみの歩行周期
        left_only_cycles = [
            GaitCycle(
                cycle_id="L_001",
                start_frame=0,
                end_frame=30,
                duration_seconds=1.0,
                side="left",
                step_length_m=0.65,
                step_width_m=0.10,
                stance_time_seconds=0.65,
                swing_time_seconds=0.35,
                stance_ratio=0.65,
                hip_flexion_peak_deg=30.0,
                knee_flexion_peak_deg=60.0,
                ankle_dorsiflexion_peak_deg=10.0,
                phase_timings={}
            )
        ]
        
        params = analyzer.analyze_spatiotemporal_parameters(left_only_cycles, scale_factor=1.0)
        
        assert params is not None
        assert params.left_step_length_m > 0
        # 右脚データは0またはNoneになる可能性がある


class TestJointAngleCalculator:
    """関節角度計算器のテスト"""
    
    def test_calculate_joint_angles_success(self, sample_landmarks_data):
        """関節角度計算の正常系テスト"""
        calculator = JointAngleCalculator()
        
        joint_angles = calculator.calculate_joint_angles(sample_landmarks_data)
        
        assert isinstance(joint_angles, JointAngles)
        assert joint_angles.frame_timestamps is not None
        assert len(joint_angles.frame_timestamps) > 0
        
        # 各関節角度データの確認
        if joint_angles.hip_flexion_deg:
            assert len(joint_angles.hip_flexion_deg) == len(joint_angles.frame_timestamps)
        if joint_angles.knee_flexion_deg:
            assert len(joint_angles.knee_flexion_deg) == len(joint_angles.frame_timestamps)
        if joint_angles.ankle_dorsiflexion_deg:
            assert len(joint_angles.ankle_dorsiflexion_deg) == len(joint_angles.frame_timestamps)
    
    def test_calculate_joint_angles_empty_data(self):
        """空データでの関節角度計算テスト"""
        calculator = JointAngleCalculator()
        
        joint_angles = calculator.calculate_joint_angles([])
        
        assert isinstance(joint_angles, JointAngles)
        assert joint_angles.frame_timestamps == [] or joint_angles.frame_timestamps is None
    
    def test_calculate_joint_angles_low_visibility(self):
        """低可視性ランドマークでの関節角度計算テスト"""
        calculator = JointAngleCalculator()
        
        # 可視性の低いランドマークデータ
        low_visibility_data = [
            {
                'frame': 0,
                'timestamp': 0.0,
                'landmarks': [
                    {'x': 0.5, 'y': 0.5, 'z': 0.0, 'visibility': 0.1}  # 低可視性
                    for _ in range(33)
                ]
            }
        ]
        
        joint_angles = calculator.calculate_joint_angles(low_visibility_data)
        
        # 低可視性の場合、計算されないか、信頼性フラグが設定される
        assert isinstance(joint_angles, JointAngles)


class TestSymmetryAnalyzer:
    """対称性分析器のテスト"""
    
    def test_analyze_gait_symmetry_success(self):
        """対称性分析の正常系テスト"""
        analyzer = SymmetryAnalyzer()
        
        # バランスの取れた歩行周期データ
        balanced_cycles = [
            GaitCycle(
                cycle_id="L_001",
                start_frame=0,
                end_frame=30,
                duration_seconds=1.0,
                side="left",
                step_length_m=0.65,
                step_width_m=0.10,
                stance_time_seconds=0.65,
                swing_time_seconds=0.35,
                stance_ratio=0.65,
                hip_flexion_peak_deg=30.0,
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
                step_length_m=0.65,  # 同じ値で対称性をテスト
                step_width_m=0.10,
                stance_time_seconds=0.65,
                swing_time_seconds=0.35,
                stance_ratio=0.65,
                hip_flexion_peak_deg=30.0,
                knee_flexion_peak_deg=60.0,
                ankle_dorsiflexion_peak_deg=10.0,
                phase_timings={}
            )
        ]
        
        symmetry = analyzer.analyze_gait_symmetry(balanced_cycles)
        
        assert isinstance(symmetry, SymmetryIndices)
        assert symmetry.overall_symmetry_score >= 0
        assert symmetry.overall_symmetry_score <= 100
        
        # 完全に対称なデータでは対称性スコアが高い
        assert symmetry.step_length_symmetry_percent < 5.0  # 5%未満の非対称性
    
    def test_analyze_gait_symmetry_asymmetric(self):
        """非対称歩行の分析テスト"""
        analyzer = SymmetryAnalyzer()
        
        # 非対称な歩行周期データ
        asymmetric_cycles = [
            GaitCycle(
                cycle_id="L_001",
                start_frame=0,
                end_frame=30,
                duration_seconds=1.0,
                side="left",
                step_length_m=0.50,  # 短い歩幅
                step_width_m=0.10,
                stance_time_seconds=0.60,
                swing_time_seconds=0.40,
                stance_ratio=0.60,
                hip_flexion_peak_deg=25.0,
                knee_flexion_peak_deg=55.0,
                ankle_dorsiflexion_peak_deg=8.0,
                phase_timings={}
            ),
            GaitCycle(
                cycle_id="R_001",
                start_frame=15,
                end_frame=45,
                duration_seconds=1.0,
                side="right",
                step_length_m=0.80,  # 長い歩幅
                step_width_m=0.10,
                stance_time_seconds=0.70,
                swing_time_seconds=0.30,
                stance_ratio=0.70,
                hip_flexion_peak_deg=35.0,
                knee_flexion_peak_deg=65.0,
                ankle_dorsiflexion_peak_deg=12.0,
                phase_timings={}
            )
        ]
        
        symmetry = analyzer.analyze_gait_symmetry(asymmetric_cycles)
        
        assert isinstance(symmetry, SymmetryIndices)
        # 非対称なデータでは非対称性パーセンテージが高い
        assert symmetry.step_length_symmetry_percent > 10.0
    
    def test_analyze_gait_symmetry_single_side(self):
        """片側のみの歩行データでの対称性分析テスト"""
        analyzer = SymmetryAnalyzer()
        
        # 左脚のみの歩行周期
        single_side_cycles = [
            GaitCycle(
                cycle_id="L_001",
                start_frame=0,
                end_frame=30,
                duration_seconds=1.0,
                side="left",
                step_length_m=0.65,
                step_width_m=0.10,
                stance_time_seconds=0.65,
                swing_time_seconds=0.35,
                stance_ratio=0.65,
                hip_flexion_peak_deg=30.0,
                knee_flexion_peak_deg=60.0,
                ankle_dorsiflexion_peak_deg=10.0,
                phase_timings={}
            )
        ]
        
        symmetry = analyzer.analyze_gait_symmetry(single_side_cycles)
        
        assert isinstance(symmetry, SymmetryIndices)
        # 片側のみの場合、変動性ベースの評価が行われる


class TestDataService:
    """データサービスのテスト"""
    
    @pytest.mark.asyncio
    async def test_save_analysis_result_success(self, sample_gait_analysis_response):
        """分析結果保存の正常系テスト"""
        data_service = DataService()
        
        with patch.object(data_service.db_manager, 'get_async_session') as mock_session:
            mock_session_instance = MagicMock()
            mock_session.__aenter__.return_value = mock_session_instance
            
            # 保存処理のモック
            mock_session_instance.add = MagicMock()
            mock_session_instance.flush = MagicMock()
            
            user_id = "test_user_001"
            
            # 実際のメソッドをパッチ
            with patch.object(data_service, '_log_action'):
                result_id = await data_service.save_analysis_result(
                    user_id=user_id,
                    analysis_result=sample_gait_analysis_response
                )
                
                # セッションのaddメソッドが呼ばれたことを確認
                mock_session_instance.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_analysis_result_success(self, sample_gait_analysis_response):
        """分析結果取得の正常系テスト"""
        data_service = DataService()
        
        with patch.object(data_service.db_manager, 'get_async_session') as mock_session:
            mock_session_instance = MagicMock()
            mock_session.__aenter__.return_value = mock_session_instance
            
            # クエリ結果のモック
            mock_gait_analysis = MagicMock()
            mock_gait_analysis.analysis_id = sample_gait_analysis_response.analysis_id
            mock_gait_analysis.analysis_date = sample_gait_analysis_response.timestamp
            mock_gait_analysis.overall_gait_score = sample_gait_analysis_response.overall_gait_score
            mock_gait_analysis.spatiotemporal_params = sample_gait_analysis_response.spatiotemporal_params.dict()
            mock_gait_analysis.symmetry_indices = sample_gait_analysis_response.symmetry_indices.dict()
            mock_gait_analysis.joint_angles = sample_gait_analysis_response.joint_angles.dict()
            mock_gait_analysis.gait_cycles = [cycle.dict() for cycle in sample_gait_analysis_response.gait_cycles]
            mock_gait_analysis.recommendations = sample_gait_analysis_response.recommendations
            
            mock_session_instance.query().filter().first.return_value = mock_gait_analysis
            
            # _convert_to_responseメソッドをパッチ
            with patch.object(data_service, '_convert_to_response', return_value=sample_gait_analysis_response):
                result = await data_service.get_analysis_result(
                    user_id="test_user_001",
                    analysis_id=sample_gait_analysis_response.analysis_id
                )
                
                assert result is not None
                assert result.analysis_id == sample_gait_analysis_response.analysis_id
    
    @pytest.mark.asyncio
    async def test_get_analysis_result_not_found(self):
        """存在しない分析結果取得のテスト"""
        data_service = DataService()
        
        with patch.object(data_service.db_manager, 'get_async_session') as mock_session:
            mock_session_instance = MagicMock()
            mock_session.__aenter__.return_value = mock_session_instance
            
            # 結果が見つからない場合
            mock_session_instance.query().filter().first.return_value = None
            
            result = await data_service.get_analysis_result(
                user_id="test_user_001",
                analysis_id="NONEXISTENT"
            )
            
            assert result is None


class TestReportGenerator:
    """レポート生成器のテスト"""
    
    @pytest.mark.asyncio
    async def test_generate_pdf_report_success(self, sample_gait_analysis_response):
        """PDFレポート生成の正常系テスト"""
        generator = ReportGenerator()
        
        # ファイル操作をモック
        with patch('matplotlib.pyplot.savefig'), \
             patch('matplotlib.pyplot.close'), \
             patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=1024):
            
            pdf_path = await generator.generate_pdf_report(
                analysis_result=sample_gait_analysis_response,
                patient_info={"patient_id": "TEST_001", "height_cm": 170}
            )
            
            assert pdf_path is not None
            assert pdf_path.endswith('.pdf')
    
    @pytest.mark.asyncio
    async def test_generate_png_summary_success(self, sample_gait_analysis_response):
        """PNG画像生成の正常系テスト"""
        generator = ReportGenerator()
        
        with patch('matplotlib.pyplot.savefig'), \
             patch('matplotlib.pyplot.close'), \
             patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=2048):
            
            png_path = await generator.generate_png_summary(
                analysis_result=sample_gait_analysis_response,
                size=(1200, 800)
            )
            
            assert png_path is not None
            assert png_path.endswith('.png')
    
    @pytest.mark.asyncio
    async def test_generate_base64_image_success(self, sample_gait_analysis_response):
        """Base64画像生成の正常系テスト"""
        generator = ReportGenerator()
        
        with patch.object(generator, 'generate_png_summary', return_value='/tmp/test.png'), \
             patch('builtins.open', MagicMock()), \
             patch('base64.b64encode', return_value=b'dGVzdA=='), \
             patch('os.remove'):
            
            base64_data = await generator.generate_base64_image(
                analysis_result=sample_gait_analysis_response
            )
            
            assert base64_data is not None
            assert base64_data.startswith('data:image/png;base64,')


class TestIntegrationScenarios:
    """統合シナリオのテスト"""
    
    @pytest.mark.asyncio
    async def test_complete_analysis_workflow(self, sample_landmarks_data):
        """完全な分析ワークフローのテスト"""
        # 各コンポーネントを順番に実行
        
        # 1. 歩行周期検出
        detector = GaitCycleDetector()
        gait_cycles = detector.detect_gait_cycles(sample_landmarks_data, fps=30.0)
        assert len(gait_cycles) > 0
        
        # 2. 時空間パラメータ分析
        spatiotemporal_analyzer = SpatiotemporalAnalyzer()
        spatiotemporal_params = spatiotemporal_analyzer.analyze_spatiotemporal_parameters(
            gait_cycles, scale_factor=1.0
        )
        assert spatiotemporal_params is not None
        
        # 3. 関節角度計算
        joint_calculator = JointAngleCalculator()
        joint_angles = joint_calculator.calculate_joint_angles(sample_landmarks_data)
        assert joint_angles is not None
        
        # 4. 対称性分析
        symmetry_analyzer = SymmetryAnalyzer()
        symmetry_indices = symmetry_analyzer.analyze_gait_symmetry(gait_cycles, joint_angles)
        assert symmetry_indices is not None
        
        # 全てのコンポーネントが正常に動作することを確認
        assert symmetry_indices.overall_symmetry_score >= 0