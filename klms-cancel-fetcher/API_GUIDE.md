# KLMS休講情報API 使用ガイド

## 概要

KLMS休講見逃し防止アプリのAPIは、Canvas LMSから自動的に休講情報を収集・分析し、構造化されたデータとして提供します。

## ベースURL

```
https://api.klms-cancel-checker.com  # 本番環境
http://localhost:8000               # 開発環境
```

## 認証

### Canvas APIトークンの取得

1. [Canvas LMS](https://keio.instructure.com)にログイン
2. Account → Settings → Approved Integrations
3. "New Access Token"をクリック
4. 用途を入力して"Generate Token"
5. 表示されたトークンをコピー（一度しか表示されません）

## エンドポイント

### 1. 休講情報取得

最新の休講情報を取得します。

```http
GET /api/kyukou
```

#### パラメータ

| パラメータ | 型 | 必須 | 説明 |
|-----------|---|------|------|
| canvas_token | string | No | Canvas APIトークン |
| force_refresh | boolean | No | キャッシュを無視して強制更新 (default: false) |

#### レスポンス例

```json
{
  "summary": {
    "total_courses": 5,
    "total_cancellations": 2,
    "analyzed_at": "2023-12-01T10:30:00",
    "api_version": "1.0.0",
    "processing_time_seconds": 2.45
  },
  "cancellations": [
    {
      "course_id": 12345,
      "course_name": "プログラミング基礎",
      "announcement_id": 67890,
      "announcement_title": "12月1日 休講のお知らせ",
      "analyzed_at": "2023-12-01T10:30:00",
      "canceled": true,
      "course": "プログラミング基礎",
      "date": "2023-12-01",
      "period": "2限",
      "message": "講師の都合により休講いたします",
      "reason": "講師都合",
      "confidence": 0.95
    }
  ]
}
```

### 2. 最新結果取得（高速版）

キャッシュファイルから最新の結果を高速で取得します。

```http
GET /api/kyukou/latest
```

#### パラメータ

| パラメータ | 型 | 必須 | 説明 |
|-----------|---|------|------|
| canvas_token | string | No | Canvas APIトークン（現在未使用） |

### 3. ヘルスチェック

システムの健全性を確認します。

```http
GET /health
```

#### レスポンス例

```json
{
  "status": "healthy",
  "timestamp": "2023-12-01T10:30:00",
  "uptime_seconds": 86400,
  "checks": {
    "database": {"healthy": true},
    "external_apis": {"healthy": true},
    "memory": {"healthy": true}
  }
}
```

### 4. メトリクス取得

システムのパフォーマンスメトリクスを取得します。

```http
GET /metrics
```

#### レスポンス例

```json
{
  "timestamp": "2023-12-01T10:30:00",
  "system": {
    "cpu_percent": 25.5,
    "memory_percent": 68.2,
    "disk_percent": 42.1
  },
  "application": {
    "total_requests": 1250,
    "successful_requests": 1180,
    "failed_requests": 70,
    "avg_response_time_ms": 485.2,
    "cache_hit_rate": 78.5
  }
}
```

## エラーハンドリング

### HTTPステータスコード

| コード | 説明 |
|--------|------|
| 200 | 成功 |
| 400 | リクエストエラー（無効なパラメータなど） |
| 401 | 認証エラー（無効なAPIトークン） |
| 429 | レート制限超過 |
| 500 | サーバーエラー |

### エラーレスポンス形式

```json
{
  "error": "エラーメッセージ",
  "error_code": "ERROR_CODE",
  "details": {
    "additional": "info"
  },
  "timestamp": "2023-12-01T10:30:00"
}
```

## レート制限

- **制限**: 30リクエスト/分
- **制限超過時**: HTTP 429 Too Many Requests
- **ヘッダー**: `Retry-After` で再試行までの秒数を返却

## SDKとサンプルコード

### Python

```python
import requests
from typing import Optional, Dict, Any

class KlmsApiClient:
    def __init__(self, base_url: str = "https://api.klms-cancel-checker.com"):
        self.base_url = base_url
    
    def get_kyukou_info(self, canvas_token: Optional[str] = None, 
                       force_refresh: bool = False) -> Dict[str, Any]:
        """休講情報を取得"""
        params = {}
        if canvas_token:
            params['canvas_token'] = canvas_token
        if force_refresh:
            params['force_refresh'] = 'true'
        
        response = requests.get(f"{self.base_url}/api/kyukou", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_latest_results(self) -> Dict[str, Any]:
        """最新結果を高速取得"""
        response = requests.get(f"{self.base_url}/api/kyukou/latest")
        response.raise_for_status()
        return response.json()
    
    def check_health(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

# 使用例
if __name__ == "__main__":
    client = KlmsApiClient()
    
    try:
        # 休講情報取得
        result = client.get_kyukou_info(
            canvas_token="your_canvas_token_here",
            force_refresh=False
        )
        
        print(f"総コース数: {result['summary']['total_courses']}")
        print(f"休講件数: {result['summary']['total_cancellations']}")
        
        for cancellation in result['cancellations']:
            print(f"休講: {cancellation['course_name']} - {cancellation['date']} {cancellation['period']}")
            
    except requests.exceptions.HTTPError as e:
        print(f"APIエラー: {e}")
    except Exception as e:
        print(f"エラー: {e}")
```

### JavaScript/TypeScript

```typescript
interface KyukouSummary {
  total_courses: number;
  total_cancellations: number;
  analyzed_at: string;
  api_version: string;
}

interface Cancellation {
  course_id: number;
  course_name: string;
  date: string;
  period: string;
  canceled: boolean;
  confidence: number;
  message?: string;
  reason?: string;
}

interface KyukouResponse {
  summary: KyukouSummary;
  cancellations: Cancellation[];
}

class KlmsApiClient {
  private baseUrl: string;
  
  constructor(baseUrl = "https://api.klms-cancel-checker.com") {
    this.baseUrl = baseUrl;
  }
  
  async getKyukouInfo(canvasToken?: string, forceRefresh = false): Promise<KyukouResponse> {
    const params = new URLSearchParams();
    if (canvasToken) params.append('canvas_token', canvasToken);
    if (forceRefresh) params.append('force_refresh', 'true');
    
    const response = await fetch(`${this.baseUrl}/api/kyukou?${params}`);
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  }
  
  async getLatestResults(): Promise<KyukouResponse> {
    const response = await fetch(`${this.baseUrl}/api/kyukou/latest`);
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  }
}

// 使用例
const client = new KlmsApiClient();

client.getKyukouInfo('your_canvas_token_here')
  .then(result => {
    console.log(`総コース数: ${result.summary.total_courses}`);
    console.log(`休講件数: ${result.summary.total_cancellations}`);
    
    result.cancellations.forEach(cancellation => {
      console.log(`休講: ${cancellation.course_name} - ${cancellation.date} ${cancellation.period}`);
    });
  })
  .catch(error => console.error('エラー:', error));
```

### Unity C#

```csharp
using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

[Serializable]
public class KyukouSummary
{
    public int total_courses;
    public int total_cancellations;
    public string analyzed_at;
    public string api_version;
}

[Serializable]
public class Cancellation
{
    public int course_id;
    public string course_name;
    public string date;
    public string period;
    public bool canceled;
    public float confidence;
    public string message;
    public string reason;
}

[Serializable]
public class KyukouResponse
{
    public KyukouSummary summary;
    public Cancellation[] cancellations;
}

public class KlmsApiClient : MonoBehaviour
{
    private const string BASE_URL = "https://api.klms-cancel-checker.com";
    
    public IEnumerator GetKyukouInfo(string canvasToken, bool forceRefresh, 
                                   System.Action<KyukouResponse> onSuccess, 
                                   System.Action<string> onError)
    {
        string url = $"{BASE_URL}/api/kyukou";
        
        // パラメータ構築
        List<string> parameters = new List<string>();
        if (!string.IsNullOrEmpty(canvasToken))
            parameters.Add($"canvas_token={UnityWebRequest.EscapeURL(canvasToken)}");
        if (forceRefresh)
            parameters.Add("force_refresh=true");
        
        if (parameters.Count > 0)
            url += "?" + string.Join("&", parameters);
        
        using (UnityWebRequest request = UnityWebRequest.Get(url))
        {
            request.timeout = 30;
            yield return request.SendWebRequest();
            
            if (request.result == UnityWebRequest.Result.Success)
            {
                try
                {
                    string jsonResponse = request.downloadHandler.text;
                    KyukouResponse response = JsonUtility.FromJson<KyukouResponse>(jsonResponse);
                    onSuccess?.Invoke(response);
                }
                catch (Exception e)
                {
                    onError?.Invoke($"JSON parse error: {e.Message}");
                }
            }
            else
            {
                onError?.Invoke($"Request failed: {request.error}");
            }
        }
    }
    
    // 使用例
    void Start()
    {
        StartCoroutine(GetKyukouInfo(
            "your_canvas_token_here",
            false,
            OnKyukouSuccess,
            OnKyukouError
        ));
    }
    
    void OnKyukouSuccess(KyukouResponse response)
    {
        Debug.Log($"総コース数: {response.summary.total_courses}");
        Debug.Log($"休講件数: {response.summary.total_cancellations}");
        
        foreach (var cancellation in response.cancellations)
        {
            Debug.Log($"休講: {cancellation.course_name} - {cancellation.date} {cancellation.period}");
        }
    }
    
    void OnKyukouError(string error)
    {
        Debug.LogError($"API Error: {error}");
    }
}
```

## ベストプラクティス

### 1. キャッシュの活用

- 同じデータを短時間で複数回取得する場合は`force_refresh=false`を使用
- 最新データが不要な場合は`/api/kyukou/latest`エンドポイントを使用

### 2. エラーハンドリング

```python
import time
import requests
from requests.exceptions import RequestException

def get_kyukou_with_retry(client, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.get_kyukou_info()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limit
                retry_after = int(e.response.headers.get('Retry-After', 60))
                print(f"Rate limited. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
            elif attempt == max_retries - 1:
                raise
        except RequestException as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

### 3. パフォーマンス最適化

- 大量のリクエストを送信する場合は、適切な間隔を空ける
- 不要な`force_refresh`の使用を避ける
- APIレスポンスのキャッシュを検討する

## トラブルシューティング

### よくある問題

1. **401 Unauthorized**
   - Canvas APIトークンが無効または期限切れ
   - トークンを再生成してください

2. **429 Too Many Requests**
   - レート制限に達しました
   - `Retry-After`ヘッダーの値を確認して待機

3. **500 Internal Server Error**
   - サーバー側の問題
   - `/health`エンドポイントでシステム状態を確認

### デバッグ情報

システムの詳細情報が必要な場合：

```bash
curl -X GET "https://api.klms-cancel-checker.com/metrics" \
     -H "accept: application/json"
```

## サポート

- **API仕様書**: https://api.klms-cancel-checker.com/docs
- **GitHub Issues**: https://github.com/your-org/klms-cancel-fetcher/issues
- **メール**: support@klms-cancel-checker.com

## 変更履歴

### v1.0.0 (2023-12-01)
- 初回リリース
- 基本的な休講情報取得機能
- キャッシュ機能
- レート制限実装