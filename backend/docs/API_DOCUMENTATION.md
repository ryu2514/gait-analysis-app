# Enhanced MediaPipe Gait Analysis API

**Version:** 2.0.0-enhanced  
**Generated:** 2025-09-11 05:12:25

## Description


    ## Enhanced MediaPipe歩行分析API v2.0

    スマートフォンで撮影した動画から歩行パターンを分析し、
    理学療法士や医療従事者向けの詳細なレポートを生成する拡張APIです。

    ### 🚀 新機能（v2.0 Enhanced）
    - **30秒高速処理**: 撮影からレポート出力まで30秒以内
    - **33ランドマーク活用**: MediaPipe Pose v0.10の全機能
    - **代償動作検出**: 自動アラート機能付き
    - **重心・バランス分析**: COM軌跡とバランス安定性評価
    - **拡張出力**: 正規化波形グラフ、スローモーション動画、カラーPDFレポート
    - **iPad/iPhone最適化**: 60fps対応、横・後方撮影モード

    ### 📊 詳細分析機能
    - **スパイオテンポラル指標**: ピッチ、歩幅/ストライド長、立脚/遊脚時間、対称性指標
    - **キネマティクス**: 股関節ROM、膝関節詳細角度、足関節背屈/底屈、骨盤・体幹回旋
    - **代償動作アラート**: アウト/イントゥーイング、膝外反/内反、トレンデレンブルグ、ペルビックドロップ
    - **バランス指標**: COM水平/垂直移動幅、重心投影線2Dマップ

    ### 🎯 対象ユーザー
    - **理学療法士**: 詳細な歩行評価と治療計画立案
    - **作業療法士**: 日常生活動作の評価
    - **医師**: 診断支援と経過観察
    - **研究者**: 歩行データの定量的解析
    - **アスリート・トレーナー**: パフォーマンス向上

    ### ⚙️ 技術仕様（Enhanced）
    - **バックエンド**: FastAPI + Python 3.11+
    - **AI処理**: MediaPipe Pose v0.10 + 最高精度モデル
    - **並列処理**: マルチコア活用による高速化
    - **データベース**: PostgreSQL + Redis キャッシュ
    - **認証**: Firebase Auth + JWT
    - **監視**: リアルタイムパフォーマンス監視
    - **出力**: PDF/MP4/JSON/CSV 多形式対応
    

## Base URLs

- **Development:** http://localhost:8000
- **Production:** https://api.gaitanalysis.com

## Authentication

This API supports multiple authentication methods:

### Bearer Token (JWT)
```
Authorization: Bearer <your-jwt-token>
```

### Firebase Authentication
OAuth2 flow with Google accounts:
- **Authorization URL:** https://accounts.google.com/o/oauth2/auth
- **Scopes:** openid, email, profile

## API Endpoints

### health

#### `GET /api/v1/health`

**Summary:** Health Check

**Description:** システムヘルスチェック

Returns:
    dict: システム状態情報

**Responses:**

**200:** Successful Response


---

#### `GET /api/v1/ready`

**Summary:** Readiness Check

**Description:** レディネスチェック（Kubernetes用）

Returns:
    dict: サービス準備状態

**Responses:**

**200:** Successful Response


---

### gait-analysis

#### `POST /api/v1/gait-analysis/analyze`

**Summary:** Analyze Gait

**Description:** 歩行動画分析エンドポイント

Args:
    video: アップロードされた歩行動画ファイル
    user_height_cm: ユーザーの身長（cm）
    analysis_mode: 分析モード（standard, detailed, quick）

Returns:
    GaitAnalysisResponse: 歩行分析結果

**Parameters:**

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| user_height_cm | string | query | No |  |
| analysis_mode | string | query | No |  |

**Request Body:**

**Responses:**

**200:** Successful Response

```json
{}
```

**422:** Validation Error

```json
{}
```


---

#### `GET /api/v1/gait-analysis/analysis/{analysis_id}`

**Summary:** Get Analysis Result

**Description:** 分析結果取得エンドポイント

Args:
    analysis_id: 分析ID

Returns:
    dict: 分析結果または状態

**Parameters:**

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| analysis_id | string | path | Yes |  |

**Responses:**

**200:** Successful Response

**422:** Validation Error

```json
{}
```


---

#### `GET /api/v1/gait-analysis/supported-formats`

**Summary:** Get Supported Formats

**Description:** サポートされている動画フォーマット一覧取得

Returns:
    dict: サポートフォーマット情報

**Responses:**

**200:** Successful Response


---

### enhanced-gait-analysis

#### `POST /api/v1/gait-analysis/analyze-enhanced`

**Summary:** Analyze Gait Enhanced

**Description:** 拡張歩行分析エンドポイント

新機能を全て統合した最新の歩行分析API
- 30秒高速処理
- 33ランドマーク活用
- 代償動作検出
- バランス・重心分析
- 拡張出力（正規化グラフ、動画、PDFレポート）

**Parameters:**

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| user_height_cm | string | query | No | ユーザー身長（cm） |
| analysis_mode | string | query | No | 分析モード（standard/detailed/quick） |
| camera_position | string | query | No | カメラ位置（side/posterior/anterior） |
| target_fps | integer | query | No | 目標フレームレート |
| device_type | string | query | No | デバイスタイプ（mobile/tablet/desktop） |
| enable_30s_optimization | boolean | query | No | 30秒最適化有効化 |
| enable_compensation_alerts | boolean | query | No | 代償動作アラート有効化 |
| enable_balance_analysis | boolean | query | No | バランス分析有効化 |
| generate_enhanced_output | boolean | query | No | 拡張出力生成有効化 |

**Request Body:**

**Responses:**

**200:** Successful Response

```json
{}
```

**422:** Validation Error

```json
{}
```


---

#### `GET /api/v1/gait-analysis/analysis-enhanced/{analysis_id}`

**Summary:** Get Enhanced Analysis Result

**Description:** 拡張分析結果取得エンドポイント

**Parameters:**

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| analysis_id | string | path | Yes |  |

**Responses:**

**200:** Successful Response

**422:** Validation Error

```json
{}
```


---

#### `GET /api/v1/gait-analysis/download-report/{analysis_id}`

**Summary:** Download Analysis Report

**Description:** 分析レポートダウンロードエンドポイント

**Parameters:**

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| analysis_id | string | path | Yes |  |
| format | string | query | No | レポート形式（pdf/video/json） |

**Responses:**

**200:** Successful Response

**422:** Validation Error

```json
{}
```


---

#### `GET /api/v1/gait-analysis/capabilities`

**Summary:** Get Enhanced Capabilities

**Description:** 拡張機能一覧取得エンドポイント

**Responses:**

**200:** Successful Response


---

#### `GET /api/v1/gait-analysis/demo-data`

**Summary:** Get Demo Data

**Description:** デモ用サンプルデータ取得エンドポイント

**Responses:**

**200:** Successful Response


---

### auth

#### `POST /api/v1/auth/register`

**Summary:** Register

**Description:** 新規ユーザー登録

Args:
    user_data: ユーザー登録データ
    request: HTTPリクエスト
    db: データベースセッション
    
Returns:
    TokenResponse: 認証トークンとユーザー情報

**Request Body:**

```json
{}
```

**Responses:**

**201:** Successful Response

```json
{}
```

**422:** Validation Error

```json
{}
```


---

#### `POST /api/v1/auth/login`

**Summary:** Login

**Description:** ユーザーログイン

Args:
    user_data: ログインデータ
    request: HTTPリクエスト
    db: データベースセッション
    
Returns:
    TokenResponse: 認証トークンとユーザー情報

**Request Body:**

```json
{}
```

**Responses:**

**200:** Successful Response

```json
{}
```

**422:** Validation Error

```json
{}
```


---

#### `POST /api/v1/auth/firebase`

**Summary:** Firebase Login

**Description:** Firebase認証ログイン

Args:
    firebase_token: FirebaseIDトークン
    request: HTTPリクエスト
    db: データベースセッション
    
Returns:
    TokenResponse: 認証トークンとユーザー情報

**Request Body:**

```json
{}
```

**Responses:**

**200:** Successful Response

```json
{}
```

**422:** Validation Error

```json
{}
```


---

#### `GET /api/v1/auth/me`

**Summary:** Get Current User Info

**Description:** 現在のユーザー情報取得

Args:
    current_user: 現在のユーザー（認証情報）
    db: データベースセッション
    
Returns:
    UserResponse: ユーザー情報

**Responses:**

**200:** Successful Response

```json
{}
```


---

#### `PUT /api/v1/auth/me`

**Summary:** Update Current User

**Description:** 現在のユーザー情報更新

Args:
    user_data: 更新データ
    current_user: 現在のユーザー（認証情報）
    db: データベースセッション
    
Returns:
    UserResponse: 更新後のユーザー情報

**Request Body:**

```json
{}
```

**Responses:**

**200:** Successful Response

```json
{}
```

**422:** Validation Error

```json
{}
```


---

#### `GET /api/v1/auth/stats`

**Summary:** Get User Statistics

**Description:** ユーザー統計情報取得

Args:
    current_user: 現在のユーザー（認証情報）
    db: データベースセッション
    
Returns:
    UserStats: ユーザー統計情報

**Responses:**

**200:** Successful Response

```json
{}
```


---

#### `POST /api/v1/auth/verify-token`

**Summary:** Verify Token

**Description:** トークン検証

Args:
    current_user: 現在のユーザー（認証情報）
    
Returns:
    dict: トークン検証結果

**Responses:**

**200:** Successful Response


---

#### `POST /api/v1/auth/password/reset`

**Summary:** Request Password Reset

**Description:** パスワードリセット要求

Args:
    reset_data: パスワードリセットデータ
    db: データベースセッション
    
Returns:
    dict: リセット要求結果

**Request Body:**

```json
{}
```

**Responses:**

**200:** Successful Response

**422:** Validation Error

```json
{}
```


---

#### `GET /api/v1/auth/login-history`

**Summary:** Get Login History

**Description:** ログイン履歴取得

Args:
    limit: 取得件数
    current_user: 現在のユーザー（認証情報）
    db: データベースセッション
    
Returns:
    dict: ログイン履歴

**Parameters:**

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| limit | integer | query | No |  |

**Responses:**

**200:** Successful Response

**422:** Validation Error

```json
{}
```


---

### reports

#### `POST /api/v1/reports/generate/pdf`

**Summary:** Generate Pdf Report

**Description:** PDF形式の詳細レポートを生成

Args:
    analysis_result: 歩行分析結果データ
    patient_info: 患者情報（オプション）
    background_tasks: バックグラウンドタスク
    
Returns:
    FileResponse: 生成されたPDFファイル

**Request Body:**

```json
{}
```

**Responses:**

**200:** Successful Response

**422:** Validation Error

```json
{}
```


---

#### `POST /api/v1/reports/generate/png`

**Summary:** Generate Png Summary

**Description:** PNG形式のサマリー画像を生成

Args:
    analysis_result: 歩行分析結果データ
    width: 画像幅（ピクセル）
    height: 画像高さ（ピクセル）
    background_tasks: バックグラウンドタスク
    
Returns:
    FileResponse: 生成されたPNG画像ファイル

**Parameters:**

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| width | integer | query | No |  |
| height | integer | query | No |  |

**Request Body:**

```json
{}
```

**Responses:**

**200:** Successful Response

**422:** Validation Error

```json
{}
```


---

#### `POST /api/v1/reports/generate/base64`

**Summary:** Generate Base64 Image

**Description:** Base64エンコードされた画像を生成（Web表示用）

Args:
    analysis_result: 歩行分析結果データ
    
Returns:
    JSONResponse: Base64エンコードされた画像データ

**Request Body:**

```json
{}
```

**Responses:**

**200:** Successful Response

**422:** Validation Error

```json
{}
```


---

#### `GET /api/v1/reports/templates`

**Summary:** Get Report Templates

**Description:** 利用可能なレポートテンプレート一覧を取得

Returns:
    JSONResponse: テンプレート情報

**Responses:**

**200:** Successful Response


---

#### `POST /api/v1/reports/generate/custom`

**Summary:** Generate Custom Report

**Description:** カスタムレポートを生成

Args:
    analysis_result: 歩行分析結果データ
    template_config: レポート設定
    patient_info: 患者情報（オプション）
    background_tasks: バックグラウンドタスク
    
Returns:
    FileResponse: 生成されたレポートファイル

**Request Body:**

```json
{}
```

**Responses:**

**200:** Successful Response

**422:** Validation Error

```json
{}
```


---

#### `GET /api/v1/reports/status/{analysis_id}`

**Summary:** Get Report Status

**Description:** レポート生成状況を確認

Args:
    analysis_id: 分析ID
    
Returns:
    JSONResponse: レポート状況

**Parameters:**

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| analysis_id | string | path | Yes |  |

**Responses:**

**200:** Successful Response

**422:** Validation Error

```json
{}
```


---

### history

#### `GET /api/v1/history/analyses`

**Summary:** Get Analysis History

**Description:** ユーザーの分析履歴を取得

Args:
    user_id: ユーザーID
    limit: 取得件数制限（1-100）
    offset: オフセット
    start_date: 開始日時
    end_date: 終了日時
    
Returns:
    JSONResponse: 分析履歴リスト

**Parameters:**

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| user_id | string | query | Yes | ユーザーID |
| limit | integer | query | No | 取得件数制限 |
| offset | integer | query | No | オフセット |
| start_date | string | query | No | 開始日時（ISO8601形式） |
| end_date | string | query | No | 終了日時（ISO8601形式） |

**Responses:**

**200:** Successful Response

**422:** Validation Error

```json
{}
```


---

#### `GET /api/v1/history/analyses/{analysis_id}`

**Summary:** Get Analysis Detail

**Description:** 特定の分析結果の詳細を取得

Args:
    analysis_id: 分析ID
    user_id: ユーザーID
    
Returns:
    JSONResponse: 分析結果詳細

**Parameters:**

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| analysis_id | string | path | Yes |  |
| user_id | string | query | Yes | ユーザーID |

**Responses:**

**200:** Successful Response

**422:** Validation Error

```json
{}
```


---

#### `DELETE /api/v1/history/analyses/{analysis_id}`

**Summary:** Delete Analysis

**Description:** 分析結果を削除

Args:
    analysis_id: 分析ID
    user_id: ユーザーID
    
Returns:
    JSONResponse: 削除結果

**Parameters:**

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| analysis_id | string | path | Yes |  |
| user_id | string | query | Yes | ユーザーID |

**Responses:**

**200:** Successful Response

**422:** Validation Error

```json
{}
```


---

#### `GET /api/v1/history/statistics`

**Summary:** Get User Statistics

**Description:** ユーザーの統計情報を取得

Args:
    user_id: ユーザーID
    
Returns:
    JSONResponse: 統計情報

**Parameters:**

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| user_id | string | query | Yes | ユーザーID |

**Responses:**

**200:** Successful Response

**422:** Validation Error

```json
{}
```


---

#### `POST /api/v1/history/analyses/{analysis_id}/save`

**Summary:** Save Analysis To History

**Description:** 分析結果を履歴に保存

Args:
    analysis_id: 分析ID
    user_id: ユーザーID
    analysis_result: 分析結果データ
    video_info: 動画情報
    
Returns:
    JSONResponse: 保存結果

**Parameters:**

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| analysis_id | string | path | Yes |  |
| user_id | string | query | Yes | ユーザーID |

**Request Body:**

```json
{}
```

**Responses:**

**200:** Successful Response

**422:** Validation Error

```json
{}
```


---

#### `GET /api/v1/history/analyses/{analysis_id}/compare`

**Summary:** Compare With Previous

**Description:** 過去の分析結果と比較

Args:
    analysis_id: 現在の分析ID
    user_id: ユーザーID
    compare_with: 比較対象の分析ID（未指定の場合は直前の分析）
    
Returns:
    JSONResponse: 比較結果

**Parameters:**

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| analysis_id | string | path | Yes |  |
| user_id | string | query | Yes | ユーザーID |
| compare_with | string | query | No | 比較対象の分析ID |

**Responses:**

**200:** Successful Response

**422:** Validation Error

```json
{}
```


---

### performance

#### `GET /api/v1/performance/metrics/system`

**Summary:** Get System Metrics

**Description:** システムメトリクスを取得

**Responses:**

**200:** Successful Response


---

#### `GET /api/v1/performance/metrics/performance`

**Summary:** Get Performance Metrics

**Description:** パフォーマンスメトリクスを取得

**Parameters:**

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| metric_name | string | query | No | 特定のメトリクス名 |
| hours | integer | query | No | 取得する時間範囲（時間） |

**Responses:**

**200:** Successful Response

**422:** Validation Error

```json
{}
```


---

#### `GET /api/v1/performance/metrics/cache`

**Summary:** Get Cache Metrics

**Description:** キャッシュメトリクスを取得

**Responses:**

**200:** Successful Response


---

#### `GET /api/v1/performance/metrics/tasks`

**Summary:** Get Task Metrics

**Description:** タスクキューメトリクスを取得

**Responses:**

**200:** Successful Response


---

#### `GET /api/v1/performance/metrics/video_processing`

**Summary:** Get Video Processing Metrics

**Description:** 動画処理メトリクスを取得

**Responses:**

**200:** Successful Response


---

#### `GET /api/v1/performance/alerts`

**Summary:** Get Performance Alerts

**Description:** パフォーマンスアラートを取得

**Parameters:**

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| hours | integer | query | No | 取得する時間範囲（時間） |
| severity | string | query | No | アラートの重要度フィルタ |

**Responses:**

**200:** Successful Response

**422:** Validation Error

```json
{}
```


---

#### `GET /api/v1/performance/optimization/suggestions`

**Summary:** Get Optimization Suggestions

**Description:** 最適化提案を取得

**Responses:**

**200:** Successful Response


---

#### `POST /api/v1/performance/optimization/apply`

**Summary:** Apply Optimization

**Description:** 最適化を適用

**Parameters:**

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| optimization_type | string | query | Yes |  |

**Responses:**

**200:** Successful Response

**422:** Validation Error

```json
{}
```


---

#### `GET /api/v1/performance/dashboard`

**Summary:** Get Dashboard Html

**Description:** パフォーマンスダッシュボードのHTML

**Responses:**

**200:** Successful Response


---

### documentation

#### `GET /api/v1/docs/openapi.json`

**Summary:** Get Openapi Json

**Description:** OpenAPI仕様書をJSON形式で取得

**Responses:**

**200:** Successful Response


---

#### `GET /api/v1/docs/openapi.yaml`

**Summary:** Get Openapi Yaml

**Description:** OpenAPI仕様書をYAML形式で取得

**Responses:**

**200:** Successful Response


---

#### `GET /api/v1/docs/markdown`

**Summary:** Get Markdown Documentation

**Description:** マークダウン形式のAPIドキュメントを取得

**Responses:**

**200:** Successful Response


---

#### `GET /api/v1/docs/postman`

**Summary:** Get Postman Collection

**Description:** Postmanコレクションを取得

**Responses:**

**200:** Successful Response


---

#### `POST /api/v1/docs/generate`

**Summary:** Regenerate Documentation

**Description:** APIドキュメンテーションを再生成

**Responses:**

**200:** Successful Response


---

#### `GET /api/v1/docs/info`

**Summary:** Get Documentation Info

**Description:** ドキュメンテーション情報を取得

**Responses:**

**200:** Successful Response


---

### monitoring

#### `GET /api/v1/monitoring/`

**Summary:** Get Monitoring Dashboard

**Description:** リアルタイム監視ダッシュボードのHTML

**Responses:**

**200:** Successful Response


---

#### `GET /api/v1/monitoring/status`

**Summary:** Get Monitoring Status

**Description:** 監視システムの状態を取得

**Responses:**

**200:** Successful Response


---

#### `GET /api/v1/monitoring/metrics/current`

**Summary:** Get Current Metrics

**Description:** 現在のメトリクスを取得（REST API）

**Responses:**

**200:** Successful Response


---

#### `POST /api/v1/monitoring/alerts/clear`

**Summary:** Clear Alerts

**Description:** アラートをクリア（管理者のみ）

**Responses:**

**200:** Successful Response


---

### Default

#### `GET /`

**Summary:** Root

**Description:** ルートエンドポイント

**Responses:**

**200:** Successful Response


---

## Data Models

### Body_analyze_gait_api_v1_gait_analysis_analyze_post

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| video | string | Yes |  |

**Example:**

```json
{
  "video": "string"
}
```


### Body_analyze_gait_enhanced_api_v1_gait_analysis_analyze_enhanced_post

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| video | string | Yes |  |

**Example:**

```json
{
  "video": "string"
}
```


### Body_generate_custom_report_api_v1_reports_generate_custom_post

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| analysis_result | unknown | Yes |  |
| template_config | object | Yes |  |
| patient_info | unknown | No |  |

**Example:**

```json
{
  "analysis_result": "string",
  "template_config": {},
  "patient_info": "string"
}
```


### Body_generate_pdf_report_api_v1_reports_generate_pdf_post

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| analysis_result | unknown | Yes |  |
| patient_info | unknown | No |  |

**Example:**

```json
{
  "analysis_result": "string",
  "patient_info": "string"
}
```


### Body_save_analysis_to_history_api_v1_history_analyses__analysis_id__save_post

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| analysis_result | unknown | Yes |  |
| video_info | unknown | No |  |

**Example:**

```json
{
  "analysis_result": "string",
  "video_info": "string"
}
```


### GaitAnalysisResponse

歩行分析レスポンス

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| analysis_id | string | Yes | 分析ID |
| status | string | Yes | 分析状態 |
| timestamp | string | No | 分析完了時刻 |
| processing_time_seconds | number | Yes | 処理時間（秒） |
| spatiotemporal_params | unknown | No |  |
| symmetry_indices | unknown | No |  |
| gait_cycles | array | No | 検出された歩行周期 |
| joint_angles | unknown | No |  |
| video_quality_score | number | Yes | 動画品質スコア（0-100） |
| pose_detection_confidence | number | Yes | 姿勢検出信頼度 |
| gait_cycles_detected | integer | Yes | 検出された歩行周期数 |
| overall_gait_score | number | Yes | 総合歩行スコア（0-100） |
| recommendations | array | No | 改善提案 |
| video_info | object | No | 動画情報 |
| analysis_settings | object | No | 分析設定 |

**Example:**

```json
{
  "analysis_id": "string",
  "status": "string",
  "timestamp": "string",
  "processing_time_seconds": 0.0,
  "spatiotemporal_params": "string",
  "symmetry_indices": "string",
  "gait_cycles": [
    "string"
  ],
  "joint_angles": "string",
  "video_quality_score": 0.0,
  "pose_detection_confidence": 0.0,
  "gait_cycles_detected": 0,
  "overall_gait_score": 0.0,
  "recommendations": [
    "string"
  ],
  "video_info": {},
  "analysis_settings": {}
}
```


### GaitCycle

歩行周期データ

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| cycle_id | string | Yes | 周期ID |
| start_frame | integer | Yes | 開始フレーム |
| end_frame | integer | Yes | 終了フレーム |
| duration_seconds | number | Yes | 周期時間（秒） |
| side | string | Yes | 左右（left/right） |
| step_length_m | number | Yes | 歩幅（m） |
| step_width_m | number | Yes | 歩隔（m） |
| stance_time_seconds | number | Yes | 立脚時間（秒） |
| swing_time_seconds | number | Yes | 遊脚時間（秒） |
| stance_ratio | number | Yes | 立脚比率 |
| hip_flexion_peak_deg | number | Yes | 股関節最大屈曲角度 |
| knee_flexion_peak_deg | number | Yes | 膝関節最大屈曲角度 |
| ankle_dorsiflexion_peak_deg | number | Yes | 足関節最大背屈角度 |
| phase_timings | object | No | フェーズタイミング |

**Example:**

```json
{
  "cycle_id": "string",
  "start_frame": 0,
  "end_frame": 0,
  "duration_seconds": 0.0,
  "side": "string",
  "step_length_m": 0.0,
  "step_width_m": 0.0,
  "stance_time_seconds": 0.0,
  "swing_time_seconds": 0.0,
  "stance_ratio": 0.0,
  "hip_flexion_peak_deg": 0.0,
  "knee_flexion_peak_deg": 0.0,
  "ankle_dorsiflexion_peak_deg": 0.0,
  "phase_timings": {}
}
```


### Gender

性別

**Example:**

```json
"string"
```


### HTTPAuthorizationCredentials

The HTTP authorization credentials in the result of using `HTTPBearer` or
`HTTPDigest` in a dependency.

The HTTP authorization header value is split by the first space.

The first part is the `scheme`, the second part is the `credentials`.

For example, in an HTTP Bearer token scheme, the client will send a header
like:

```
Authorization: Bearer deadbeef12346
```

In this case:

* `scheme` will have the value `"Bearer"`
* `credentials` will have the value `"deadbeef12346"`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| scheme | string | Yes |  |
| credentials | string | Yes |  |

**Example:**

```json
{
  "scheme": "string",
  "credentials": "string"
}
```


### HTTPValidationError

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| detail | array | No |  |

**Example:**

```json
{
  "detail": [
    "string"
  ]
}
```


### JointAngles

関節角度データ

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| hip_flexion_deg | array | No | 股関節屈曲角度時系列 |
| hip_extension_deg | array | No | 股関節伸展角度時系列 |
| hip_abduction_deg | array | No | 股関節外転角度時系列 |
| hip_rom_deg | number | No | 股関節可動域 |
| knee_flexion_deg | array | No | 膝関節屈曲角度時系列 |
| knee_heel_contact_deg | number | No | ヒールコンタクト時膝関節角度 |
| knee_max_flexion_deg | number | No | 膝関節最大屈曲角度 |
| ankle_dorsiflexion_deg | array | No | 足関節背屈角度時系列 |
| ankle_plantarflexion_deg | array | No | 足関節底屈角度時系列 |
| ankle_toe_off_deg | number | No | トーオフ時足関節角度 |
| pelvic_drop_deg | array | No | 骨盤傾斜角度時系列 |
| pelvic_list_deg | array | No | 骨盤リスト（左右傾き） |
| trunk_rotation_deg | array | No | 体幹回旋角度時系列 |
| frame_timestamps | array | No | フレームタイムスタンプ |

**Example:**

```json
{
  "hip_flexion_deg": [
    0.0
  ],
  "hip_extension_deg": [
    0.0
  ],
  "hip_abduction_deg": [
    0.0
  ],
  "hip_rom_deg": 0.0,
  "knee_flexion_deg": [
    0.0
  ],
  "knee_heel_contact_deg": 0.0,
  "knee_max_flexion_deg": 0.0,
  "ankle_dorsiflexion_deg": [
    0.0
  ],
  "ankle_plantarflexion_deg": [
    0.0
  ],
  "ankle_toe_off_deg": 0.0,
  "pelvic_drop_deg": [
    0.0
  ],
  "pelvic_list_deg": [
    0.0
  ],
  "trunk_rotation_deg": [
    0.0
  ],
  "frame_timestamps": [
    0.0
  ]
}
```


### PasswordReset

パスワードリセットリクエスト

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | メールアドレス |

**Example:**

```json
{
  "email": "string"
}
```


### SpatiotemporalParameters

時空間パラメータ

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| gait_speed_ms | number | Yes | 歩行速度（m/s） |
| cadence_steps_per_min | integer | Yes | ケイデンス（歩/分） |
| stride_length_m | number | Yes | 歩幅（m） |
| stride_time_s | number | Yes | 歩行周期時間（秒） |
| left_step_length_m | number | Yes | 左脚歩幅（m） |
| right_step_length_m | number | Yes | 右脚歩幅（m） |
| left_stance_time_s | number | Yes | 左脚立脚時間（秒） |
| right_stance_time_s | number | Yes | 右脚立脚時間（秒） |
| double_support_time_s | number | Yes | 両脚支持時間（秒） |

**Example:**

```json
{
  "gait_speed_ms": 0.0,
  "cadence_steps_per_min": 0,
  "stride_length_m": 0.0,
  "stride_time_s": 0.0,
  "left_step_length_m": 0.0,
  "right_step_length_m": 0.0,
  "left_stance_time_s": 0.0,
  "right_stance_time_s": 0.0,
  "double_support_time_s": 0.0
}
```


### SymmetryIndices

対称性指標

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| step_length_symmetry_percent | number | Yes | 歩幅対称性（%） |
| stance_time_symmetry_percent | number | Yes | 立脚時間対称性（%） |
| swing_time_symmetry_percent | number | Yes | 遊脚時間対称性（%） |
| hip_flexion_symmetry_percent | number | Yes | 股関節屈曲対称性（%） |
| knee_flexion_symmetry_percent | number | Yes | 膝関節屈曲対称性（%） |
| ankle_dorsiflexion_symmetry_percent | number | Yes | 足関節背屈対称性（%） |
| overall_symmetry_score | number | Yes | 総合対称性スコア（0-100） |

**Example:**

```json
{
  "step_length_symmetry_percent": 0.0,
  "stance_time_symmetry_percent": 0.0,
  "swing_time_symmetry_percent": 0.0,
  "hip_flexion_symmetry_percent": 0.0,
  "knee_flexion_symmetry_percent": 0.0,
  "ankle_dorsiflexion_symmetry_percent": 0.0,
  "overall_symmetry_score": 0.0
}
```


### TokenResponse

トークンレスポンス

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| access_token | string | Yes | アクセストークン |
| token_type | string | No | トークンタイプ |
| expires_in | integer | Yes | 有効期限（秒） |
| user | unknown | Yes | ユーザー情報 |

**Example:**

```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 0,
  "user": "string"
}
```


### UserCreate

ユーザー作成リクエスト

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | メールアドレス |
| password | string | Yes | パスワード |
| full_name | string | Yes | フルネーム |
| height_cm | unknown | No | 身長（cm） |
| weight_kg | unknown | No | 体重（kg） |
| age | unknown | No | 年齢 |
| gender | unknown | No | 性別 |

**Example:**

```json
{
  "email": "string",
  "password": "string",
  "full_name": "string",
  "height_cm": "string",
  "weight_kg": "string",
  "age": "string",
  "gender": "string"
}
```


### UserLogin

ログインリクエスト

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | メールアドレス |
| password | string | Yes | パスワード |

**Example:**

```json
{
  "email": "string",
  "password": "string"
}
```


### UserResponse

ユーザーレスポンス（パスワードなし）

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes |  |
| email | string | Yes |  |
| full_name | string | Yes |  |
| user_type | unknown | Yes |  |
| height_cm | unknown | No |  |
| weight_kg | unknown | No |  |
| age | unknown | No |  |
| gender | unknown | No |  |
| created_at | string | Yes |  |
| updated_at | string | Yes |  |
| last_login | unknown | No |  |
| is_active | boolean | Yes |  |
| is_verified | boolean | Yes |  |
| timezone | string | Yes |  |
| language | string | Yes |  |

**Example:**

```json
{
  "id": "string",
  "email": "string",
  "full_name": "string",
  "user_type": "string",
  "height_cm": "string",
  "weight_kg": "string",
  "age": "string",
  "gender": "string",
  "created_at": "string",
  "updated_at": "string",
  "last_login": "string",
  "is_active": true,
  "is_verified": true,
  "timezone": "string",
  "language": "string"
}
```


### UserStats

ユーザー統計情報

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| total_analyses | integer | Yes | 総分析回数 |
| this_month_analyses | integer | Yes | 今月の分析回数 |
| average_score | number | Yes | 平均スコア |
| latest_analysis_date | unknown | No | 最新分析日時 |
| account_created_days | integer | Yes | アカウント作成からの日数 |
| streak_days | integer | No | 連続使用日数 |

**Example:**

```json
{
  "total_analyses": 0,
  "this_month_analyses": 0,
  "average_score": 0.0,
  "latest_analysis_date": "string",
  "account_created_days": 0,
  "streak_days": 0
}
```


### UserType

ユーザータイプ

**Example:**

```json
"string"
```


### UserUpdate

ユーザー更新リクエスト

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| full_name | unknown | No | フルネーム |
| height_cm | unknown | No | 身長（cm） |
| weight_kg | unknown | No | 体重（kg） |
| age | unknown | No | 年齢 |
| gender | unknown | No | 性別 |
| timezone | unknown | No | タイムゾーン |
| language | unknown | No | 言語設定 |

**Example:**

```json
{
  "full_name": "string",
  "height_cm": "string",
  "weight_kg": "string",
  "age": "string",
  "gender": "string",
  "timezone": "string",
  "language": "string"
}
```


### ValidationError

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| loc | array | Yes |  |
| msg | string | Yes |  |
| type | string | Yes |  |

**Example:**

```json
{
  "loc": [
    "string"
  ],
  "msg": "string",
  "type": "string"
}
```


## Error Codes

| Code | Description |
|------|-------------|
| 200  | OK - Request successful |
| 201  | Created - Resource created successfully |
| 400  | Bad Request - Invalid request parameters |
| 401  | Unauthorized - Authentication required |
| 403  | Forbidden - Insufficient permissions |
| 404  | Not Found - Resource not found |
| 422  | Validation Error - Request validation failed |
| 500  | Internal Server Error - Server error occurred |

## Rate Limiting

- **Standard Users:** 100 requests per minute
- **Professional Users:** 500 requests per minute
- **Admin Users:** Unlimited

## Support

For API support, please contact:
- **Email:** support@gaitanalysis.com
- **Documentation:** [API Reference](https://docs.gaitanalysis.com)
- **Status Page:** [System Status](https://status.gaitanalysis.com)

