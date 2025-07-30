# 休講見逃し防止アプリ

SFC学生向けの休講情報自動取得・通知アプリです。位置情報を利用してSFCキャンパス内にいる際に休講情報を自動通知します。

## 概要

本アプリは以下の機能を提供します：
- **位置情報記録・距離測定**: ユーザーの位置を記録し、現在地からの距離を測定
- **Canvas APIトークン入力**: ユーザー個人のCanvas APIトークンを安全に保存
- **休講情報自動取得**: KLMSから最新の休講情報を取得・表示
- **GPT分析**: お知らせを自動分析して休講情報を判定

## システム構成

### クライアント側（Unity）
- **フレームワーク**: GameCanvas
- **言語**: C#
- **プラットフォーム**: Android/iOS対応
- **主要機能**:
  - 位置情報サービス
  - Canvas APIトークン入力UI
  - 休講情報表示
  - HTTPクライアント通信

### サーバー側（Python）
- **フレームワーク**: FastAPI
- **言語**: Python 3.11+
- **デプロイ**: SFC CCX03サーバー (133.27.4.213)
- **主要機能**:
  - Canvas LMS API連携
  - GPT-4による自然言語解析
  - 休講情報キャッシュ機能
  - REST APIエンドポイント

## 使用方法

### 1. 環境構築

#### Unity側
```bash
# Unity 2022.3.24f1以降をインストール
# Android/iOSモジュールを含めてインストール
```

#### サーバー側
```bash
cd klms-cancel-fetcher
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. 環境設定

#### サーバー側設定
```bash
# .envファイルを作成
cp .env.example .env

# 以下の設定を入力
OPENAI_API_KEY=your_openai_api_key_here
CANVAS_BASE_URL=https://keio.instructure.com
```

### 3. 実行

#### サーバー起動
```bash
# 開発環境（localhost）
python api_server.py

# 本番環境（CCX03）
# SSH接続後、仮想環境内で実行
python api_server.py
```

#### Unity実行
1. UnityHubでプロジェクトを開く
2. Gameシーンを開く
3. 再生ボタンを押す

### 4. アプリ操作

1. **位置記録**: 「位置記録」ボタンで現在地を保存
2. **API設定**: 「API設定」ボタンでCanvas APIトークンを入力
3. **休講情報取得**: 「休講情報」ボタンで最新の休講情報を取得

## API仕様

### エンドポイント

#### GET `/api/kyukou`
休講情報を取得
- **パラメータ**:
  - `canvas_token` (optional): Canvas APIトークン
  - `force_refresh` (optional): キャッシュを無視して最新情報を取得
- **レスポンス**:
```json
{
  "summary": {
    "total_courses": 15,
    "total_cancellations": 2,
    "analyzed_at": "2024-01-15T10:30:00",
    "api_version": "1.0.0"
  },
  "cancellations": [
    {
      "course": "プログラミング基礎",
      "date": "2024-01-15",
      "period": "2限",
      "reason": "講師の都合により"
    }
  ]
}
```

#### GET `/health`
ヘルスチェック

## 開発状況

### 完了済み機能
- ✅ 位置情報取得・記録機能
- ✅ Canvas APIトークン入力UI
- ✅ 休講情報API設計・実装
- ✅ Unity-サーバー間HTTP通信
- ✅ GPT分析によるお知らせ解析
- ✅ 基本的なUI実装

### 進行中
- 🔄 CCX03サーバーでのデプロイ
- 🔄 エンドツーエンドテスト

### 今後の予定
- 📋 プッシュ通知機能
- 📋 位置情報による自動通知
- 📋 UI/UXの改善
- 📋 エラーハンドリング強化
- 📋 セキュリティ強化
- 📋 パフォーマンス最適化

## 技術仕様

### 開発環境
- **Unity**: 2022.3.24f1以降
- **Python**: 3.11+
- **サーバー**: SFC CCX03 (133.27.4.213)

### 依存関係
#### Unity
- GameCanvas Framework
- UnityWebRequest
- Unity Input System

#### Python
- FastAPI
- OpenAI API
- Requests
- Uvicorn

### セキュリティ
- APIトークンのマスク表示
- HTTPS通信（本番環境）
- 環境変数による秘密情報管理
- CORS設定

## 貢献

このプロジェクトは教育目的で作成されています。バグ報告や機能提案はIssuesでお願いします。

## ライセンス

MIT License. 詳細は[LICENSE](LICENSE)を参照してください。
