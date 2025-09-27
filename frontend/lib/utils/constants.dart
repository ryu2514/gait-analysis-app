class AppConstants {
  // API設定
  // 本番では --dart-define=API_BASE_URL=... で上書き可能にする
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000/api/v1',
  );
  
  // 動画設定
  static const int maxVideoSizeMB = 100;
  static const int maxVideoDurationSeconds = 30;
  static const int targetFPS = 30;
  static const List<String> supportedFormats = ['mp4', 'mov', 'avi', 'webm'];
  
  // UI設定
  static const double defaultPadding = 16.0;
  static const double defaultRadius = 12.0;
  static const double cardElevation = 4.0;
  
  // 分析設定
  static const int minGaitCycles = 2;
  static const double symmetryThreshold = 10.0;
  
  // 撮影ガイドライン
  static const String shootingDistance = '3-5m';
  static const String recommendedAngle = '側方または前方';
  static const String recommendedDuration = '5-10秒';
  
  // スコア閾値
  static const double excellentScoreThreshold = 85.0;
  static const double goodScoreThreshold = 70.0;
  static const double fairScoreThreshold = 50.0;
}

class AppStrings {
  // アプリ名
  static const String appName = 'MediaPipe歩行分析';
  static const String appDescription = 'スマートフォンで簡単歩行評価';
  
  // ナビゲーション
  static const String homeTab = 'ホーム';
  static const String historyTab = '履歴';
  static const String guideTab = 'ガイド';
  static const String settingsTab = '設定';
  
  // 分析関連
  static const String startAnalysis = '歩行を測定';
  static const String analyzing = '分析中...';
  static const String analysisComplete = '分析完了';
  static const String analysisError = '分析エラー';
  
  // 結果
  static const String overallScore = '総合スコア';
  static const String gaitSpeed = '歩行速度';
  static const String symmetryIndex = '対称性指数';
  static const String recommendations = '改善提案';
  
  // エラーメッセージ
  static const String networkError = 'ネットワークエラーが発生しました';
  static const String videoTooLarge = 'ファイルサイズが大きすぎます';
  static const String unsupportedFormat = 'サポートされていないファイル形式です';
  static const String cameraPermissionDenied = 'カメラの許可が必要です';
}

class AppColors {
  // プライマリカラー
  static const Color primary = Color(0xFF2196F3);
  static const Color primaryDark = Color(0xFF1976D2);
  static const Color primaryLight = Color(0xFFBBDEFB);
  
  // アクセントカラー
  static const Color accent = Color(0xFF4CAF50);
  static const Color accentDark = Color(0xFF388E3C);
  
  // グレースケール
  static const Color textPrimary = Color(0xFF212121);
  static const Color textSecondary = Color(0xFF757575);
  static const Color background = Color(0xFFFAFAFA);
  static const Color surface = Color(0xFFFFFFFF);
  static const Color divider = Color(0xFFBDBDBD);
  
  // ステータスカラー
  static const Color success = Color(0xFF4CAF50);
  static const Color warning = Color(0xFFFF9800);
  static const Color error = Color(0xFFF44336);
  static const Color info = Color(0xFF2196F3);
  
  // スコアカラー
  static const Color excellentScore = Color(0xFF4CAF50);
  static const Color goodScore = Color(0xFF8BC34A);
  static const Color fairScore = Color(0xFFFF9800);
  static const Color poorScore = Color(0xFFF44336);
}

class AppAssets {
  // 画像
  static const String logoPath = 'assets/images/logo.png';
  static const String walkingGuidePath = 'assets/images/walking_guide.png';
  static const String cameraGuidePath = 'assets/images/camera_guide.png';
  
  // アイコン
  static const String homeIcon = 'assets/icons/home.svg';
  static const String historyIcon = 'assets/icons/history.svg';
  static const String guideIcon = 'assets/icons/guide.svg';
  static const String settingsIcon = 'assets/icons/settings.svg';
  
  // アニメーション
  static const String loadingAnimation = 'assets/animations/loading.json';
  static const String successAnimation = 'assets/animations/success.json';
  static const String errorAnimation = 'assets/animations/error.json';
}
