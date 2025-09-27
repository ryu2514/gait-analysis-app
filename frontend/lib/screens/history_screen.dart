import 'package:flutter/material.dart';
import 'package:gait_analysis_app/utils/constants.dart';
import 'package:gait_analysis_app/widgets/custom_app_bar.dart';

class HistoryScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: CustomAppBar(
        title: AppStrings.historyTab,
        showBackButton: false,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(AppConstants.defaultPadding),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 統計サマリー
              _buildStatsSummary(),
              
              const SizedBox(height: 24),
              
              // 履歴リスト
              Expanded(
                child: _buildHistoryList(),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatsSummary() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '今月の統計',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildStatItem('分析回数', '12', AppColors.primary),
                _buildStatItem('平均スコア', '82', AppColors.success),
                _buildStatItem('改善率', '+5%', AppColors.accent),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatItem(String label, String value, Color color) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        Text(
          label,
          style: const TextStyle(
            fontSize: 12,
            color: AppColors.textSecondary,
          ),
        ),
      ],
    );
  }

  Widget _buildHistoryList() {
    // 仮のデータ
    final historyItems = List.generate(10, (index) {
      return {
        'date': '2025/07/${25 - index}',
        'time': '${14 + index}:30',
        'score': 80 + (index % 20),
        'speed': '1.${2 + (index % 3)}',
      };
    });

    return ListView.builder(
      itemCount: historyItems.length,
      itemBuilder: (context, index) {
        final item = historyItems[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          child: ListTile(
            leading: Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: AppColors.primaryLight,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(
                Icons.directions_walk,
                color: AppColors.primary,
              ),
            ),
            title: Text('${item['date']} ${item['time']}'),
            subtitle: Text(
              'スコア: ${item['score']}点 | 速度: ${item['speed']}m/s',
            ),
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: _getScoreColor(item['score'] as int).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    '${item['score']}',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: _getScoreColor(item['score'] as int),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                const Icon(Icons.chevron_right),
              ],
            ),
            onTap: () => _showHistoryDetail(item),
          ),
        );
      },
    );
  }

  Color _getScoreColor(int score) {
    if (score >= 85) return AppColors.excellentScore;
    if (score >= 70) return AppColors.goodScore;
    if (score >= 50) return AppColors.fairScore;
    return AppColors.poorScore;
  }

  void _showHistoryDetail(Map<String, dynamic> item) {
    // TODO: 詳細画面への遷移
  }
}