"""
OpenAPI仕様書定義
FastAPIでの自動生成とカスタマイズ
"""

from typing import Dict, Any, List
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from models import (
    KyukouApiResponse, 
    ApiError, 
    HealthCheckResponse,
    CanvasTokenRequest
)


def custom_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """
    カスタムOpenAPI仕様書を生成
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    # 基本的なOpenAPI仕様を生成
    openapi_schema = get_openapi(
        title="KLMS休講情報API",
        version="1.0.0",
        description="""
## KLMS休講見逃し防止アプリ API

Canvas LMSとOpenAI GPTを活用して休講情報を自動収集・分析するAPIです。

### 主な機能

- **休講情報取得**: Canvas LMSから最新のお知らせを取得し、GPTで休講情報を分析
- **キャッシュ機能**: 効率的な情報取得のためのインメモリ・ファイルキャッシュ
- **パフォーマンス最適化**: 並列処理による高速な情報処理
- **監視・メトリクス**: システムの健全性とパフォーマンスの監視

### 認証

Canvas APIトークンが必要です。トークンは以下の方法で取得できます：

1. Canvas LMSにログイン
2. Account > Settings > Approved Integrations
3. New Access Token を作成

### レート制限

- **制限**: 30リクエスト/分
- **制限超過時**: HTTP 429 Too Many Requests

### エラーハンドリング

APIは以下のHTTPステータスコードを返します：

- `200`: 成功
- `400`: リクエストエラー（無効なパラメータなど）
- `401`: 認証エラー（無効なAPIトークン）
- `429`: レート制限超過
- `500`: サーバーエラー

## サンプルコード

### Python

```python
import requests

# 休講情報を取得
response = requests.get(
    'https://api.example.com/api/kyukou',
    params={
        'canvas_token': 'your_canvas_token_here',
        'force_refresh': False
    }
)

if response.status_code == 200:
    data = response.json()
    cancellations = data['cancellations']
    for cancellation in cancellations:
        print(f"休講: {cancellation['course_name']} - {cancellation['date']}")
else:
    print(f"エラー: {response.status_code}")
```

### JavaScript

```javascript
const apiUrl = 'https://api.example.com/api/kyukou';
const params = new URLSearchParams({
    canvas_token: 'your_canvas_token_here',
    force_refresh: 'false'
});

fetch(`${apiUrl}?${params}`)
    .then(response => response.json())
    .then(data => {
        data.cancellations.forEach(cancellation => {
            console.log(`休講: ${cancellation.course_name} - ${cancellation.date}`);
        });
    })
    .catch(error => console.error('Error:', error));
```

### Unity C#

```csharp
using UnityEngine;
using UnityEngine.Networking;
using System.Collections;

public class KyukouApiClient : MonoBehaviour
{
    private const string API_URL = "https://api.example.com/api/kyukou";
    
    public IEnumerator GetKyukouInfo(string canvasToken)
    {
        string url = $"{API_URL}?canvas_token={canvasToken}&force_refresh=false";
        
        using (UnityWebRequest request = UnityWebRequest.Get(url))
        {
            yield return request.SendWebRequest();
            
            if (request.result == UnityWebRequest.Result.Success)
            {
                string jsonResponse = request.downloadHandler.text;
                // JSONをパースして休講情報を処理
                Debug.Log($"休講情報: {jsonResponse}");
            }
            else
            {
                Debug.LogError($"API Error: {request.error}");
            }
        }
    }
}
```
        """,
        routes=app.routes,
    )
    
    # サーバー情報を追加
    openapi_schema["servers"] = [
        {
            "url": "https://api.klms-cancel-checker.com",
            "description": "本番環境"
        },
        {
            "url": "https://staging-api.klms-cancel-checker.com", 
            "description": "ステージング環境"
        },
        {
            "url": "http://localhost:8000",
            "description": "開発環境"
        }
    ]
    
    # タグを追加
    openapi_schema["tags"] = [
        {
            "name": "kyukou",
            "description": "休講情報関連のエンドポイント"
        },
        {
            "name": "monitoring",
            "description": "監視・ヘルスチェック関連のエンドポイント"
        },
        {
            "name": "cache",
            "description": "キャッシュ管理関連のエンドポイント"
        }
    ]
    
    # セキュリティスキームを追加
    openapi_schema["components"]["securitySchemes"] = {
        "CanvasToken": {
            "type": "apiKey",
            "in": "query",
            "name": "canvas_token",
            "description": "Canvas LMS APIトークン"
        }
    }
    
    # レスポンス例を追加
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    if "examples" not in openapi_schema["components"]:
        openapi_schema["components"]["examples"] = {}
    
    # 成功レスポンス例
    openapi_schema["components"]["examples"]["KyukouSuccessResponse"] = {
        "summary": "休講情報取得成功",
        "description": "休講情報が正常に取得された場合のレスポンス例",
        "value": {
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
                    "canceled": True,
                    "course": "プログラミング基礎",
                    "date": "2023-12-01",
                    "period": "2限",
                    "message": "講師の都合により休講いたします",
                    "reason": "講師都合",
                    "confidence": 0.95
                }
            ]
        }
    }
    
    # エラーレスポンス例
    openapi_schema["components"]["examples"]["ApiErrorResponse"] = {
        "summary": "APIエラー",
        "description": "APIエラーが発生した場合のレスポンス例",
        "value": {
            "error": "APIトークンが無効です",
            "error_code": "INVALID_TOKEN",
            "details": {
                "token_length": 25,
                "expected_min_length": 32
            },
            "timestamp": "2023-12-01T10:30:00"
        }
    }
    
    # レート制限エラー例
    openapi_schema["components"]["examples"]["RateLimitResponse"] = {
        "summary": "レート制限エラー",
        "description": "レート制限に達した場合のレスポンス例",
        "value": {
            "error": "レート制限に達しました。45秒後に再試行してください",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "details": {
                "retry_after_seconds": 45,
                "limit_per_window": 30,
                "window_minutes": 1
            },
            "timestamp": "2023-12-01T10:30:00"
        }
    }
    
    # ヘルスチェック例
    openapi_schema["components"]["examples"]["HealthResponse"] = {
        "summary": "ヘルスチェック正常",
        "description": "システムが正常な場合のヘルスチェックレスポンス",
        "value": {
            "status": "healthy",
            "timestamp": "2023-12-01T10:30:00",
            "uptime_seconds": 86400,
            "checks": {
                "database": {
                    "healthy": True,
                    "cache_stats": {
                        "api_response_cache": {
                            "total_entries": 10,
                            "active_entries": 8,
                            "expired_entries": 2
                        }
                    }
                },
                "external_apis": {
                    "healthy": True,
                    "canvas_api": {"healthy": True},
                    "openai_api": {"healthy": True}
                },
                "memory": {
                    "healthy": True,
                    "system_memory_percent": 65.2,
                    "process_memory_mb": 128.5
                }
            }
        }
    }
    
    app.openapi_schema = openapi_schema
    return openapi_schema


def add_api_documentation_routes(app: FastAPI):
    """
    API仕様書関連のルートを追加
    """
    
    @app.get("/openapi.json", include_in_schema=False)
    async def get_openapi_json():
        """OpenAPI仕様書をJSON形式で取得"""
        return custom_openapi_schema(app)
    
    @app.get("/docs", include_in_schema=False)
    async def get_swagger_ui():
        """Swagger UIを表示"""
        from fastapi.responses import HTMLResponse
        from fastapi.openapi.docs import get_swagger_ui_html
        
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="KLMS休講情報API - Swagger UI",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        )
    
    @app.get("/redoc", include_in_schema=False)
    async def get_redoc():
        """ReDocを表示"""
        from fastapi.responses import HTMLResponse
        from fastapi.openapi.docs import get_redoc_html
        
        return get_redoc_html(
            openapi_url="/openapi.json",
            title="KLMS休講情報API - ReDoc",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js",
        )


# カスタムレスポンスモデル定義
API_RESPONSES = {
    200: {
        "description": "成功",
        "model": KyukouApiResponse,
        "content": {
            "application/json": {
                "examples": {
                    "success": {
                        "summary": "休講情報取得成功",
                        "value": {
                            "summary": {
                                "total_courses": 5,
                                "total_cancellations": 2,
                                "analyzed_at": "2023-12-01T10:30:00",
                                "api_version": "1.0.0"
                            },
                            "cancellations": [
                                {
                                    "course_name": "プログラミング基礎",
                                    "date": "2023-12-01",
                                    "period": "2限",
                                    "canceled": True,
                                    "confidence": 0.95
                                }
                            ]
                        }
                    }
                }
            }
        }
    },
    400: {
        "description": "リクエストエラー",
        "model": ApiError,
        "content": {
            "application/json": {
                "examples": {
                    "invalid_token": {
                        "summary": "無効なAPIトークン",
                        "value": {
                            "error": "APIトークンが無効です",
                            "error_code": "INVALID_TOKEN"
                        }
                    }
                }
            }
        }
    },
    429: {
        "description": "レート制限超過",
        "model": ApiError,
        "content": {
            "application/json": {
                "examples": {
                    "rate_limit": {
                        "summary": "レート制限超過",
                        "value": {
                            "error": "レート制限に達しました",
                            "error_code": "RATE_LIMIT_EXCEEDED"
                        }
                    }
                }
            }
        }
    },
    500: {
        "description": "サーバーエラー",
        "model": ApiError
    }
}

HEALTH_RESPONSES = {
    200: {
        "description": "ヘルスチェック結果",
        "model": HealthCheckResponse,
        "content": {
            "application/json": {
                "examples": {
                    "healthy": {
                        "summary": "システム正常",
                        "value": {
                            "status": "healthy",
                            "timestamp": "2023-12-01T10:30:00"
                        }
                    },
                    "unhealthy": {
                        "summary": "システム異常",
                        "value": {
                            "status": "unhealthy",
                            "timestamp": "2023-12-01T10:30:00"
                        }
                    }
                }
            }
        }
    }
}