import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:gait_analysis_app/models/gait_analysis_models.dart';
import 'package:gait_analysis_app/utils/constants.dart';
import 'package:gait_analysis_app/utils/app_theme.dart';
import 'package:gait_analysis_app/widgets/custom_app_bar.dart';
import 'package:gait_analysis_app/widgets/score_gauge.dart';
import 'package:gait_analysis_app/widgets/parameter_card.dart';
import 'package:gait_analysis_app/widgets/joint_angle_chart.dart';
import 'package:gait_analysis_app/widgets/symmetry_comparison.dart';
import 'package:gait_analysis_app/widgets/report_generator_dialog.dart';

class ResultsScreen extends StatefulWidget {
  final GaitAnalysisResponse analysisResult;

  const ResultsScreen({
    Key? key,
    required this.analysisResult,
  }) : super(key: key);

  @override
  _ResultsScreenState createState() => _ResultsScreenState();
}

class _ResultsScreenState extends State<ResultsScreen>
    with TickerProviderStateMixin {
  late TabController _tabController;
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );
    
    _animationController.forward();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: CustomAppBar(
        title: '分析結果',
        actions: [
          IconButton(
            icon: const Icon(Icons.share),
            onPressed: () => _shareResults(),
          ),
          IconButton(
            icon: const Icon(Icons.download),
            onPressed: () => _downloadReport(),
          ),
        ],
      ),
      body: FadeTransition(
        opacity: _fadeAnimation,
        child: Column(
          children: [
            // 総合スコア表示
            _buildOverallScoreSection(),
            
            // タブバー
            _buildTabBar(),
            
            // タブビュー
            Expanded(
              child: TabBarView(
                controller: _tabController,
                children: [
                  _buildOverviewTab(),
                  _buildParametersTab(),
                  _buildJointAnglesTab(),
                  _buildRecommendationsTab(),
                ],
              ),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _saveToHistory(),
        icon: const Icon(Icons.save),
        label: const Text('履歴に保存'),
      ),
    );
  }

  Widget _buildOverallScoreSection() {
    return Container(
      padding: const EdgeInsets.all(AppConstants.defaultPadding),
      decoration: BoxDecoration(
        gradient: AppTheme.primaryGradient,
        borderRadius: const BorderRadius.only(
          bottomLeft: Radius.circular(24),
          bottomRight: Radius.circular(24),
        ),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              // 総合スコア
              ScoreGauge(
                score: widget.analysisResult.overallGaitScore,
                title: '総合スコア',
                size: 120,
              ),
              
              // 品質指標
              Column(
                children: [
                  _buildMiniScore(
                    '動画品質',
                    widget.analysisResult.videoQualityScore,
                    Icons.videocam,
                  ),
                  const SizedBox(height: 12),
                  _buildMiniScore(
                    '検出精度',
                    widget.analysisResult.poseDetectionConfidence * 100,
                    Icons.my_location,
                  ),
                  const SizedBox(height: 12),
                  _buildMiniScore(
                    '歩行周期',
                    widget.analysisResult.gaitCyclesDetected.toDouble() * 10,
                    Icons.timeline,
                  ),
                ],
              ),
            ],
          ),
          
          const SizedBox(height: 16),
          
          // 処理情報
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildInfoItem(
                  Icons.timer,
                  '処理時間',
                  '${widget.analysisResult.processingTimeSeconds.toStringAsFixed(1)}秒',
                ),
                _buildInfoItem(
                  Icons.date_range,
                  '分析日時',
                  _formatDateTime(widget.analysisResult.timestamp),
                ),
                _buildInfoItem(
                  Icons.analytics,
                  '分析ID',
                  widget.analysisResult.analysisId.substring(0, 8),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMiniScore(String title, double score, IconData icon) {
    final color = AppTheme.getScoreColor(score);
    
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.2),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        children: [
          Icon(icon, color: Colors.white, size: 20),
          const SizedBox(height: 4),
          Text(
            '${score.toInt()}',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          Text(
            title,
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 10,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoItem(IconData icon, String label, String value) {
    return Column(
      children: [
        Icon(icon, color: Colors.white70, size: 16),
        const SizedBox(height: 4),
        Text(
          value,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 12,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: const TextStyle(
            color: Colors.white70,
            fontSize: 10,
          ),
        ),
      ],
    );
  }

  Widget _buildTabBar() {
    return Container(
      color: Colors.white,
      child: TabBar(
        controller: _tabController,
        tabs: const [
          Tab(text: '概要', icon: Icon(Icons.dashboard, size: 20)),
          Tab(text: 'パラメータ', icon: Icon(Icons.straighten, size: 20)),
          Tab(text: '関節角度', icon: Icon(Icons.show_chart, size: 20)),
          Tab(text: '改善提案', icon: Icon(Icons.lightbulb, size: 20)),
        ],
        labelColor: AppColors.primary,
        unselectedLabelColor: AppColors.textSecondary,
        indicatorColor: AppColors.primary,
        labelStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
      ),
    );
  }

  Widget _buildOverviewTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppConstants.defaultPadding),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 対称性比較
          if (widget.analysisResult.symmetryIndices != null)
            SymmetryComparison(
              symmetryIndices: widget.analysisResult.symmetryIndices!,
            ),
          
          const SizedBox(height: 24),
          
          // 主要指標カード
          if (widget.analysisResult.spatiotemporalParams != null)
            _buildKeyParametersGrid(),
          
          const SizedBox(height: 24),
          
          // 歩行周期概要
          _buildGaitCyclesOverview(),
        ],
      ),
    );
  }

  Widget _buildKeyParametersGrid() {
    final params = widget.analysisResult.spatiotemporalParams!;
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '主要指標',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        
        GridView.count(
          crossAxisCount: 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
          childAspectRatio: 1.5,
          children: [
            ParameterCard(
              title: '歩行速度',
              value: params.gaitSpeedMs.toStringAsFixed(2),
              unit: 'm/s',
              subtitle: '${params.gaitSpeedKmh.toStringAsFixed(1)} km/h',
              icon: Icons.speed,
              color: AppColors.primary,
              evaluation: params.speedEvaluation,
            ),
            ParameterCard(
              title: 'ケイデンス',
              value: params.cadenceStepsPerMin.toString(),
              unit: '歩/分',
              subtitle: 'リズム',
              icon: Icons.music_note,
              color: AppColors.accent,
            ),
            ParameterCard(
              title: 'ストライド長',
              value: params.strideLengthM.toStringAsFixed(2),
              unit: 'm',
              subtitle: '1歩の距離',
              icon: Icons.straighten,
              color: AppColors.warning,
            ),
            ParameterCard(
              title: '両脚支持時間',
              value: (params.doubleSupportTimeS * 1000).toStringAsFixed(0),
              unit: 'ms',
              subtitle: '安定性',
              icon: Icons.balance,
              color: AppColors.success,
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildGaitCyclesOverview() {
    final cycles = widget.analysisResult.gaitCycles;
    
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.timeline, color: AppColors.primary),
                const SizedBox(width: 8),
                const Text(
                  '歩行周期',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            
            Text('検出された歩行周期: ${cycles.length}個'),
            const SizedBox(height: 8),
            
            if (cycles.isNotEmpty) ...[
              Text('平均周期時間: ${_calculateAverageCycleTime(cycles).toStringAsFixed(2)}秒'),
              const SizedBox(height: 8),
              Text('左右バランス: ${_calculateLeftRightBalance(cycles)}'),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildParametersTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppConstants.defaultPadding),
      child: Column(
        children: [
          if (widget.analysisResult.spatiotemporalParams != null)
            _buildDetailedParameters(),
        ],
      ),
    );
  }

  Widget _buildDetailedParameters() {
    final params = widget.analysisResult.spatiotemporalParams!;
    
    return Column(
      children: [
        _buildParameterSection(
          '時間的パラメータ',
          Icons.timer,
          [
            _buildParameterRow('ストライド時間', '${params.strideTimeS.toStringAsFixed(2)}秒'),
            _buildParameterRow('左脚立脚時間', '${params.leftStanceTimeS.toStringAsFixed(2)}秒'),
            _buildParameterRow('右脚立脚時間', '${params.rightStanceTimeS.toStringAsFixed(2)}秒'),
            _buildParameterRow('両脚支持時間', '${params.doubleSupportTimeS.toStringAsFixed(2)}秒'),
          ],
        ),
        
        const SizedBox(height: 24),
        
        _buildParameterSection(
          '空間的パラメータ',
          Icons.straighten,
          [
            _buildParameterRow('左脚歩幅', '${params.leftStepLengthM.toStringAsFixed(2)}m'),
            _buildParameterRow('右脚歩幅', '${params.rightStepLengthM.toStringAsFixed(2)}m'),
            _buildParameterRow('ストライド長', '${params.strideLengthM.toStringAsFixed(2)}m'),
          ],
        ),
      ],
    );
  }

  Widget _buildParameterSection(String title, IconData icon, List<Widget> children) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: AppColors.primary),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            ...children,
          ],
        ),
      ),
    );
  }

  Widget _buildParameterRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label),
          Text(
            value,
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }

  Widget _buildJointAnglesTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppConstants.defaultPadding),
      child: Column(
        children: [
          if (widget.analysisResult.jointAngles != null)
            JointAngleChart(
              jointAngles: widget.analysisResult.jointAngles!,
            ),
        ],
      ),
    );
  }

  Widget _buildRecommendationsTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppConstants.defaultPadding),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '改善提案',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          
          ...widget.analysisResult.recommendations.asMap().entries.map(
            (entry) => _buildRecommendationCard(entry.key + 1, entry.value),
          ),
        ],
      ),
    );
  }

  Widget _buildRecommendationCard(int index, String recommendation) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: AppColors.primary,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Center(
                child: Text(
                  '$index',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Text(
                recommendation,
                style: const TextStyle(fontSize: 14),
              ),
            ),
          ],
        ),
      ),
    );
  }

  double _calculateAverageCycleTime(List<GaitCycle> cycles) {
    if (cycles.isEmpty) return 0.0;
    return cycles.map((c) => c.durationSeconds).reduce((a, b) => a + b) / cycles.length;
  }

  String _calculateLeftRightBalance(List<GaitCycle> cycles) {
    final leftCount = cycles.where((c) => c.isLeft).length;
    final rightCount = cycles.where((c) => c.isRight).length;
    
    if (leftCount == 0 && rightCount == 0) return '不明';
    if (leftCount == rightCount) return '均等';
    
    final ratio = (leftCount / (leftCount + rightCount) * 100).toInt();
    return '左${ratio}% : 右${100-ratio}%';
  }

  String _formatDateTime(DateTime dateTime) {
    return '${dateTime.month}/${dateTime.day} ${dateTime.hour}:${dateTime.minute.toString().padLeft(2, '0')}';
  }

  void _shareResults() {
    // TODO: 結果共有機能
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('共有機能は実装中です')),
    );
  }

  void _downloadReport() {
    showReportGeneratorDialog(
      context,
      widget.analysisResult,
      patientInfo: {
        // TODO: 実際の患者情報を設定
        'patient_id': 'DEMO_001',
        'height_cm': 170,
        'age': 30,
      },
    );
  }

  void _saveToHistory() {
    // TODO: 履歴保存機能
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('履歴に保存しました')),
    );
  }
}