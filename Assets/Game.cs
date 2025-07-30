#nullable enable
using GameCanvas;
using Unity.Mathematics;
using UnityEngine;
using UnityEngine.InputSystem;
using KyukouApp;
using System;

/// <summary>
/// ゲームクラス。
/// 学生が編集すべきソースコードです。
/// </summary>
public sealed class Game : GameBase
{
    // 管理クラス
    private LocationManager? locationManager;
    private SettingsManager? settingsManager;
    private UIManager? uiManager;
    private KyukouNotificationManager? notificationManager;
    
    // 変数の宣言
    string text;

    // 休講情報関連
    KyukouApiClient? kyukouApiClient;
    bool isLoadingKyukou = false;

    /// <summary>
    /// 初期化処理
    /// </summary>
    public override void InitGame()
    {
        gc.SetResolution(720, 1280);
        text = "取得中";

        // 管理クラスの初期化
        InitializeManagers();

        // 休講情報APIクライアントの初期化
        InitializeKyukouApiClient();
    }

    /// <summary>
    /// 管理クラスの初期化
    /// </summary>
    void InitializeManagers()
    {
        // 位置情報管理の初期化
        locationManager = new LocationManager(gc);
        locationManager.OnLocationUpdated += OnLocationUpdated;

        // 設定管理の初期化
        settingsManager = new SettingsManager(gc);

        // UI管理の初期化
        uiManager = new UIManager(gc);
        uiManager.OnRecordButtonClicked += OnRecordButtonClicked;
        uiManager.OnKyukouButtonClicked += OnKyukouButtonClicked;
        uiManager.OnTokenToggleClicked += OnTokenToggleClicked;
        uiManager.OnTokenSaved += OnTokenSaved;
        uiManager.OnCommuteTimeSaved += OnCommuteTimeSaved;

        // 通知管理の初期化
        notificationManager = new KyukouNotificationManager();

        Debug.Log("[Game] 管理クラス初期化完了");
    }

    /// <summary>
    /// 位置情報更新時のコールバック
    /// </summary>
    void OnLocationUpdated(float latitude, float longitude)
    {
        text = $"緯度: {latitude:F6}\n経度: {longitude:F6}";
    }

    /// <summary>
    /// 位置記録ボタンクリック時のコールバック
    /// </summary>
    void OnRecordButtonClicked()
    {
        if (locationManager != null)
        {
            locationManager.RecordCurrentLocation();
            text = $"位置を記録しました ({locationManager.CurrentLatitude:F4}, {locationManager.CurrentLongitude:F4})";
        }
    }

    /// <summary>
    /// 休講情報取得ボタンクリック時のコールバック
    /// </summary>
    void OnKyukouButtonClicked()
    {
        if (kyukouApiClient != null && !isLoadingKyukou)
        {
            isLoadingKyukou = true;
            string? tokenToUse = settingsManager?.HasCanvasApiToken == true ? settingsManager.CanvasApiToken : null;
            kyukouApiClient.GetKyukouInfo(tokenToUse);
            Debug.Log($"休講情報取得開始 (トークン: {(tokenToUse != null ? "あり" : "なし")})");
        }
    }

    /// <summary>
    /// APIトークン設定ボタンクリック時のコールバック
    /// </summary>
    void OnTokenToggleClicked()
    {
        if (uiManager != null)
        {
            uiManager.ShowTokenInput = !uiManager.ShowTokenInput;
        }
    }

    /// <summary>
    /// APIトークン保存時のコールバック
    /// </summary>
    void OnTokenSaved(string token)
    {
        settingsManager?.SaveCanvasApiToken(token);
    }

    /// <summary>
    /// 通学時間保存時のコールバック
    /// </summary>
    void OnCommuteTimeSaved(int minutes)
    {
        settingsManager?.SaveCommuteTime(minutes);
    }

    /// <summary>
    /// 休講情報APIクライアントの初期化
    /// </summary>
    void InitializeKyukouApiClient()
    {
        // KyukouApiClientコンポーネントを追加
        kyukouApiClient = gameObject.AddComponent<KyukouApiClient>();

        // コールバック設定
        kyukouApiClient.OnKyukouReceived += OnKyukouInfoReceived;
        kyukouApiClient.OnApiError += OnKyukouApiError;

        Debug.Log("KyukouApiClient 初期化完了");
    }

    /// <summary>
    /// 動きなどの更新処理
    /// </summary>
    public override void UpdateGame()
    {
        // 位置情報管理の更新
        if (locationManager != null)
        {
            locationManager.StartLocationService();
            locationManager.UpdateLocation();
            
            if (!locationManager.HasLocationPermission)
            {
                text = "位置情報サービスが無効です";
            }
        }

        // UI入力処理
        uiManager?.HandleInput();

        // 通知チェック
        notificationManager?.CheckNotification(locationManager, settingsManager);
    }

    /// <summary>
    /// 描画の処理
    /// </summary>
    public override void DrawGame()
    {
        if (uiManager != null)
        {
            string kyukouText = notificationManager?.GetKyukouSummaryText() ?? "休講情報: 未取得";
            string canvasTokenStatus = settingsManager?.GetMaskedToken() ?? "未設定";
            string kyukouNotification = notificationManager?.CurrentNotification ?? "";
            
            uiManager.DrawMainScreen(text, locationManager, kyukouText, 
                                   notificationManager?.LastResponse, canvasTokenStatus, kyukouNotification);
        }
    }

    /// <summary>
    /// 休講情報取得成功時のコールバック
    /// </summary>
    void OnKyukouInfoReceived(KyukouResponse response)
    {
        isLoadingKyukou = false;
        notificationManager?.UpdateKyukouInfo(response);
        Debug.Log($"休講情報取得完了: {response.summary.total_cancellations}件");
    }

    /// <summary>
    /// 休講情報取得失敗時のコールバック
    /// </summary>
    void OnKyukouApiError(string errorMessage)
    {
        isLoadingKyukou = false;
        notificationManager?.SetError(errorMessage);
        Debug.LogError($"休講情報取得エラー: {errorMessage}");
    }
}