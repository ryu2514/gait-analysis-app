import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:file_picker/file_picker.dart';
import 'dart:typed_data';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:gait_analysis_app/services/api_service.dart';
import 'package:gait_analysis_app/models/gait_analysis_models.dart';
import 'package:gait_analysis_app/screens/results_screen.dart';
import 'package:gait_analysis_app/utils/constants.dart';
import 'package:gait_analysis_app/widgets/custom_app_bar.dart';

class AnalysisScreen extends StatefulWidget {
  @override
  _AnalysisScreenState createState() => _AnalysisScreenState();
}

class _AnalysisScreenState extends State<AnalysisScreen> {
  bool _isAnalyzing = false;
  final TextEditingController _heightController = TextEditingController();
  String? _selectedFileName;
  Uint8List? _selectedBytes; // Web/bytes
  String? _selectedFilePath; // Mobile/Desktop

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: CustomAppBar(
        title: '歩行分析',
        showBackButton: true,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(AppConstants.defaultPadding),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 撮影オプション
              _buildCaptureOptions(),
              
              const SizedBox(height: 24),
              
              // 撮影ガイド
              _buildShootingGuide(),
              
              const SizedBox(height: 24),
              
              // 身長入力
              _buildHeightInput(),
              
              const Spacer(),
              
              // 開始ボタン
              _buildStartButton(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCaptureOptions() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '動画の選択方法',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(
              child: _buildOptionCard(
                icon: Icons.videocam,
                title: '撮影',
                subtitle: '新しく撮影',
                onTap: () => _handleCameraCapture(),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildOptionCard(
                icon: Icons.photo_library,
                title: 'ライブラリ',
                subtitle: '保存済み動画',
                onTap: () => _handleLibrarySelect(),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildOptionCard({
    required IconData icon,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
  }) {
    return Card(
      elevation: AppConstants.cardElevation,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(AppConstants.defaultRadius),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Icon(
                icon,
                size: 48,
                color: AppColors.primary,
              ),
              const SizedBox(height: 12),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                subtitle,
                style: const TextStyle(
                  fontSize: 12,
                  color: AppColors.textSecondary,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildShootingGuide() {
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
                  Icons.info_outline,
                  color: AppColors.info,
                ),
                const SizedBox(width: 8),
                const Text(
                  '撮影のポイント',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            _buildGuideItem('カメラから3-5m離れて歩く'),
            _buildGuideItem('横向きまたは前向きで撮影'),
            _buildGuideItem('5-10秒程度で3歩以上歩く'),
            _buildGuideItem('明るい場所で撮影する'),
            _buildGuideItem('シンプルな背景を選ぶ'),
          ],
        ),
      ),
    );
  }

  Widget _buildGuideItem(String text) {
    return Padding(
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
              text,
              style: const TextStyle(fontSize: 14),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeightInput() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '身長（任意）',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'より正確な分析のために身長を入力してください',
              style: TextStyle(
                fontSize: 12,
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 12),
            TextFormField(
              decoration: const InputDecoration(
                labelText: '身長 (cm)',
                hintText: '例: 170',
                suffixText: 'cm',
              ),
              keyboardType: TextInputType.number,
              controller: _heightController,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStartButton() {
    return SizedBox(
      width: double.infinity,
      height: 56,
      child: ElevatedButton(
        onPressed: _isAnalyzing ? null : () => _startAnalysis(),
        child: _isAnalyzing
            ? const CircularProgressIndicator(color: Colors.white)
            : const Text('分析開始'),
      ),
    );
  }

  void _handleCameraCapture() {
    // TODO: カメラ撮影の実装
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('カメラ撮影機能は実装中です')),
    );
  }

  Future<void> _handleLibrarySelect() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.video,
        withData: kIsWeb, // on web we need bytes
      );

      if (result == null || result.files.isEmpty) {
        return;
      }

      final file = result.files.single;
      setState(() {
        _selectedFileName = file.name;
      });

      if (kIsWeb) {
        // Use bytes
        if (file.bytes == null) {
          throw Exception('選択したファイルの読み込みに失敗しました');
        }
        _selectedBytes = file.bytes;
        _selectedFilePath = null;
      } else {
        // Use local path
        if (file.path == null) {
          throw Exception('ファイルパスが取得できませんでした');
        }
        _selectedFilePath = file.path!;
        _selectedBytes = null;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('選択: ${_selectedFileName}')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('動画の選択に失敗しました: $e')),
      );
    }
  }

  Future<void> _startAnalysis() async {
    if (_selectedBytes == null && _selectedFilePath == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('先に動画を選択してください')),
      );
      return;
    }

    setState(() {
      _isAnalyzing = true;
    });

    try {
      final api = RepositoryProvider.of<ApiService>(context);
      final height = double.tryParse(_heightController.text);
      late GaitAnalysisResponse result;

      if (kIsWeb && _selectedBytes != null && _selectedFileName != null) {
        result = await api.analyzeGaitFromBytes(
          bytes: _selectedBytes!,
          filename: _selectedFileName!,
          userHeightCm: height,
          analysisMode: 'standard',
        );
      } else if (!kIsWeb && _selectedFilePath != null) {
        result = await api.analyzeGaitFromFile(
          filePath: _selectedFilePath!,
          userHeightCm: height,
          analysisMode: 'standard',
        );
      } else {
        throw Exception('動画データが無効です');
      }

      if (!mounted) return;
      setState(() {
        _isAnalyzing = false;
      });

      // Navigate to results
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => ResultsScreen(analysisResult: result),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isAnalyzing = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('分析に失敗しました: $e')),
      );
    }
  }
}
