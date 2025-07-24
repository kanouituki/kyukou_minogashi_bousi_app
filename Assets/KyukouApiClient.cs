#nullable enable
using System;
using System.Collections;
using UnityEngine;
using UnityEngine.Networking;
using KyukouApp;

/// <summary>
/// KLMS休講情報APIクライアント
/// FastAPIサーバーと通信して休講情報を取得
/// </summary>
public class KyukouApiClient : MonoBehaviour
{
    [Header("API設定")]
    [SerializeField] private string apiBaseUrl = "http://192.168.0.2:8000";
    [SerializeField] private float timeoutSeconds = 30f;
    [SerializeField] private bool useLatestCache = true;

    [Header("デバッグ")]
    [SerializeField] private bool enableDebugLog = true;

    /// <summary>
    /// 休講情報取得完了時のコールバック
    /// </summary>
    public System.Action<KyukouResponse>? OnKyukouReceived;
    
    /// <summary>
    /// API エラー発生時のコールバック
    /// </summary>
    public System.Action<string>? OnApiError;

    /// <summary>
    /// 現在取得中かどうか
    /// </summary>
    public bool IsLoading { get; private set; } = false;

    /// <summary>
    /// 最後に取得した休講情報
    /// </summary>
    public KyukouResponse? LastResponse { get; private set; }

    private void Start()
    {
        // 初期化時にデバッグログ出力
        if (enableDebugLog)
        {
            Debug.Log($"[KyukouApiClient] 初期化完了 - API Base URL: {apiBaseUrl}");
        }
    }

    /// <summary>
    /// 休講情報を取得（メインメソッド）
    /// </summary>
    /// <param name="apiToken">Canvas APIトークン</param>
    /// <param name="forceRefresh">キャッシュを無視して強制更新</param>
    public void GetKyukouInfo(string? apiToken = null, bool forceRefresh = false)
    {
        if (IsLoading)
        {
            if (enableDebugLog)
            {
                Debug.LogWarning("[KyukouApiClient] 既に取得中です");
            }
            return;
        }

        StartCoroutine(GetKyukouInfoCoroutine(apiToken, forceRefresh));
    }

    /// <summary>
    /// 休講情報取得のコルーチン
    /// </summary>
    private IEnumerator GetKyukouInfoCoroutine(string? apiToken, bool forceRefresh)
    {
        IsLoading = true;

        // エンドポイントURLを決定
        string endpoint = useLatestCache && !forceRefresh ? "/api/kyukou/latest" : "/api/kyukou";
        string url = $"{apiBaseUrl}{endpoint}";

        // クエリパラメータ追加
        var queryParams = new System.Collections.Generic.List<string>();
        
        // Canvas APIトークンがある場合は追加
        if (!string.IsNullOrEmpty(apiToken))
        {
            queryParams.Add($"canvas_token={UnityEngine.Networking.UnityWebRequest.EscapeURL(apiToken)}");
        }
        
        if (forceRefresh)
        {
            queryParams.Add("force_refresh=true");
        }

        if (queryParams.Count > 0)
        {
            url += "?" + string.Join("&", queryParams);
        }

        if (enableDebugLog)
        {
            Debug.Log($"[KyukouApiClient] リクエスト開始: {url}");
        }

        // HTTPリクエスト作成
        using (UnityWebRequest request = UnityWebRequest.Get(url))
        {
            // タイムアウト設定
            request.timeout = (int)timeoutSeconds;

            // リクエスト送信
            yield return request.SendWebRequest();

            // レスポンス処理
            if (request.result == UnityWebRequest.Result.Success)
            {
                yield return ProcessSuccessResponse(request.downloadHandler.text);
            }
            else
            {
                yield return ProcessErrorResponse(request);
            }
        }

        // エラーハンドリング（try-catch を使わない）
        IsLoading = false;
    }

    /// <summary>
    /// 成功レスポンスの処理
    /// </summary>
    private IEnumerator ProcessSuccessResponse(string jsonResponse)
    {
        if (enableDebugLog)
        {
            Debug.Log($"[KyukouApiClient] レスポンス受信: {jsonResponse.Substring(0, Mathf.Min(200, jsonResponse.Length))}...");
        }

        // JSONパース
        KyukouResponse response = null;
        string errorMessage = null;

        try
        {
            response = JsonUtility.FromJson<KyukouResponse>(jsonResponse);
            
            if (response == null)
            {
                errorMessage = "JSONのパースに失敗しました";
            }
        }
        catch (Exception e)
        {
            errorMessage = $"レスポンスの解析に失敗しました: {e.Message}";
        }

        if (errorMessage != null)
        {
            if (enableDebugLog)
            {
                Debug.LogError($"[KyukouApiClient] {errorMessage}");
                Debug.LogError($"[KyukouApiClient] 生レスポンス: {jsonResponse}");
            }
            OnApiError?.Invoke(errorMessage);
        }
        else
        {
            // レスポンス保存
            LastResponse = response;

            if (enableDebugLog)
            {
                Debug.Log($"[KyukouApiClient] 休講情報取得完了 - 総コース数: {response.summary.total_courses}, 休講件数: {response.summary.total_cancellations}");
            }

            // コールバック実行
            OnKyukouReceived?.Invoke(response);
        }

        yield return null;
    }

    /// <summary>
    /// エラーレスポンスの処理
    /// </summary>
    private IEnumerator ProcessErrorResponse(UnityWebRequest request)
    {
        string errorMessage;

        switch (request.result)
        {
            case UnityWebRequest.Result.ConnectionError:
                errorMessage = $"サーバーに接続できませんでした: {request.error}";
                break;
            case UnityWebRequest.Result.ProtocolError:
                errorMessage = $"HTTPエラー ({request.responseCode}): {request.error}";
                
                // APIからのエラーレスポンスを解析
                if (!string.IsNullOrEmpty(request.downloadHandler.text))
                {
                    try
                    {
                        ApiError apiError = JsonUtility.FromJson<ApiError>(request.downloadHandler.text);
                        if (!string.IsNullOrEmpty(apiError.detail))
                        {
                            errorMessage += $" - {apiError.detail}";
                        }
                    }
                    catch
                    {
                        // APIエラー解析失敗時は生レスポンスを使用
                        errorMessage += $" - {request.downloadHandler.text}";
                    }
                }
                break;
            case UnityWebRequest.Result.DataProcessingError:
                errorMessage = $"データ処理エラー: {request.error}";
                break;
            default:
                errorMessage = $"不明なエラー: {request.error}";
                break;
        }

        if (enableDebugLog)
        {
            Debug.LogError($"[KyukouApiClient] {errorMessage}");
        }

        OnApiError?.Invoke(errorMessage);
        yield return null;
    }

    /// <summary>
    /// ヘルスチェック（サーバー接続確認用）
    /// </summary>
    public void CheckServerHealth()
    {
        StartCoroutine(CheckServerHealthCoroutine());
    }

    /// <summary>
    /// ヘルスチェックのコルーチン
    /// </summary>
    private IEnumerator CheckServerHealthCoroutine()
    {
        string url = $"{apiBaseUrl}/health";
        
        if (enableDebugLog)
        {
            Debug.Log($"[KyukouApiClient] ヘルスチェック開始: {url}");
        }

        using (UnityWebRequest request = UnityWebRequest.Get(url))
        {
            request.timeout = 10; // ヘルスチェックは短時間で
            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                if (enableDebugLog)
                {
                    Debug.Log($"[KyukouApiClient] サーバー接続正常: {request.downloadHandler.text}");
                }
            }
            else
            {
                if (enableDebugLog)
                {
                    Debug.LogError($"[KyukouApiClient] サーバー接続失敗: {request.error}");
                }
            }
        }
    }

    /// <summary>
    /// API設定の更新
    /// </summary>
    public void UpdateApiSettings(string newBaseUrl, float newTimeout = 30f)
    {
        apiBaseUrl = newBaseUrl;
        timeoutSeconds = newTimeout;
        
        if (enableDebugLog)
        {
            Debug.Log($"[KyukouApiClient] API設定更新 - URL: {apiBaseUrl}, タイムアウト: {timeoutSeconds}s");
        }
    }
}