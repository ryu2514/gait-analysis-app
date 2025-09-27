import 'package:flutter/material.dart';
import 'package:gait_analysis_app/models/gait_analysis_models.dart';
import 'package:gait_analysis_app/utils/constants.dart';
import 'package:gait_analysis_app/utils/app_theme.dart';
import 'dart:math' as math;

class SymmetryComparison extends StatefulWidget {
  final SymmetryIndices symmetryIndices;

  const SymmetryComparison({
    Key? key,
    required this.symmetryIndices,
  }) : super(key: key);

  @override
  _SymmetryComparisonState createState() => _SymmetryComparisonState();
}

class _SymmetryComparisonState extends State<SymmetryComparison>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );
    _animation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );
    _animationController.forward();
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.balance, color: AppColors.primary),
                const SizedBox(width: 8),
                const Text(
                  '歩行対称性',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: _getOverallSymmetryColor().withOpacity(0.2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    _getOverallSymmetryLabel(),
                    style: TextStyle(
                      color: _getOverallSymmetryColor(),
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
            
            const SizedBox(height: 16),
            
            // 対称性スコア表示
            _buildSymmetryScore(),
            
            const SizedBox(height: 24),
            
            // 詳細対称性指標
            _buildDetailedSymmetryMetrics(),
            
            const SizedBox(height: 16),
            
            // 左右比較可視化
            _buildLeftRightComparison(),
          ],
        ),
      ),
    );
  }

  Widget _buildSymmetryScore() {
    return AnimatedBuilder(
      animation: _animation,
      builder: (context, child) {
        return Row(
          children: [
            // 対称性スコア円形表示
            SizedBox(
              width: 100,
              height: 100,
              child: CustomPaint(
                painter: SymmetryScorePainter(
                  score: widget.symmetryIndices.overallSymmetryScore,
                  progress: _animation.value,
                ),
              ),
            ),
            
            const SizedBox(width: 24),
            
            // スコア詳細
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    '総合対称性スコア',
                    style: TextStyle(
                      fontSize: 14,
                      color: AppColors.textSecondary,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${widget.symmetryIndices.overallSymmetryScore.toStringAsFixed(1)}点',
                    style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: AppColors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    _getSymmetryDescription(),
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppColors.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildDetailedSymmetryMetrics() {
    final metrics = [
      {
        'title': '歩幅対称性',
        'value': widget.symmetryIndices.stepLengthSymmetryPercent,
        'icon': Icons.straighten,
        'optimal': 5.0,
      },
      {
        'title': '立脚時間対称性',
        'value': widget.symmetryIndices.stanceTimeSymmetryPercent,
        'icon': Icons.timer,
        'optimal': 5.0,
      },
      {
        'title': '遊脚時間対称性',
        'value': widget.symmetryIndices.swingTimeSymmetryPercent,
        'icon': Icons.schedule,
        'optimal': 5.0,
      },
      {
        'title': '股関節対称性',
        'value': widget.symmetryIndices.hipFlexionSymmetryPercent,
        'icon': Icons.accessibility_new,
        'optimal': 10.0,
      },
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '詳細指標',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 12),
        ...metrics.map((metric) => _buildSymmetryMetricRow(
          title: metric['title'] as String,
          value: metric['value'] as double,
          icon: metric['icon'] as IconData,
          optimalThreshold: metric['optimal'] as double,
        )),
      ],
    );
  }

  Widget _buildSymmetryMetricRow({
    required String title,
    required double value,
    required IconData icon,
    required double optimalThreshold,
  }) {
    final isOptimal = value <= optimalThreshold;
    final color = isOptimal ? AppColors.success : AppColors.warning;
    
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, color: color, size: 16),
          ),
          
          const SizedBox(width: 12),
          
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 2),
                Row(
                  children: [
                    Text(
                      '${value.toStringAsFixed(1)}%',
                      style: TextStyle(
                        fontSize: 12,
                        color: color,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      isOptimal ? '良好' : '要注意',
                      style: TextStyle(
                        fontSize: 10,
                        color: color,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          
          // 対称性レベル表示
          _buildSymmetryLevel(value, optimalThreshold),
        ],
      ),
    );
  }

  Widget _buildSymmetryLevel(double value, double threshold) {
    final level = value <= threshold ? 3 : value <= threshold * 2 ? 2 : 1;
    
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(3, (index) {
        final isActive = index < level;
        return Container(
          margin: const EdgeInsets.only(left: 2),
          width: 6,
          height: 16,
          decoration: BoxDecoration(
            color: isActive 
                ? (level == 3 ? AppColors.success : level == 2 ? AppColors.warning : AppColors.error)
                : AppColors.textSecondary.withOpacity(0.3),
            borderRadius: BorderRadius.circular(3),
          ),
        );
      }),
    );
  }

  Widget _buildLeftRightComparison() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '左右比較',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 12),
        
        // 左右の人型アイコンと非対称性表示
        Row(
          children: [
            Expanded(
              child: _buildSideIndicator(
                side: '左脚',
                color: AppColors.primary,
                asymmetryLevel: _calculateAsymmetryLevel('left'),
              ),
            ),
            
            const SizedBox(width: 24),
            
            // 中央のバランス表示
            Column(
              children: [
                Icon(
                  Icons.balance,
                  color: _getOverallSymmetryColor(),
                  size: 32,
                ),
                const SizedBox(height: 4),
                Text(
                  _getBalanceStatus(),
                  style: TextStyle(
                    fontSize: 10,
                    color: _getOverallSymmetryColor(),
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
            
            const SizedBox(width: 24),
            
            Expanded(
              child: _buildSideIndicator(
                side: '右脚',
                color: AppColors.accent,
                asymmetryLevel: _calculateAsymmetryLevel('right'),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildSideIndicator({
    required String side,
    required Color color,
    required double asymmetryLevel,
  }) {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: color.withOpacity(0.3),
              width: 1,
            ),
          ),
          child: Column(
            children: [
              Icon(
                Icons.directions_walk,
                color: color,
                size: 32,
              ),
              const SizedBox(height: 8),
              Text(
                side,
                style: TextStyle(
                  fontSize: 12,
                  color: color,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
        
        const SizedBox(height: 8),
        
        // 非対称性レベル表示
        Container(
          width: double.infinity,
          height: 4,
          decoration: BoxDecoration(
            color: AppColors.textSecondary.withOpacity(0.2),
            borderRadius: BorderRadius.circular(2),
          ),
          child: FractionallySizedBox(
            alignment: Alignment.centerLeft,
            widthFactor: asymmetryLevel / 100,
            child: Container(
              decoration: BoxDecoration(
                color: color,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
        ),
      ],
    );
  }

  String _getSymmetryDescription() {
    final score = widget.symmetryIndices.overallSymmetryScore;
    if (score >= 90) {
      return '優秀な歩行対称性です';
    } else if (score >= 80) {
      return '良好な歩行対称性です';
    } else if (score >= 70) {
      return '普通の歩行対称性です';
    } else {
      return '対称性の改善が必要です';
    }
  }

  Color _getOverallSymmetryColor() {
    final score = widget.symmetryIndices.overallSymmetryScore;
    if (score >= 90) return AppColors.excellentScore;
    if (score >= 80) return AppColors.goodScore;
    if (score >= 70) return AppColors.fairScore;
    return AppColors.poorScore;
  }

  String _getOverallSymmetryLabel() {
    final score = widget.symmetryIndices.overallSymmetryScore;
    if (score >= 90) return '優秀';
    if (score >= 80) return '良好';
    if (score >= 70) return '普通';
    return '要改善';
  }

  String _getBalanceStatus() {
    final avgAsymmetry = (
      widget.symmetryIndices.stepLengthSymmetryPercent +
      widget.symmetryIndices.stanceTimeSymmetryPercent
    ) / 2;
    
    if (avgAsymmetry <= 5) return 'バランス良好';
    if (avgAsymmetry <= 10) return '軽度の非対称';
    return '要注意';
  }

  double _calculateAsymmetryLevel(String side) {
    // 簡易的な非対称性レベル計算
    final avgAsymmetry = (
      widget.symmetryIndices.stepLengthSymmetryPercent +
      widget.symmetryIndices.stanceTimeSymmetryPercent
    ) / 2;
    
    return math.min(100, avgAsymmetry * 5);
  }
}

class SymmetryScorePainter extends CustomPainter {
  final double score;
  final double progress;

  SymmetryScorePainter({required this.score, required this.progress});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = math.min(size.width, size.height) / 2 - 10;
    
    // 背景円
    final backgroundPaint = Paint()
      ..color = AppColors.textSecondary.withOpacity(0.2)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 8
      ..strokeCap = StrokeCap.round;
    
    canvas.drawCircle(center, radius, backgroundPaint);
    
    // プログレス円
    final progressPaint = Paint()
      ..color = _getScoreColor(score)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 8
      ..strokeCap = StrokeCap.round;
    
    const startAngle = -math.pi / 2;
    final sweepAngle = 2 * math.pi * (score / 100) * progress;
    
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      startAngle,
      sweepAngle,
      false,
      progressPaint,
    );
    
    // スコアテキスト
    final scoreText = TextPainter(
      text: TextSpan(
        text: score.toInt().toString(),
        style: TextStyle(
          color: AppColors.textPrimary,
          fontSize: radius * 0.4,
          fontWeight: FontWeight.bold,
        ),
      ),
      textDirection: TextDirection.ltr,
    );
    
    scoreText.layout();
    scoreText.paint(
      canvas,
      Offset(
        center.dx - scoreText.width / 2,
        center.dy - scoreText.height / 2,
      ),
    );
  }

  Color _getScoreColor(double score) {
    if (score >= 90) return AppColors.excellentScore;
    if (score >= 80) return AppColors.goodScore;
    if (score >= 70) return AppColors.fairScore;
    return AppColors.poorScore;
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}