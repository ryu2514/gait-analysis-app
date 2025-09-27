import 'package:flutter/material.dart';
import 'package:gait_analysis_app/utils/constants.dart';
import 'package:gait_analysis_app/widgets/custom_app_bar.dart';

class GuideScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: CustomAppBar(
        title: AppStrings.guideTab,
        showBackButton: false,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppConstants.defaultPadding),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // アプリ概要
              _buildAppOverview(),
              
              const SizedBox(height: 24),
              
              // 撮影ガイド
              _buildShootingGuide(),
              
              const SizedBox(height: 24),
              
              // 分析指標説明
              _buildAnalysisIndicators(),
              
              const SizedBox(height: 24),
              
              // よくある質問
              _buildFAQ(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAppOverview() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.info_outline,
                  color: AppColors.primary,
                  size: 24,
                ),
                const SizedBox(width: 8),
                const Text(
                  'アプリについて',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            const Text(
              'このアプリは、スマートフォンのカメラだけで歩行を分析し、歩行速度、対称性、関節角度などの指標を測定できます。理学療法士、トレーナー、一般の方々の歩行評価にご活用ください。',
              style: TextStyle(fontSize: 14),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildShootingGuide() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.camera_alt,
                  color: AppColors.accent,
                  size: 24,
                ),
                const SizedBox(width: 8),
                const Text(
                  '撮影ガイド',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            _buildGuideSection(
              '推奨設定',
              [
                '解像度: 1080p以上',
                'フレームレート: 30fps以上',
                '撮影時間: 5-10秒',
                'ファイルサイズ: 100MB以下',
              ],
            ),
            const SizedBox(height: 16),
            _buildGuideSection(
              '撮影環境',
              [
                '距離: カメラから3-5メートル',
                '角度: 側方または前方',
                '背景: シンプルで明るい',
                '照明: 十分な明るさ',
              ],
            ),
            const SizedBox(height: 16),
            _buildGuideSection(
              '歩行のポイント',
              [
                '自然な歩行速度で',
                '最低3歩以上歩く',
                'カメラに向かって真っ直ぐ',
                '遮蔽物がないように',
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildGuideSection(String title, List<String> items) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        ...items.map((item) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 2),
              child: Row(
                children: [
                  Icon(
                    Icons.check_circle_outline,
                    color: AppColors.success,
                    size: 16,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      item,
                      style: const TextStyle(fontSize: 14),
                    ),
                  ),
                ],
              ),
            )),
      ],
    );
  }

  Widget _buildAnalysisIndicators() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.analytics,
                  color: AppColors.warning,
                  size: 24,
                ),
                const SizedBox(width: 8),
                const Text(
                  '分析指標の説明',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            _buildIndicatorItem(
              '歩行速度',
              '1秒間に歩く距離（m/s）。一般的に1.2-1.4m/sが正常範囲。',
              AppColors.primary,
            ),
            _buildIndicatorItem(
              'ケイデンス',
              '1分間の歩数。一般的に110-120歩/分が正常範囲。',
              AppColors.accent,
            ),
            _buildIndicatorItem(
              '対称性指数',
              '左右の歩行パターンの対称性。100%に近いほど良好。',
              AppColors.success,
            ),
            _buildIndicatorItem(
              '関節角度',
              '股関節、膝関節、足関節の可動域。正常範囲との比較。',
              AppColors.warning,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildIndicatorItem(String title, String description, Color color) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 8,
            height: 8,
            margin: const EdgeInsets.only(top: 6),
            decoration: BoxDecoration(
              color: color,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  description,
                  style: const TextStyle(
                    fontSize: 12,
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFAQ() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.help_outline,
                  color: AppColors.info,
                  size: 24,
                ),
                const SizedBox(width: 8),
                const Text(
                  'よくある質問',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            _buildFAQItem(
              'Q: どの程度の精度ですか？',
              'A: 研究用機器と比較して±5%以内の精度を実現しています。',
            ),
            _buildFAQItem(
              'Q: 屋外でも使用できますか？',
              'A: 十分な照明があれば屋外でも使用可能ですが、屋内での撮影を推奨します。',
            ),
            _buildFAQItem(
              'Q: データはどこに保存されますか？',
              'A: 分析結果は端末に保存され、動画は分析後72時間で自動削除されます。',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFAQItem(String question, String answer) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            question,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            answer,
            style: const TextStyle(
              fontSize: 12,
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }
}