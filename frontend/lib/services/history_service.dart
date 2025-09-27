import 'package:dio/dio.dart';
import 'package:gait_analysis_app/models/gait_analysis_models.dart';
import 'package:gait_analysis_app/services/api_service.dart';

class HistoryService {
  final ApiService _apiService;

  HistoryService({ApiService? apiService}) : _apiService = apiService ?? ApiService();

  /// 分析履歴を取得
  Future<AnalysisHistoryResponse> getAnalysisHistory({
    required String userId,
    int limit = 20,
    int offset = 0,
    String? startDate,
    String? endDate,
  }) async {
    try {
      final queryParams = {
        'user_id': userId,
        'limit': limit.toString(),
        'offset': offset.toString(),
      };
      
      if (startDate != null) queryParams['start_date'] = startDate;
      if (endDate != null) queryParams['end_date'] = endDate;

      final response = await _apiService.get(
        '/history/analyses',
        queryParameters: queryParams,
      );

      if (response.data['status'] == 'success') {
        return AnalysisHistoryResponse.fromJson(response.data['data']);
      } else {
        throw Exception('履歴の取得に失敗しました');
      }
    } catch (e) {
      throw Exception('履歴取得エラー: $e');
    }
  }

  /// 特定の分析結果の詳細を取得
  Future<GaitAnalysisResponse> getAnalysisDetail({
    required String userId,
    required String analysisId,
  }) async {
    try {
      final response = await _apiService.get(
        '/history/analyses/$analysisId',
        queryParameters: {'user_id': userId},
      );

      if (response.data['status'] == 'success') {
        return GaitAnalysisResponse.fromJson(response.data['data']);
      } else {
        throw Exception('分析詳細の取得に失敗しました');
      }
    } catch (e) {
      throw Exception('分析詳細取得エラー: $e');
    }
  }

  /// 分析結果を削除
  Future<bool> deleteAnalysis({
    required String userId,
    required String analysisId,
  }) async {
    try {
      final response = await _apiService.delete(
        '/history/analyses/$analysisId',
        queryParameters: {'user_id': userId},
      );

      return response.data['status'] == 'success';
    } catch (e) {
      throw Exception('分析削除エラー: $e');
    }
  }

  /// ユーザーの統計情報を取得
  Future<UserStatistics> getUserStatistics({
    required String userId,
  }) async {
    try {
      final response = await _apiService.get(
        '/history/statistics',
        queryParameters: {'user_id': userId},
      );

      if (response.data['status'] == 'success') {
        return UserStatistics.fromJson(response.data['data']);
      } else {
        throw Exception('統計情報の取得に失敗しました');
      }
    } catch (e) {
      throw Exception('統計情報取得エラー: $e');
    }
  }

  /// 分析結果を履歴に保存
  Future<bool> saveAnalysisToHistory({
    required String userId,
    required GaitAnalysisResponse analysisResult,
    Map<String, dynamic>? videoInfo,
  }) async {
    try {
      final response = await _apiService.post(
        '/history/analyses/${analysisResult.analysisId}/save',
        data: analysisResult.toJson(),
        queryParameters: {'user_id': userId},
      );

      return response.data['status'] == 'success';
    } catch (e) {
      throw Exception('履歴保存エラー: $e');
    }
  }

  /// 過去の分析結果と比較
  Future<AnalysisComparison?> compareWithPrevious({
    required String userId,
    required String analysisId,
    String? compareWith,
  }) async {
    try {
      final queryParams = {'user_id': userId};
      if (compareWith != null) {
        queryParams['compare_with'] = compareWith;
      }

      final response = await _apiService.get(
        '/history/analyses/$analysisId/compare',
        queryParameters: queryParams,
      );

      if (response.data['status'] == 'success') {
        final comparisonData = response.data['data']['comparison'];
        if (comparisonData != null) {
          return AnalysisComparison.fromJson(response.data['data']);
        }
      }
      return null;
    } catch (e) {
      throw Exception('比較処理エラー: $e');
    }
  }
}

/// 分析履歴レスポンス
class AnalysisHistoryResponse {
  final List<AnalysisHistoryItem> analyses;
  final int totalCount;
  final int limit;
  final int offset;
  final bool hasMore;

  AnalysisHistoryResponse({
    required this.analyses,
    required this.totalCount,
    required this.limit,
    required this.offset,
    required this.hasMore,
  });

  factory AnalysisHistoryResponse.fromJson(Map<String, dynamic> json) {
    return AnalysisHistoryResponse(
      analyses: (json['analyses'] as List)
          .map((item) => AnalysisHistoryItem.fromJson(item))
          .toList(),
      totalCount: json['total_count'],
      limit: json['limit'],
      offset: json['offset'],
      hasMore: json['has_more'],
    );
  }
}

/// 分析履歴項目
class AnalysisHistoryItem {
  final String id;
  final String analysisId;
  final DateTime analysisDate;
  final double? overallGaitScore;
  final double? videoQualityScore;
  final int gaitCyclesDetected;
  final String analysisMode;
  final double processingTimeSeconds;
  final bool hasReports;

  AnalysisHistoryItem({
    required this.id,
    required this.analysisId,
    required this.analysisDate,
    this.overallGaitScore,
    this.videoQualityScore,
    required this.gaitCyclesDetected,
    required this.analysisMode,
    required this.processingTimeSeconds,
    required this.hasReports,
  });

  factory AnalysisHistoryItem.fromJson(Map<String, dynamic> json) {
    return AnalysisHistoryItem(
      id: json['id'],
      analysisId: json['analysis_id'],
      analysisDate: DateTime.parse(json['analysis_date']),
      overallGaitScore: json['overall_gait_score']?.toDouble(),
      videoQualityScore: json['video_quality_score']?.toDouble(),
      gaitCyclesDetected: json['gait_cycles_detected'],
      analysisMode: json['analysis_mode'],
      processingTimeSeconds: json['processing_time_seconds']?.toDouble() ?? 0.0,
      hasReports: json['has_reports'] ?? false,
    );
  }
}

/// ユーザー統計情報
class UserStatistics {
  final int totalAnalyses;
  final int thisMonthAnalyses;
  final double averageScore;
  final DateTime? latestAnalysisDate;
  final double? latestScore;
  final List<ScoreTrendData> scoreTrend;

  UserStatistics({
    required this.totalAnalyses,
    required this.thisMonthAnalyses,
    required this.averageScore,
    this.latestAnalysisDate,
    this.latestScore,
    required this.scoreTrend,
  });

  factory UserStatistics.fromJson(Map<String, dynamic> json) {
    return UserStatistics(
      totalAnalyses: json['total_analyses'],
      thisMonthAnalyses: json['this_month_analyses'],
      averageScore: json['average_score']?.toDouble() ?? 0.0,
      latestAnalysisDate: json['latest_analysis_date'] != null
          ? DateTime.parse(json['latest_analysis_date'])
          : null,
      latestScore: json['latest_score']?.toDouble(),
      scoreTrend: (json['score_trend'] as List? ?? [])
          .map((item) => ScoreTrendData.fromJson(item))
          .toList(),
    );
  }
}

/// スコア傾向データ
class ScoreTrendData {
  final DateTime date;
  final double score;

  ScoreTrendData({
    required this.date,
    required this.score,
  });

  factory ScoreTrendData.fromJson(Map<String, dynamic> json) {
    return ScoreTrendData(
      date: DateTime.parse(json['date']),
      score: json['score']?.toDouble() ?? 0.0,
    );
  }
}

/// 分析結果比較
class AnalysisComparison {
  final AnalysisInfo currentAnalysis;
  final AnalysisInfo previousAnalysis;
  final ComparisonData comparison;

  AnalysisComparison({
    required this.currentAnalysis,
    required this.previousAnalysis,
    required this.comparison,
  });

  factory AnalysisComparison.fromJson(Map<String, dynamic> json) {
    return AnalysisComparison(
      currentAnalysis: AnalysisInfo.fromJson(json['current_analysis']),
      previousAnalysis: AnalysisInfo.fromJson(json['previous_analysis']),
      comparison: ComparisonData.fromJson(json['comparison']),
    );
  }
}

/// 分析情報
class AnalysisInfo {
  final String analysisId;
  final DateTime timestamp;
  final double overallScore;

  AnalysisInfo({
    required this.analysisId,
    required this.timestamp,
    required this.overallScore,
  });

  factory AnalysisInfo.fromJson(Map<String, dynamic> json) {
    return AnalysisInfo(
      analysisId: json['analysis_id'],
      timestamp: DateTime.parse(json['timestamp']),
      overallScore: json['overall_score']?.toDouble() ?? 0.0,
    );
  }
}

/// 比較データ
class ComparisonData {
  final double overallScoreChange;
  final Map<String, double> spatiotemporalChanges;
  final Map<String, double> symmetryChanges;
  final RecommendationsComparison recommendationsComparison;

  ComparisonData({
    required this.overallScoreChange,
    required this.spatiotemporalChanges,
    required this.symmetryChanges,
    required this.recommendationsComparison,
  });

  factory ComparisonData.fromJson(Map<String, dynamic> json) {
    return ComparisonData(
      overallScoreChange: json['overall_score_change']?.toDouble() ?? 0.0,
      spatiotemporalChanges: Map<String, double>.from(
        json['spatiotemporal_changes']?.map((k, v) => MapEntry(k, v?.toDouble() ?? 0.0)) ?? {}
      ),
      symmetryChanges: Map<String, double>.from(
        json['symmetry_changes']?.map((k, v) => MapEntry(k, v?.toDouble() ?? 0.0)) ?? {}
      ),
      recommendationsComparison: RecommendationsComparison.fromJson(
        json['recommendations_comparison']
      ),
    );
  }
}

/// 推奨事項比較
class RecommendationsComparison {
  final List<String> current;
  final List<String> previous;
  final List<String> newRecommendations;
  final List<String> resolvedIssues;

  RecommendationsComparison({
    required this.current,
    required this.previous,
    required this.newRecommendations,
    required this.resolvedIssues,
  });

  factory RecommendationsComparison.fromJson(Map<String, dynamic> json) {
    return RecommendationsComparison(
      current: List<String>.from(json['current'] ?? []),
      previous: List<String>.from(json['previous'] ?? []),
      newRecommendations: List<String>.from(json['new_recommendations'] ?? []),
      resolvedIssues: List<String>.from(json['resolved_issues'] ?? []),
    );
  }
}
