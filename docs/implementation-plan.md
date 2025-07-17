# 休講アラームアプリ実装計画

## 📋 現状把握

### Unity アプリ側 (現在完成済み)
- ✅ **位置情報機能**: GPS取得・保存・距離計算
- ✅ **スマホ対応**: Android設定済み (Bundle ID: jp.ac.keio.sfc.sdp)
- ✅ **基本UI**: 720x1280解像度、タッチ操作対応
- ✅ **GameCanvasフレームワーク**: モバイル向け最適化済み

### サーバー側 (klms-cancel-fetcher)
- ✅ **KLMS連携**: Canvas API でコース・お知らせ取得
- ✅ **AI判定**: GPT-4o で休講情報自動判定
- ✅ **結果保存**: JSON形式で `results/` に出力
- ✅ **キャッシュ機能**: 新着情報のみ効率的に処理
- ❌ **Web API**: HTTPエンドポイント未実装（バッチ処理のみ）

---

## 🎯 実装目標

**メイン機能:**
家を出る → 位置検知 → サーバーから休講情報取得 → 休講があれば通知表示

---

## 📅 実装計画

### Phase 1: サーバーのWeb API化 【優先度: 高】

#### 1.1 FastAPI サーバー構築
```bash
# 新規ファイル作成
klms-cancel-fetcher/
├── api_server.py        # FastAPI サーバーメイン
├── requirements.txt     # fastapi, uvicorn 追加
└── .env                # 既存
```

#### 1.2 APIエンドポイント設計
```
GET /api/kyukou?token=xxx
Response: {
  "summary": {
    "total_cancellations": 2,
    "last_updated": "2025-07-17T10:30:00"
  },
  "cancellations": [
    {
      "course": "プログラミング入門",
      "date": "2025-07-18", 
      "period": "2限",
      "message": "本日は休講です"
    }
  ]
}
```

#### 1.3 デプロイ選択肢
- **開発用**: localhost:8000 (Unity Editor テスト)
- **本番用**: Heroku, Railway, Vercel (スマホアプリ用)

### Phase 2: Unity側 HTTP通信実装 【優先度: 高】

#### 2.1 HTTP クライアント機能
```csharp
// 新規ファイル: Assets/KyukouApiClient.cs
public class KyukouApiClient
{
    public static IEnumerator GetKyukouInfo(string apiToken, System.Action<KyukouResponse> callback)
    {
        using (UnityWebRequest request = UnityWebRequest.Get($"{API_BASE_URL}/api/kyukou?token={apiToken}"))
        {
            yield return request.SendWebRequest();
            // JSON パース & コールバック実行
        }
    }
}
```

#### 2.2 データモデル定義
```csharp
[System.Serializable]
public class KyukouResponse
{
    public Summary summary;
    public Cancellation[] cancellations;
}

[System.Serializable] 
public class Cancellation
{
    public string course;
    public string date;
    public string period;
    public string message;
}
```

### Phase 3: UI拡張 【優先度: 中】

#### 3.1 休講情報表示画面
- 現在の位置情報画面に休講リスト追加
- スクロール可能なリスト表示
- 休講件数の概要表示

#### 3.2 設定画面 (最小構成)
- APIトークン入力欄
- 通知ON/OFF切り替え
- 家の位置登録ボタン

### Phase 4: 統合テスト 【優先度: 中】

#### 4.1 ローカル環境テスト
1. FastAPIサーバーをlocalhost:8000で起動
2. Unity Editor でHTTP通信テスト
3. 実際のKLMS APIを使って休講情報取得確認

#### 4.2 スマホ実機テスト  
1. サーバーをクラウドにデプロイ
2. Unity アプリをAndroidビルド
3. 実機で位置情報 + HTTP通信の動作確認

### Phase 5: 高度な機能 【優先度: 低】

#### 5.1 バックグラウンド監視
- アプリがバックグラウンドでも位置監視
- 家を出たタイミングでの自動チェック

#### 5.2 プッシュ通知
- Firebase Cloud Messaging 連携
- アプリ外でも休講通知受信

---

## 🛠️ 技術選択

### サーバー側
| 機能 | 選択技術 | 理由 |
|------|----------|------|
| Web フレームワーク | FastAPI | 軽量、JSON API に最適 |
| デプロイ | Heroku/Railway | 無料枠あり、Python対応 |
| ドメイン | 動的DNS or ngrok | 開発時は簡易設定 |

### Unity側  
| 機能 | 選択技術 | 理由 |
|------|----------|------|
| HTTP通信 | UnityWebRequest | Unity標準、モバイル対応 |
| JSON解析 | JsonUtility | Unity標準、軽量 |
| UI | GameCanvas | 既存フレームワーク活用 |

---

## ⚠️ 想定される課題

### 技術的課題
1. **CORS問題**: スマホからクラウドサーバーへのHTTPアクセス
2. **認証**: APIトークンの安全な管理
3. **レート制限**: KLMS API の呼び出し頻度制限

### 運用課題  
1. **コスト**: OpenAI API + クラウドサーバー料金
2. **メンテナンス**: KLMS仕様変更への対応
3. **プライバシー**: 位置情報の適切な取り扱い

---

## 📈 段階的リリース計画

### v0.1 (開発版)
- ローカルサーバー + Unity Editor
- 基本的な HTTP通信確認

### v0.2 (テスト版) 
- クラウドサーバー + Android APK
- 実機での動作確認

### v1.0 (正式版)
- 位置情報連動
- 安定した休講情報取得

### v1.1 (拡張版)
- バックグラウンド監視
- プッシュ通知対応

---

## 🎯 次のアクション

**直近 (今日-明日):**
1. FastAPI サーバーの基本実装
2. Unity HTTP通信の基礎コード作成

**短期 (1週間以内):**
1. ローカル環境での動作確認
2. クラウドデプロイとテスト

**中期 (1ヶ月以内):**
1. スマホ実機での完全動作
2. UI/UX の改善