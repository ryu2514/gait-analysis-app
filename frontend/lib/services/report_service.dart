import 'package:dio/dio.dart';
import 'package:gait_analysis_app/models/gait_analysis_models.dart';
import 'package:gait_analysis_app/services/api_service.dart';
import 'package:gait_analysis_app/utils/constants.dart';
import 'dart:typed_data';
import 'dart:convert';

class ReportService {
  final ApiService _apiService;

  ReportService({ApiService? apiService}) : _apiService = apiService ?? ApiService();
  
  /// PDF形式のレポートを生成してダウンロード
  Future<Uint8List> generatePdfReport(
    GaitAnalysisResponse analysisResult, {
    Map<String, dynamic>? patientInfo,
  }) async {
    try {
      final response = await _apiService.post(
        '/reports/generate/pdf',
        data: {
          'analysis_result': analysisResult.toJson(),
          'patient_info': patientInfo,
        },
        options: Options(
          responseType: ResponseType.bytes,
          headers: {
            'Accept': 'application/pdf',
          },
        ),
      );
      
      return Uint8List.fromList(response.data);
    } catch (e) {
      throw Exception('PDFレポートの生成に失敗しました: $e');
    }
  }
  
  /// PNG形式のサマリー画像を生成してダウンロード
  Future<Uint8List> generatePngSummary(
    GaitAnalysisResponse analysisResult, {
    int width = 1200,
    int height = 800,
  }) async {
    try {
      final response = await _apiService.post(
        '/reports/generate/png',
        data: {
          'analysis_result': analysisResult.toJson(),
          'width': width,
          'height': height,
        },
        options: Options(
          responseType: ResponseType.bytes,
          headers: {
            'Accept': 'image/png',
          },
        ),
      );
      
      return Uint8List.fromList(response.data);
    } catch (e) {
      throw Exception('PNG画像の生成に失敗しました: $e');
    }
  }
  
  /// Base64エンコードされた画像を生成（Web表示用）
  Future<String> generateBase64Image(
    GaitAnalysisResponse analysisResult,
  ) async {
    try {
      final response = await _apiService.post(
        '/reports/generate/base64',
        data: {
          'analysis_result': analysisResult.toJson(),
        },
      );
      
      if (response.data['status'] == 'success') {
        return response.data['image_data'];
      } else {
        throw Exception('Base64画像の生成に失敗しました');
      }
    } catch (e) {
      throw Exception('Base64画像の生成に失敗しました: $e');
    }
  }
  
  /// 利用可能なレポートテンプレート一覧を取得
  Future<List<ReportTemplate>> getReportTemplates() async {
    try {
      final response = await _apiService.get('/reports/templates');
      
      if (response.data['status'] == 'success') {
        final templates = response.data['templates'] as List;
        return templates.map((template) => ReportTemplate.fromJson(template)).toList();
      } else {
        throw Exception('テンプレート一覧の取得に失敗しました');
      }
    } catch (e) {
      throw Exception('テンプレート一覧の取得に失敗しました: $e');
    }
  }
  
  /// カスタムレポートを生成
  Future<Uint8List> generateCustomReport(
    GaitAnalysisResponse analysisResult,
    ReportTemplate template, {
    Map<String, dynamic>? patientInfo,
    Map<String, dynamic>? customConfig,
  }) async {
    try {
      final templateConfig = {
        'format': template.format.toLowerCase(),
        'template_id': template.id,
        ...?customConfig,
      };
      
      final response = await _apiService.post(
        '/reports/generate/custom',
        data: {
          'analysis_result': analysisResult.toJson(),
          'template_config': templateConfig,
          'patient_info': patientInfo,
        },
        options: Options(
          responseType: ResponseType.bytes,
          headers: {
            'Accept': template.format.toLowerCase() == 'pdf' 
                ? 'application/pdf' 
                : 'image/png',
          },
        ),
      );
      
      return Uint8List.fromList(response.data);
    } catch (e) {
      throw Exception('カスタムレポートの生成に失敗しました: $e');
    }
  }
  
  /// レポート生成状況を確認
  Future<ReportStatus> getReportStatus(String analysisId) async {
    try {
      final response = await _apiService.get('/reports/status/$analysisId');
      
      if (response.data['status'] == 'success') {
        return ReportStatus.fromJson(response.data);
      } else {
        throw Exception('レポート状況の取得に失敗しました');
      }
    } catch (e) {
      throw Exception('レポート状況の取得に失敗しました: $e');
    }
  }
  
  /// レポートをデバイスにダウンロード（Web環境用）
  Future<void> downloadReportWeb(
    Uint8List data,
    String filename,
    String mimeType,
  ) async {
    try {
      // Web環境でのファイルダウンロード実装
      final blob = html.Blob([data], mimeType);
      final url = html.Url.createObjectUrlFromBlob(blob);
      
      final anchor = html.AnchorElement(href: url)
        ..target = 'blank'
        ..download = filename;
      
      html.document.body?.append(anchor);
      anchor.click();
      anchor.remove();
      
      html.Url.revokeObjectUrl(url);
    } catch (e) {
      throw Exception('ファイルのダウンロードに失敗しました: $e');
    }
  }
  
  /// 複数形式のレポートを一括生成
  Future<Map<String, Uint8List>> generateMultipleReports(
    GaitAnalysisResponse analysisResult, {
    List<String> formats = const ['pdf', 'png'],
    Map<String, dynamic>? patientInfo,
  }) async {
    final reports = <String, Uint8List>{};
    
    try {
      // 並列でレポート生成
      final futures = <Future<void>>[];
      
      for (final format in formats) {
        if (format.toLowerCase() == 'pdf') {
          futures.add(
            generatePdfReport(analysisResult, patientInfo: patientInfo)
                .then((data) => reports['pdf'] = data)
          );
        } else if (format.toLowerCase() == 'png') {
          futures.add(
            generatePngSummary(analysisResult)
                .then((data) => reports['png'] = data)
          );
        }
      }
      
      await Future.wait(futures);
      return reports;
    } catch (e) {
      throw Exception('複数レポートの生成に失敗しました: $e');
    }
  }
}

/// レポートテンプレート情報
class ReportTemplate {
  final String id;
  final String name;
  final String description;
  final String format;
  final int? pages;
  final List<String> sections;
  
  ReportTemplate({
    required this.id,
    required this.name,
    required this.description,
    required this.format,
    this.pages,
    required this.sections,
  });
  
  factory ReportTemplate.fromJson(Map<String, dynamic> json) {
    return ReportTemplate(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      format: json['format'],
      pages: json['pages'],
      sections: List<String>.from(json['sections'] ?? []),
    );
  }
  
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'format': format,
      'pages': pages,
      'sections': sections,
    };
  }
}

/// レポート生成状況
class ReportStatus {
  final String analysisId;
  final List<String> reportsGenerated;
  final List<String> availableFormats;
  final DateTime? lastGenerated;
  
  ReportStatus({
    required this.analysisId,
    required this.reportsGenerated,
    required this.availableFormats,
    this.lastGenerated,
  });
  
  factory ReportStatus.fromJson(Map<String, dynamic> json) {
    return ReportStatus(
      analysisId: json['analysis_id'],
      reportsGenerated: List<String>.from(json['reports_generated'] ?? []),
      availableFormats: List<String>.from(json['available_formats'] ?? []),
      lastGenerated: json['last_generated'] != null 
          ? DateTime.parse(json['last_generated'])
          : null,
    );
  }
  
  Map<String, dynamic> toJson() {
    return {
      'analysis_id': analysisId,
      'reports_generated': reportsGenerated,
      'available_formats': availableFormats,
      'last_generated': lastGenerated?.toIso8601String(),
    };
  }
}

// Web環境でのimport（条件付きimport用）
import 'dart:html' as html;
