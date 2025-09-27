import 'package:flutter/material.dart';
import 'package:gait_analysis_app/models/gait_analysis_models.dart';
import 'package:gait_analysis_app/services/report_service.dart';
import 'package:gait_analysis_app/utils/constants.dart';
import 'package:gait_analysis_app/utils/app_theme.dart';

class ReportGeneratorDialog extends StatefulWidget {
  final GaitAnalysisResponse analysisResult;
  final Map<String, dynamic>? patientInfo;

  const ReportGeneratorDialog({
    Key? key,
    required this.analysisResult,
    this.patientInfo,
  }) : super(key: key);

  @override
  _ReportGeneratorDialogState createState() => _ReportGeneratorDialogState();
}

class _ReportGeneratorDialogState extends State<ReportGeneratorDialog> {
  final ReportService _reportService = ReportService();
  
  bool _isGenerating = false;
  List<ReportTemplate> _templates = [];
  ReportTemplate? _selectedTemplate;
  String _selectedFormat = 'pdf';
  Map<String, bool> _selectedSections = {};
  
  @override
  void initState() {
    super.initState();
    _loadTemplates();
  }

  Future<void> _loadTemplates() async {
    try {
      final templates = await _reportService.getReportTemplates();
      setState(() {
        _templates = templates;
        if (templates.isNotEmpty) {
          _selectedTemplate = templates.first;
          _selectedFormat = templates.first.format.toLowerCase();
        }
      });
    } catch (e) {
      _showErrorSnackBar('テンプレート情報の取得に失敗しました: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Container(
        width: MediaQuery.of(context).size.width * 0.9,
        maxWidth: 600,
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ヘッダー
            Row(
              children: [
                Icon(Icons.picture_as_pdf, color: AppColors.primary, size: 28),
                const SizedBox(width: 12),
                const Text(
                  'レポート生成',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: () => Navigator.of(context).pop(),
                ),
              ],
            ),
            
            const SizedBox(height: 24),
            
            // フォーマット選択
            _buildFormatSelection(),
            
            const SizedBox(height: 20),
            
            // テンプレート選択
            if (_templates.isNotEmpty) _buildTemplateSelection(),
            
            const SizedBox(height: 20),
            
            // セクション選択
            if (_selectedTemplate != null) _buildSectionSelection(),
            
            const SizedBox(height: 24),
            
            // アクションボタン
            _buildActionButtons(),
          ],
        ),
      ),
    );
  }

  Widget _buildFormatSelection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'フォーマット',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            _buildFormatCard(
              format: 'pdf',
              title: 'PDF レポート',
              subtitle: '詳細な分析結果',
              icon: Icons.picture_as_pdf,
              color: AppColors.error,
            ),
            const SizedBox(width: 12),
            _buildFormatCard(
              format: 'png',
              title: 'PNG 画像',
              subtitle: 'サマリー表示',
              icon: Icons.image,
              color: AppColors.success,
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildFormatCard({
    required String format,
    required String title,
    required String subtitle,
    required IconData icon,
    required Color color,
  }) {
    final isSelected = _selectedFormat == format;
    
    return Expanded(
      child: GestureDetector(
        onTap: () {
          setState(() {
            _selectedFormat = format;
            // 対応するテンプレートを選択
            final template = _templates.firstWhere(
              (t) => t.format.toLowerCase() == format,
              orElse: () => _templates.first,
            );
            _selectedTemplate = template;
          });
        },
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            border: Border.all(
              color: isSelected ? color : AppColors.divider,
              width: isSelected ? 2 : 1,
            ),
            borderRadius: BorderRadius.circular(12),
            color: isSelected ? color.withOpacity(0.1) : null,
          ),
          child: Column(
            children: [
              Icon(
                icon,
                color: isSelected ? color : AppColors.textSecondary,
                size: 32,
              ),
              const SizedBox(height: 8),
              Text(
                title,
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: isSelected ? color : AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                subtitle,
                style: TextStyle(
                  fontSize: 12,
                  color: AppColors.textSecondary,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTemplateSelection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'テンプレート',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 12),
        Container(
          decoration: BoxDecoration(
            border: Border.all(color: AppColors.divider),
            borderRadius: BorderRadius.circular(8),
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<ReportTemplate>(
              value: _selectedTemplate,
              isExpanded: true,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              items: _templates.map((template) {
                return DropdownMenuItem<ReportTemplate>(
                  value: template,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        template.name,
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      Text(
                        template.description,
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppColors.textSecondary,
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
              onChanged: (template) {
                setState(() {
                  _selectedTemplate = template;
                  if (template != null) {
                    _selectedFormat = template.format.toLowerCase();
                  }
                });
              },
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildSectionSelection() {
    if (_selectedTemplate == null || _selectedTemplate!.sections.isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '含めるセクション',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 12),
        Container(
          decoration: BoxDecoration(
            border: Border.all(color: AppColors.divider),
            borderRadius: BorderRadius.circular(8),
          ),
          padding: const EdgeInsets.all(12),
          child: Column(
            children: _selectedTemplate!.sections.map((section) {
              final isSelected = _selectedSections[section] ?? true;
              return CheckboxListTile(
                title: Text(
                  section,
                  style: const TextStyle(fontSize: 14),
                ),
                value: isSelected,
                onChanged: (value) {
                  setState(() {
                    _selectedSections[section] = value ?? true;
                  });
                },
                controlAffinity: ListTileControlAffinity.leading,
                contentPadding: EdgeInsets.zero,
                dense: true,
              );
            }).toList(),
          ),
        ),
      ],
    );
  }

  Widget _buildActionButtons() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        TextButton(
          onPressed: _isGenerating ? null : () => Navigator.of(context).pop(),
          child: const Text('キャンセル'),
        ),
        const SizedBox(width: 12),
        ElevatedButton.icon(
          onPressed: _isGenerating ? null : _generateReport,
          icon: _isGenerating
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.download),
          label: Text(_isGenerating ? '生成中...' : 'ダウンロード'),
        ),
      ],
    );
  }

  Future<void> _generateReport() async {
    if (_selectedTemplate == null) return;

    setState(() {
      _isGenerating = true;
    });

    try {
      if (_selectedFormat == 'pdf') {
        final pdfData = await _reportService.generatePdfReport(
          widget.analysisResult,
          patientInfo: widget.patientInfo,
        );
        
        final filename = 'gait_analysis_report_${widget.analysisResult.analysisId.substring(0, 8)}.pdf';
        await _reportService.downloadReportWeb(pdfData, filename, 'application/pdf');
      } else if (_selectedFormat == 'png') {
        final pngData = await _reportService.generatePngSummary(
          widget.analysisResult,
          width: 1200,
          height: 800,
        );
        
        final filename = 'gait_summary_${widget.analysisResult.analysisId.substring(0, 8)}.png';
        await _reportService.downloadReportWeb(pngData, filename, 'image/png');
      }

      Navigator.of(context).pop();
      _showSuccessSnackBar('レポートが正常にダウンロードされました');
    } catch (e) {
      _showErrorSnackBar('レポート生成エラー: $e');
    } finally {
      setState(() {
        _isGenerating = false;
      });
    }
  }

  void _showSuccessSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: AppColors.success,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  void _showErrorSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: AppColors.error,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }
}

// 便利なファクトリ関数
void showReportGeneratorDialog(
  BuildContext context,
  GaitAnalysisResponse analysisResult, {
  Map<String, dynamic>? patientInfo,
}) {
  showDialog(
    context: context,
    builder: (context) => ReportGeneratorDialog(
      analysisResult: analysisResult,
      patientInfo: patientInfo,
    ),
  );
}