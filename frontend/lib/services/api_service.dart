import 'dart:typed_data';
import 'package:dio/dio.dart';
import 'package:gait_analysis_app/models/gait_analysis_models.dart';
import 'package:gait_analysis_app/utils/constants.dart';

class ApiService {
  late final Dio _dio;
  final String baseUrl;

  ApiService({String? baseUrl}) : baseUrl = baseUrl ?? AppConstants.apiBaseUrl {
    _dio = Dio(BaseOptions(
      baseUrl: this.baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(minutes: 5), // 分析に時間がかかる場合があるため
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));

    // インターセプター追加
    _dio.interceptors.add(LogInterceptor(
      requestBody: false, // 動画データでログが膨大になるのを防ぐ
      responseBody: true,
    ));
  }

  // Generic helpers
  Future<Response<dynamic>> get(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    return _dio.get(path, queryParameters: queryParameters, options: options);
  }

  Future<Response<dynamic>> post(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    return _dio.post(path, data: data, queryParameters: queryParameters, options: options);
  }

  Future<Response<dynamic>> delete(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    return _dio.delete(path, data: data, queryParameters: queryParameters, options: options);
  }

  /// ヘルスチェック
  Future<Map<String, dynamic>> checkHealth() async {
    try {
      final response = await _dio.get('/health');
      return response.data;
    } catch (e) {
      throw ApiException('ヘルスチェックに失敗しました: $e');
    }
  }

  /// レディネスチェック
  Future<Map<String, dynamic>> checkReadiness() async {
    try {
      final response = await _dio.get('/ready');
      return response.data;
    } catch (e) {
      throw ApiException('レディネスチェックに失敗しました: $e');
    }
  }

  /// 歩行分析実行（非Web向け：ファイルパス指定）
  Future<GaitAnalysisResponse> analyzeGait({
    required String filePath,
    double? userHeightCm,
    String analysisMode = 'standard',
  }) async {
    return analyzeGaitFromFile(
      filePath: filePath,
      userHeightCm: userHeightCm,
      analysisMode: analysisMode,
    );
  }

  /// 歩行分析実行（ローカルファイルパス）
  Future<GaitAnalysisResponse> analyzeGaitFromFile({
    required String filePath,
    double? userHeightCm,
    String analysisMode = 'standard',
  }) async {
    try {
      // FormData作成
      final formData = FormData.fromMap({
        'video': await MultipartFile.fromFile(
          filePath,
          filename: filePath.split('/').last,
        ),
        if (userHeightCm != null) 'user_height_cm': userHeightCm,
        'analysis_mode': analysisMode,
      });

      final response = await _dio.post(
        // Prefix defined in backend: /api/v1/gait-analysis/analyze
        '/gait-analysis/analyze',
        data: formData,
        options: Options(
          headers: {'Content-Type': 'multipart/form-data'},
        ),
      );

      return GaitAnalysisResponse.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleDioException(e);
    } catch (e) {
      throw ApiException('歩行分析に失敗しました: $e');
    }
  }

  /// 歩行分析実行（Web等のメモリバイト）
  Future<GaitAnalysisResponse> analyzeGaitFromBytes({
    required Uint8List bytes,
    required String filename,
    double? userHeightCm,
    String analysisMode = 'standard',
  }) async {
    try {
      final formData = FormData.fromMap({
        'video': MultipartFile.fromBytes(
          bytes,
          filename: filename,
        ),
        if (userHeightCm != null) 'user_height_cm': userHeightCm,
        'analysis_mode': analysisMode,
      });

      final response = await _dio.post(
        '/gait-analysis/analyze',
        data: formData,
        options: Options(
          headers: {'Content-Type': 'multipart/form-data'},
        ),
      );

      return GaitAnalysisResponse.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleDioException(e);
    } catch (e) {
      throw ApiException('歩行分析に失敗しました: $e');
    }
  }

  /// 拡張歩行分析（Enhanced）
  Future<Map<String, dynamic>> analyzeGaitEnhanced({
    required Uint8List bytes,
    required String filename,
    double? userHeightCm,
    String analysisMode = 'detailed',
    String cameraPosition = 'side',
    int targetFps = 60,
    String deviceType = 'mobile',
    bool enable30sOptimization = true,
  }) async {
    try {
      final formData = FormData.fromMap({
        'video': MultipartFile.fromBytes(bytes, filename: filename),
        if (userHeightCm != null) 'user_height_cm': userHeightCm,
        'analysis_mode': analysisMode,
        'camera_position': cameraPosition,
        'target_fps': targetFps,
        'device_type': deviceType,
        'enable_30s_optimization': enable30sOptimization,
      });

      final response = await _dio.post(
        '/gait-analysis/analyze-enhanced',
        data: formData,
        options: Options(headers: {'Content-Type': 'multipart/form-data'}),
      );

      return Map<String, dynamic>.from(response.data);
    } on DioException catch (e) {
      throw _handleDioException(e);
    } catch (e) {
      throw ApiException('拡張歩行分析に失敗しました: $e');
    }
  }

  /// 分析結果取得
  Future<GaitAnalysisResponse> getAnalysisResult(String analysisId) async {
    try {
      final response = await _dio.get('/gait-analysis/analysis/$analysisId');
      return GaitAnalysisResponse.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleDioException(e);
    } catch (e) {
      throw ApiException('分析結果の取得に失敗しました: $e');
    }
  }

  /// サポートされている形式取得
  Future<SupportedFormatsResponse> getSupportedFormats() async {
    try {
      final response = await _dio.get('/gait-analysis/supported-formats');
      return SupportedFormatsResponse.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleDioException(e);
    } catch (e) {
      throw ApiException('サポート形式の取得に失敗しました: $e');
    }
  }

  /// 動画の事前検証
  Future<bool> validateVideo(File videoFile) async {
    try {
      // ファイルサイズチェック
      final fileSizeBytes = await videoFile.length();
      final fileSizeMB = fileSizeBytes / (1024 * 1024);
      
      if (fileSizeMB > 100) { // 100MB制限
        throw ValidationException('ファイルサイズが大きすぎます（最大100MB）');
      }

      // ファイル拡張子チェック
      final extension = videoFile.path.split('.').last.toLowerCase();
      const supportedExtensions = ['mp4', 'mov', 'avi', 'webm'];
      
      if (!supportedExtensions.contains(extension)) {
        throw ValidationException('サポートされていないファイル形式です');
      }

      return true;
    } catch (e) {
      if (e is ValidationException) rethrow;
      throw ValidationException('動画の検証に失敗しました: $e');
    }
  }

  /// DioExceptionのハンドリング
  ApiException _handleDioException(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectTimeout:
        return ApiException('接続がタイムアウトしました');
      case DioExceptionType.sendTimeout:
        return ApiException('送信がタイムアウトしました');
      case DioExceptionType.receiveTimeout:
        return ApiException('レスポンスがタイムアウトしました');
      case DioExceptionType.badResponse:
        final statusCode = e.response?.statusCode;
        final message = e.response?.data?['detail'] ?? 'サーバーエラーが発生しました';
        return ApiException('HTTP $statusCode: $message');
      case DioExceptionType.cancel:
        return ApiException('リクエストがキャンセルされました');
      default:
        return ApiException('ネットワークエラーが発生しました: ${e.message}');
    }
  }
}

/// API例外クラス
class ApiException implements Exception {
  final String message;
  ApiException(this.message);

  @override
  String toString() => 'ApiException: $message';
}

/// バリデーション例外クラス
class ValidationException implements Exception {
  final String message;
  ValidationException(this.message);

  @override
  String toString() => 'ValidationException: $message';
}

/// サポートフォーマットレスポンス
class SupportedFormatsResponse {
  final List<String> supportedFormats;
  final int maxFileSizeMb;
  final int maxDurationSeconds;
  final int recommendedFps;
  final String recommendedResolution;
  final Map<String, String> shootingGuidelines;

  SupportedFormatsResponse({
    required this.supportedFormats,
    required this.maxFileSizeMb,
    required this.maxDurationSeconds,
    required this.recommendedFps,
    required this.recommendedResolution,
    required this.shootingGuidelines,
  });

  factory SupportedFormatsResponse.fromJson(Map<String, dynamic> json) {
    return SupportedFormatsResponse(
      supportedFormats: List<String>.from(json['supported_formats']),
      maxFileSizeMb: json['max_file_size_mb'],
      maxDurationSeconds: json['max_duration_seconds'],
      recommendedFps: json['recommended_fps'],
      recommendedResolution: json['recommended_resolution'],
      shootingGuidelines: Map<String, String>.from(json['shooting_guidelines']),
    );
  }
}
