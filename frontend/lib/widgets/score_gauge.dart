import 'package:flutter/material.dart';
import 'package:gait_analysis_app/utils/constants.dart';
import 'package:gait_analysis_app/utils/app_theme.dart';
import 'dart:math' as math;

class ScoreGauge extends StatefulWidget {
  final double score;
  final String title;
  final double size;
  final bool animated;

  const ScoreGauge({
    Key? key,
    required this.score,
    required this.title,
    this.size = 100,
    this.animated = true,
  }) : super(key: key);

  @override
  _ScoreGaugeState createState() => _ScoreGaugeState();
}

class _ScoreGaugeState extends State<ScoreGauge>
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
    
    _animation = Tween<double>(
      begin: 0.0,
      end: widget.score / 100.0,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOutCubic,
    ));

    if (widget.animated) {
      _animationController.forward();
    } else {
      _animationController.value = 1.0;
    }
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        SizedBox(
          width: widget.size,
          height: widget.size,
          child: AnimatedBuilder(
            animation: _animation,
            builder: (context, child) {
              return CustomPaint(
                painter: ScoreGaugePainter(
                  progress: _animation.value,
                  score: widget.score,
                ),
              );
            },
          ),
        ),
        const SizedBox(height: 8),
        Text(
          widget.title,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}

class ScoreGaugePainter extends CustomPainter {
  final double progress;
  final double score;

  ScoreGaugePainter({
    required this.progress,
    required this.score,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = math.min(size.width, size.height) / 2 - 10;
    
    // 背景円
    final backgroundPaint = Paint()
      ..color = Colors.white.withOpacity(0.2)
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
    
    const startAngle = -math.pi / 2; // 12時から開始
    final sweepAngle = 2 * math.pi * progress;
    
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
          color: Colors.white,
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
    
    // 評価ラベル
    final label = _getScoreLabel(score);
    final labelText = TextPainter(
      text: TextSpan(
        text: label,
        style: TextStyle(
          color: Colors.white70,
          fontSize: radius * 0.15,
          fontWeight: FontWeight.w500,
        ),
      ),
      textDirection: TextDirection.ltr,
    );
    
    labelText.layout();
    labelText.paint(
      canvas,
      Offset(
        center.dx - labelText.width / 2,
        center.dy + scoreText.height / 2 - 5,
      ),
    );
  }

  Color _getScoreColor(double score) {
    if (score >= AppConstants.excellentScoreThreshold) {
      return AppColors.excellentScore;
    } else if (score >= AppConstants.goodScoreThreshold) {
      return AppColors.goodScore;
    } else if (score >= AppConstants.fairScoreThreshold) {
      return AppColors.fairScore;
    } else {
      return AppColors.poorScore;
    }
  }

  String _getScoreLabel(double score) {
    if (score >= AppConstants.excellentScoreThreshold) {
      return '優秀';
    } else if (score >= AppConstants.goodScoreThreshold) {
      return '良好';
    } else if (score >= AppConstants.fairScoreThreshold) {
      return '普通';
    } else {
      return '要改善';
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return true;
  }
}