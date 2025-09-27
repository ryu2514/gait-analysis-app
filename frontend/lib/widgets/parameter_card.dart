import 'package:flutter/material.dart';
import 'package:gait_analysis_app/utils/constants.dart';
import 'package:gait_analysis_app/utils/app_theme.dart';

class ParameterCard extends StatelessWidget {
  final String title;
  final String value;
  final String unit;
  final String? subtitle;
  final IconData icon;
  final Color color;
  final String? evaluation;
  final bool showTrend;
  final double? trendValue;

  const ParameterCard({
    Key? key,
    required this.title,
    required this.value,
    required this.unit,
    this.subtitle,
    required this.icon,
    required this.color,
    this.evaluation,
    this.showTrend = false,
    this.trendValue,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 4,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              color.withOpacity(0.1),
              color.withOpacity(0.05),
            ],
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ヘッダー行
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(icon, color: color, size: 20),
                ),
                if (evaluation != null)
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: _getEvaluationColor(evaluation!).withOpacity(0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      evaluation!,
                      style: TextStyle(
                        color: _getEvaluationColor(evaluation!),
                        fontSize: 10,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
              ],
            ),
            
            const SizedBox(height: 12),
            
            // タイトル
            Text(
              title,
              style: const TextStyle(
                fontSize: 12,
                color: AppColors.textSecondary,
                fontWeight: FontWeight.w500,
              ),
            ),
            
            const SizedBox(height: 4),
            
            // 値と単位
            Row(
              crossAxisAlignment: CrossAxisAlignment.baseline,
              textBaseline: TextBaseline.alphabetic,
              children: [
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(width: 4),
                Text(
                  unit,
                  style: const TextStyle(
                    fontSize: 14,
                    color: AppColors.textSecondary,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
            
            // サブタイトル
            if (subtitle != null) ...[
              const SizedBox(height: 4),
              Text(
                subtitle!,
                style: const TextStyle(
                  fontSize: 11,
                  color: AppColors.textSecondary,
                ),
              ),
            ],
            
            // トレンド表示
            if (showTrend && trendValue != null) ...[
              const SizedBox(height: 8),
              Row(
                children: [
                  Icon(
                    trendValue! > 0 
                        ? Icons.trending_up 
                        : trendValue! < 0 
                            ? Icons.trending_down 
                            : Icons.trending_flat,
                    size: 16,
                    color: trendValue! > 0 
                        ? AppColors.success 
                        : trendValue! < 0 
                            ? AppColors.error 
                            : AppColors.textSecondary,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    '${trendValue!.abs().toStringAsFixed(1)}%',
                    style: TextStyle(
                      fontSize: 11,
                      color: trendValue! > 0 
                          ? AppColors.success 
                          : trendValue! < 0 
                              ? AppColors.error 
                              : AppColors.textSecondary,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  Color _getEvaluationColor(String evaluation) {
    switch (evaluation) {
      case '優秀':
        return AppColors.excellentScore;
      case '良好':
        return AppColors.goodScore;
      case '普通':
        return AppColors.fairScore;
      case '要改善':
        return AppColors.poorScore;
      default:
        return AppColors.textSecondary;
    }
  }
}

class MiniParameterCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color color;

  const MiniParameterCard({
    Key? key,
    required this.title,
    required this.value,
    required this.icon,
    required this.color,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: color.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 18),
          const SizedBox(height: 6),
          Text(
            value,
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            title,
            style: const TextStyle(
              fontSize: 10,
              color: AppColors.textSecondary,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}