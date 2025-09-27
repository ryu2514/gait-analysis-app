# Enhanced Gait Analysis API Demo Guide
# 拡張歩行分析API デモガイド

## 🎯 概要

Enhanced MediaPipe Gait Analysis API v2.0のデモ環境セットアップと使用方法を説明します。

### 🚀 新機能ハイライト

- **30秒高速処理**: 撮影からレポート出力まで30秒以内
- **33ランドマーク活用**: MediaPipe Pose v0.10の全機能
- **代償動作検出**: 自動アラート機能付き
- **重心・バランス分析**: COM軌跡とバランス安定性評価
- **拡張出力**: 正規化波形グラフ、スローモーション動画、カラーPDFレポート

## 📋 前提条件

### システム要件
- **OS**: macOS, Linux, Windows (Docker対応)
- **Docker**: 20.10.0+
- **Docker Compose**: 2.0.0+
- **CPU**: 4コア以上推奨
- **メモリ**: 8GB以上推奨
- **ストレージ**: 5GB以上の空き容量

### 推奨環境
- **CPU**: Intel i7 / AMD Ryzen 7 以上
- **メモリ**: 16GB
- **GPU**: MediaPipe最適化用（オプション）

## 🚀 クイックスタート

### 1. リポジトリクローン
```bash
git clone https://github.com/your-org/gait-analysis-app.git
cd gait-analysis-app/backend
```

### 2. デモ環境デプロイ
```bash
# 標準デプロイ
./demo_deploy.sh

# Nginxプロキシ付きデプロイ
./demo_deploy.sh --with-nginx
```

### 3. 動作確認
```bash
# ヘルスチェック
curl http://localhost:8000/api/v1/health

# 機能確認
curl http://localhost:8000/api/v1/gait-analysis/capabilities
```

## 📊 API使用例

### 基本的な拡張分析

```bash
curl -X POST "http://localhost:8000/api/v1/gait-analysis/analyze-enhanced" \
  -H "Content-Type: multipart/form-data" \
  -F "video=@your_gait_video.mp4" \
  -F "user_height_cm=170" \
  -F "analysis_mode=detailed" \
  -F "camera_position=side" \
  -F "target_fps=60" \
  -F "enable_30s_optimization=true" \
  -F "enable_compensation_alerts=true" \
  -F "enable_balance_analysis=true" \
  -F "generate_enhanced_output=true"
```

### 高速分析（30秒最適化）

```bash
curl -X POST "http://localhost:8000/api/v1/gait-analysis/analyze-enhanced" \
  -H "Content-Type: multipart/form-data" \
  -F "video=@your_gait_video.mp4" \
  -F "user_height_cm=170" \
  -F "analysis_mode=standard" \
  -F "enable_30s_optimization=true" \
  -F "device_type=mobile"
```

### 結果取得

```bash
# 分析結果取得
curl "http://localhost:8000/api/v1/gait-analysis/analysis-enhanced/{analysis_id}"

# PDFレポートダウンロード
curl "http://localhost:8000/api/v1/gait-analysis/download-report/{analysis_id}?format=pdf" \
  -o gait_report.pdf

# スローモーション動画ダウンロード
curl "http://localhost:8000/api/v1/gait-analysis/download-report/{analysis_id}?format=video" \
  -o skeleton_video.mp4
```

## 🎬 サンプル動画

### 動画撮影ガイドライン

#### 📹 撮影設定
- **解像度**: 720p以上（1080p推奨）
- **フレームレート**: 30-60fps
- **時間**: 5-30秒
- **ファイルサイズ**: 100MB以下

#### 📐 カメラ設置
- **距離**: 3-5メートル
- **高さ**: 腰の高さ（約1メートル）
- **角度**: 
  - 側面撮影（推奨）: 歩行方向に対して90度
  - 後方撮影: 歩行方向に対して180度
  - 前方撮影: 歩行方向に対して0度

#### 🌟 撮影環境
- **照明**: 十分な自然光または照明
- **背景**: シンプルで一様な背景
- **床面**: 平坦で滑りにくい表面
- **服装**: 体のラインが分かりやすい服装

### サンプルデータ

```bash
# デモデータ確認
curl http://localhost:8000/api/v1/gait-analysis/demo-data
```

## 📊 分析結果の解釈

### 時空間パラメータ

```json
{
  "gait_speed_ms": 1.25,           // 歩行速度 (m/s)
  "cadence_steps_per_min": 115,    // ケイデンス (歩/分)
  "step_length_cm": 65.2,          // 歩幅 (cm)
  "stride_length_cm": 130.4,       // ストライド長 (cm)
  "stance_time_percent": 60.5,     // 立脚時間 (%)
  "swing_time_percent": 39.5,      // 遊脚時間 (%)
  "stance_time_asymmetry_percent": 3.2  // 非対称性 (%)
}
```

### 正常値範囲
- **歩行速度**: 1.2-1.4 m/s
- **ケイデンス**: 110-130 歩/分
- **立脚時間**: 58-62%
- **非対称性**: <5%

### キネマティクス指標

```json
{
  "hip_rom_deg": 35.8,             // 股関節可動域 (度)
  "knee_max_flexion_deg": 65.4,    // 膝関節最大屈曲 (度)
  "ankle_toe_off_deg": 15.3,       // トーオフ時足関節角度 (度)
  "pelvic_list_deg": [2.1, 1.8],  // 骨盤リスト時系列 (度)
  "trunk_rotation_deg": [5.2, 4.9] // 体幹回旋時系列 (度)
}
```

### バランス指標

```json
{
  "lateral_displacement_max_cm": 4.2,    // 最大左右移動幅 (cm)
  "vertical_displacement_max_cm": 3.8,   // 最大上下変位 (cm)
  "balance_stability_score": 85.6,       // バランス安定性スコア (0-100)
  "com_projection_x": [-2.1, 0.5, 2.3], // 重心投影線X座標
  "com_projection_y": [-1.2, 0.8, 1.5]  // 重心投影線Y座標
}
```

### 代償動作アラート

```json
{
  "alert_type": "knee_valgus",        // アラートタイプ
  "severity": "medium",               // 重要度
  "message": "右膝外反検出: 12.3°",    // メッセージ
  "frame_range": [45, 67],           // 発生フレーム範囲
  "threshold_value": 10.0,           // しきい値
  "measured_value": 12.3             // 測定値
}
```

## 🎯 分析モード

### Quick Mode
- **処理時間**: 10-15秒
- **機能**: 基本時空間パラメータのみ
- **用途**: スクリーニング

### Standard Mode
- **処理時間**: 20-25秒
- **機能**: 時空間＋関節角度＋代償動作検出
- **用途**: 一般的な歩行評価

### Detailed Mode
- **処理時間**: 25-30秒
- **機能**: 全機能（バランス分析、拡張出力含む）
- **用途**: 詳細な臨床評価

## 🔧 トラブルシューティング

### よくある問題

#### 1. 動画アップロードエラー
```bash
# ファイルサイズ確認
ls -lh your_video.mp4

# 対応形式確認
curl http://localhost:8000/api/v1/gait-analysis/supported-formats
```

#### 2. 処理時間が30秒を超える
- 動画解像度を下げる（720p推奨）
- 動画時間を短縮する（10-15秒）
- `enable_30s_optimization=true`を設定

#### 3. ポーズ検出精度が低い
- 照明環境を改善
- 背景をシンプルにする
- カメラ距離を調整（3-5m）

### ログ確認

```bash
# アプリケーションログ
docker-compose -f docker-compose.demo.yml logs -f gait-api-demo

# 全サービスログ
docker-compose -f docker-compose.demo.yml logs -f

# エラーログのみ
docker-compose -f docker-compose.demo.yml logs --tail=50 gait-api-demo | grep ERROR
```

### サービス再起動

```bash
# 個別サービス再起動
docker-compose -f docker-compose.demo.yml restart gait-api-demo

# 全サービス再起動
docker-compose -f docker-compose.demo.yml restart

# クリーン再起動
./demo_deploy.sh --stop
./demo_deploy.sh
```

## 📈 パフォーマンステスト

### 処理時間測定

```bash
# タイムスタンプ付きテスト
start_time=$(date +%s)
curl -X POST "http://localhost:8000/api/v1/gait-analysis/analyze-enhanced" \
  -F "video=@test_video.mp4" \
  -F "analysis_mode=detailed" \
  -F "enable_30s_optimization=true"
end_time=$(date +%s)
echo "Processing time: $((end_time - start_time)) seconds"
```

### 負荷テスト

```bash
# 同時リクエストテスト（注意：デモ環境用）
for i in {1..3}; do
  curl -X POST "http://localhost:8000/api/v1/gait-analysis/analyze-enhanced" \
    -F "video=@test_video.mp4" \
    -F "analysis_mode=standard" &
done
wait
```

## 🎓 学習リソース

### 歩行分析基礎
- [歩行周期の基本](docs/gait_cycle_basics.md)
- [時空間パラメータの解釈](docs/spatiotemporal_interpretation.md)
- [代償動作パターン](docs/compensation_patterns.md)

### API活用
- [Python クライアント例](examples/python_client.py)
- [JavaScript 統合例](examples/js_integration.html)
- [CLI ツール](tools/gait_cli.py)

## 📞 サポート

### 技術サポート
- **Email**: support@gaitanalysis.com
- **Documentation**: http://localhost:8000/docs
- **GitHub Issues**: [Issues Page](https://github.com/your-org/gait-analysis-app/issues)

### コミュニティ
- **Discord**: [開発者コミュニティ](https://discord.gg/gaitanalysis)
- **Forum**: [技術フォーラム](https://forum.gaitanalysis.com)

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照

---

## 🎉 おわりに

Enhanced MediaPipe Gait Analysis API v2.0 デモ環境へようこそ！

この最新のAPIは以下の特徴を持ちます：
- ✅ 30秒高速処理
- ✅ 33ランドマーク活用
- ✅ 代償動作自動検出
- ✅ バランス・重心分析
- ✅ 拡張出力形式

医療・スポーツ・研究の各分野でご活用ください。

**Happy Analyzing! 🚶‍♂️💨**