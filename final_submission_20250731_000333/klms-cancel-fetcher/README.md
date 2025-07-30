# KLMS休講情報取得システム

Canvas LMS（KLMS）から授業のお知らせを自動取得し、GPTで休講情報を判定するシステム。

## 機能

- Canvas APIでコース一覧・お知らせを自動取得
- GPT-4oで休講情報を自動判定
- 新着情報のみを効率的に処理（キャッシュ機能）
- 結果をJSON形式で保存

## セットアップ

### 1. プロジェクトのダウンロード

```bash
git clone [このリポジトリのURL]
cd klms-cancel-fetcher
```

### 2. 依存関係のインストール

Pythonの仮想環境を作成（推奨）：
```bash
python3 -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
```

必要なライブラリをインストール：
```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

プロジェクト直下に`.env`ファイルを作成し、以下を設定：

```env
CANVAS_ACCESS_TOKEN=your_canvas_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

#### Canvas APIトークンの取得方法（詳細）
1. [KLMS](https://lms.keio.jp/)にログイン
2. 右上のプロフィール画像をクリック
3. 「アカウント設定」を選択
4. 左メニューから「承認済みの統合」をクリック
5. 「新しいアクセストークンを生成」ボタンをクリック
6. 用途欄に「休講情報取得アプリ」などと入力
7. 「トークンを生成」をクリック
8. 表示されたトークンをコピー（一度しか表示されません）
9. `.env`ファイルの`CANVAS_ACCESS_TOKEN=`の後に貼り付け

#### OpenAI APIキーの取得方法（詳細）
1. [OpenAI Platform](https://platform.openai.com/)にアクセス
2. アカウント作成・ログイン
3. 右上のプロフィールメニューから「API keys」を選択
4. 「Create new secret key」をクリック
5. 名前を入力（例：KLMS休講チェッカー）
6. 「Create secret key」をクリック
7. 表示されたキーをコピー（一度しか表示されません）
8. `.env`ファイルの`OPENAI_API_KEY=`の後に貼り付け

**注意**: OpenAI APIは有料サービスです。使用量に応じて課金されます。

## 使い方

### 基本的な実行方法

```bash
python3 main.py
```

### 実行時の流れ

1. **キャッシュ読み込み**: 前回の実行結果を読み込み、重複を避ける
2. **コース取得**: KLMSから登録中の全コース一覧を取得
3. **お知らせ取得**: 各コースの新しいお知らせのみを取得
4. **AI分析**: GPTで各お知らせが休講情報かどうかを判定
5. **結果保存**: 休講情報のみを`results/`フォルダにJSON形式で保存

### 実行例

```bash
$ python3 main.py
2025-07-02 22:42:17,270 - __main__ - INFO - KLMS休講情報取得を開始します...
2025-07-02 22:42:17,270 - __main__ - INFO - 前回のキャッシュを読み込み中...
2025-07-02 22:42:17,454 - __main__ - INFO - 取得したコース数: 10
2025-07-02 22:42:17,454 - __main__ - INFO - [1/10] コース: プログラミング入門 (ID: 91628)
...
2025-07-02 22:42:23,846 - __main__ - INFO - 検出した休講情報: 0件
2025-07-02 22:42:23,847 - __main__ - INFO - KLMS休講情報取得を完了しました。
```

### 定期実行の設定

**macOS/Linux (cron):**
```bash
# crontabを編集
crontab -e

# 毎日8時に実行する場合
0 8 * * * cd /path/to/klms-cancel-fetcher && python3 main.py
```

**Windows (タスクスケジューラ):**
1. 「タスクスケジューラ」を開く
2. 「基本タスクの作成」を選択
3. トリガーで実行タイミングを設定
4. 操作で`python3`と`main.py`のパスを設定

## 出力形式

検出された休講情報は`results/`ディレクトリにJSON形式で保存されます：

```json
{
  "summary": {
    "total_courses": 15,
    "total_cancellations": 2,
    "analyzed_at": "2025-07-02T10:30:00"
  },
  "cancellations": [
    {
      "course": "データサイエンス入門",
      "date": "2025-07-05",
      "period": "2限",
      "canceled": true,
      "message": "7月5日(金)2限の授業は休講とします。"
    }
  ]
}
```

## ディレクトリ構成

```
klms-cancel-fetcher/
├── main.py              # メイン実行スクリプト
├── canvas_api.py        # Canvas API通信
├── gpt_analyzer.py      # GPT分析処理
├── cache_manager.py     # キャッシュ管理
├── config.py           # 設定管理
├── requirements.txt    # 依存関係
├── .env               # 環境変数（要作成）
├── data/              # キャッシュファイル
├── results/           # 結果出力
└── logs/             # ログファイル
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. `401 Unauthorized` エラー
```
canvas_api - ERROR - コースの取得中にエラーが発生しました: 401 Client Error: Unauthorized
```

**原因**: Canvas APIトークンが無効または期限切れ
**解決方法**: 
1. KLMSで新しいトークンを生成
2. `.env`ファイルのトークンを更新
3. 古いトークンをKLMSで削除

#### 2. `ModuleNotFoundError` エラー
```
ModuleNotFoundError: No module named 'requests'
```

**原因**: 必要なライブラリがインストールされていない
**解決方法**: 
```bash
pip install -r requirements.txt
```

#### 3. OpenAI API エラー
```
openai.error.RateLimitError: You have exceeded your quota
```

**原因**: OpenAI APIの使用量制限に達した
**解決方法**: 
1. OpenAI Platformで使用量と請求状況を確認
2. クレジットを追加購入
3. 一時的に実行頻度を下げる

#### 4. ファイル権限エラー
```
PermissionError: [Errno 13] Permission denied
```

**原因**: ファイルやディレクトリの書き込み権限がない
**解決方法**: 
```bash
chmod 755 /path/to/klms-cancel-fetcher
chmod 644 /path/to/klms-cancel-fetcher/.env
```

### ログの確認方法

実行時の詳細なログは`logs/klms.log`に保存されます：
```bash
tail -f logs/klms.log  # リアルタイムでログを確認
```

### 初回実行について

- 初回実行時は全てのお知らせを取得・分析するため時間がかかります（5-10分程度）
- 2回目以降は新着のお知らせのみを処理するため高速化されます
- キャッシュファイル（`data/cache.json`）は自動生成されます

## 注意事項

### セキュリティ
- `.env`ファイルは絶対にGitにコミットしないこと
- APIキーは外部に漏らさないよう注意
- 共有PCでは実行後に`.env`ファイルを削除することを推奨

### コスト
- OpenAI APIは有料サービスです（1回の実行で約$0.01-0.05程度）
- 定期実行する場合は月額コストを考慮してください
- GPT-4oの料金は[OpenAI Pricing](https://openai.com/pricing)で確認できます

### 利用規約
- このツールは個人利用目的で作成されています
- KLMSの利用規約に従って使用してください
- 大量のリクエストでサーバーに負荷をかけないよう注意してください