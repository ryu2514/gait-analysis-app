import 'package:flutter/material.dart';
import 'package:gait_analysis_app/screens/analysis_screen.dart';
import 'package:gait_analysis_app/screens/history_screen.dart';
import 'package:gait_analysis_app/screens/guide_screen.dart';
import 'package:gait_analysis_app/utils/constants.dart';
import 'package:gait_analysis_app/widgets/custom_app_bar.dart';
import 'package:gait_analysis_app/widgets/quick_stats_card.dart';
import 'package:gait_analysis_app/widgets/analysis_start_button.dart';

class HomeScreen extends StatefulWidget {
  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;

  final List<Widget> _screens = [
    _HomeContent(),
    HistoryScreen(),
    GuideScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_currentIndex],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        type: BottomNavigationBarType.fixed,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home),
            label: AppStrings.homeTab,
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.history),
            label: AppStrings.historyTab,
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.help_outline),
            label: AppStrings.guideTab,
          ),
        ],
      ),
    );
  }
}

class _HomeContent extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: CustomAppBar(
        title: AppStrings.appName,
        showBackButton: false,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppConstants.defaultPadding),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ウェルカムセクション
              _buildWelcomeSection(context),
              
              const SizedBox(height: 24),
              
              // メイン分析ボタン
              AnalysisStartButton(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => AnalysisScreen()),
                  );
                },
              ),
              
              const SizedBox(height: 32),
              
              // クイック統計
              _buildQuickStatsSection(),
              
              const SizedBox(height: 24),
              
              // 最近の分析
              _buildRecentAnalysisSection(context),
              
              const SizedBox(height: 24),
              
              // 撮影ガイド
              _buildShootingGuideSection(context),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildWelcomeSection(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppColors.primary, AppColors.primaryDark],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(AppConstants.defaultRadius),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'おかえりなさい！',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            AppStrings.appDescription,
            style: TextStyle(
              fontSize: 16,
              color: Colors.white70,
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Icon(
                Icons.smartphone,
                color: Colors.white70,
                size: 20,
              ),
              const SizedBox(width: 8),
              const Text(
                'カメラで撮影するだけ',
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.white70,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildQuickStatsSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '今週の状況',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(
              child: QuickStatsCard(
                title: '総分析回数',
                value: '12',
                icon: Icons.analytics,
                color: AppColors.primary,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: QuickStatsCard(
                title: '平均スコア',
                value: '82',
                icon: Icons.trending_up,
                color: AppColors.success,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: QuickStatsCard(
                title: '対称性',
                value: '85%',
                icon: Icons.balance,
                color: AppColors.accent,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: QuickStatsCard(
                title: '歩行速度',
                value: '1.2m/s',
                icon: Icons.speed,
                color: AppColors.warning,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildRecentAnalysisSection(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              '最近の分析',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            TextButton(
              onPressed: () {
                // 履歴画面に遷移
              },
              child: const Text('すべて見る'),
            ),
          ],
        ),
        const SizedBox(height: 16),
        _buildRecentAnalysisCard(),
        const SizedBox(height: 12),
        _buildRecentAnalysisCard(),
      ],
    );
  }

  Widget _buildRecentAnalysisCard() {
    return Card(
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
        title: const Text('2025/07/02 14:30'),
        subtitle: const Text('総合スコア: 85点 | 歩行速度: 1.3m/s'),
        trailing: const Icon(Icons.chevron_right),
        onTap: () {
          // 詳細画面に遷移
        },
      ),
    );
  }

  Widget _buildShootingGuideSection(BuildContext context) {
    return Card(
      color: AppColors.info.withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.camera_alt,
                  color: AppColors.info,
                  size: 24,
                ),
                const SizedBox(width: 12),
                const Text(
                  '撮影のコツ',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            _buildGuideItem('距離: ${AppConstants.shootingDistance}'),
            _buildGuideItem('角度: ${AppConstants.recommendedAngle}'),
            _buildGuideItem('時間: ${AppConstants.recommendedDuration}'),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton(
                onPressed: () {
                  // ガイド画面に遷移
                },
                child: const Text('詳しいガイドを見る'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildGuideItem(String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(
            Icons.check_circle_outline,
            color: AppColors.success,
            size: 16,
          ),
          const SizedBox(width: 8),
          Text(
            text,
            style: const TextStyle(fontSize: 14),
          ),
        ],
      ),
    );
  }
}