#nullable enable
using GameCanvas;
using Unity.Mathematics;
using UnityEngine;
using UnityEngine.InputSystem;
using KyukouApp;

/// <summary>
/// ゲームクラス。
/// 学生が編集すべきソースコードです。
/// </summary>
public sealed class Game : GameBase
{
    // 変数の宣言
    float lat;
    float lng;
    float recorded_lat;
    float recorded_lng;
    float distance;
    string text;
    bool isStartGPS = false;

    // 休講情報関連
    KyukouApiClient? kyukouApiClient;
    KyukouResponse? lastKyukouResponse;
    string kyukouText = "休講情報: 未取得";
    bool isLoadingKyukou = false;

    GcRect record_button = new GcRect(50, 450, 200, 60);
    GcRect kyukou_button = new GcRect(300, 450, 200, 60);

    /// <summary>
    /// 初期化処理
    /// </summary>
    public override void InitGame()
    {
        gc.SetResolution(720, 1280);
        lat = 35.685410f;
        lng = 139.752842f;
        text = "取得中";

        // 休講情報APIクライアントの初期化
        InitializeKyukouApiClient();
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
        if (!isStartGPS)
        {
            gc.StartGeolocationService();
            isStartGPS = true;
        }

        if (!gc.HasGeolocationPermission)
        {
            text = "位置情報サービスが無効です";
        }

        if (gc.HasGeolocationUpdate)
        {
            lat = gc.GeolocationLastLatitude;
            lng = gc.GeolocationLastLongitude;
            text = string.Format("緯度: {0}\n経度: {1}", lat, lng);
        }

        if (touch_object(record_button))
        {
            text = "recorded";

            if (gc.HasGeolocationUpdate)
            {
                gc.Save("recorded_lat", gc.GeolocationLastLatitude);
                gc.Save("recorded_lng", gc.GeolocationLastLongitude);
            }
            gc.TryLoad("recorded_lat", out recorded_lat);
            gc.TryLoad("recorded_lng", out recorded_lng);
        }

        // 休講情報取得ボタン（タップ時のみ実行）
        if (touch_object(kyukou_button))
        {
            Debug.Log("休講情報ボタンがタッチされました");
            if (gc.GetPointerFrameCount(0) == 1)
            {
                Debug.Log("フレームカウント条件OK");
                if (kyukouApiClient != null && !isLoadingKyukou)
                {
                    kyukouText = "休講情報: 取得中...";
                    isLoadingKyukou = true;
                    kyukouApiClient.GetKyukouInfo();
                    Debug.Log("休講情報取得開始");
                }
                else
                {
                    Debug.Log($"API呼び出し失敗: kyukouApiClient={kyukouApiClient}, isLoadingKyukou={isLoadingKyukou}");
                }
            }
        }

        distance = CalculateDistance(recorded_lat, recorded_lng, gc.GeolocationLastLatitude, gc.GeolocationLastLongitude);
    }

    /// <summary>
    /// 描画の処理
    /// </summary>
    public override void DrawGame()
    {
        gc.ClearScreen();
        gc.SetColor(0, 0, 0);
        gc.DrawString(text, 0, 0);

        // 位置記録ボタン
        gc.SetColor(100, 100, 100);
        gc.FillRect(record_button);
        gc.SetColor(255, 255, 255);
        gc.DrawString("位置記録", record_button.Position.x + 10, record_button.Position.y + 30);

        // 休講情報取得ボタン（強制表示）
        gc.SetColor(200, 100, 100);  // 赤色で強制表示
        gc.FillRect(kyukou_button);
        gc.SetColor(255, 255, 255);
        gc.DrawString("休講情報", kyukou_button.Position.x + 10, kyukou_button.Position.y + 30);
        
        // デバッグ用: ボタンの座標を表示
        gc.SetColor(0, 0, 0);
        gc.DrawString($"ボタン位置: X={kyukou_button.Position.x}, Y={kyukou_button.Position.y}", 0, 520);
        
        // デバッグ用: マウス座標を表示
        float mouseX = gc.GetPointerX(0);
        float mouseY = gc.GetPointerY(0);
        gc.DrawString($"マウス位置: X={mouseX}, Y={mouseY}", 0, 550);

        // 位置情報表示
        gc.SetColor(0, 0, 0);
        gc.DrawString("記録された緯度:" + recorded_lat.ToString(), 0, 180);
        gc.DrawString("記録された経度:" + recorded_lng.ToString(), 0, 210);
        gc.DrawString("現在地までの距離：" + distance.ToString("F1") + "m", 0, 240);

        // 休講情報表示
        gc.DrawString(kyukouText, 0, 280);
        
        // 休講詳細表示
        if (lastKyukouResponse != null && lastKyukouResponse.cancellations.Length > 0)
        {
            int yOffset = 320;
            gc.DrawString("=== 休講一覧 ===", 0, yOffset);
            yOffset += 30;

            for (int i = 0; i < lastKyukouResponse.cancellations.Length && i < 5; i++) // 最大5件表示
            {
                var cancel = lastKyukouResponse.cancellations[i];
                gc.DrawString($"{cancel.course}", 0, yOffset);
                gc.DrawString($"{cancel.date} {cancel.period}", 0, yOffset + 20);
                yOffset += 50;
            }

            if (lastKyukouResponse.cancellations.Length > 5)
            {
                gc.DrawString($"...他{lastKyukouResponse.cancellations.Length - 5}件", 0, yOffset);
            }
        }
    }


    public bool touch_object(GcRect rect)
    {
        float px = gc.GetPointerX(0);
        float py = gc.GetPointerY(0);

        return (rect.Position.x < px && px < rect.Position.x + rect.Size.x) && (rect.Position.y < py && py < rect.Position.y + rect.Size.y);
    }
    
    float CalculateDistance(float lat1, float lon1, float lat2, float lon2)
    {
        const float R = 6371000f; // 地球の半径（メートル）

        float radLat1 = Mathf.Deg2Rad * lat1;
        float radLat2 = Mathf.Deg2Rad * lat2;
        float dLat = Mathf.Deg2Rad * (lat2 - lat1);
        float dLon = Mathf.Deg2Rad * (lon2 - lon1);

        float a = Mathf.Sin(dLat / 2) * Mathf.Sin(dLat / 2) +
                Mathf.Cos(radLat1) * Mathf.Cos(radLat2) *
                Mathf.Sin(dLon / 2) * Mathf.Sin(dLon / 2);
        float c = 2 * Mathf.Atan2(Mathf.Sqrt(a), Mathf.Sqrt(1 - a));

        return R * c;
    }

    /// <summary>
    /// 休講情報取得成功時のコールバック
    /// </summary>
    void OnKyukouInfoReceived(KyukouResponse response)
    {
        lastKyukouResponse = response;
        isLoadingKyukou = false;

        if (response.summary.total_cancellations > 0)
        {
            kyukouText = $"休講情報: {response.summary.total_cancellations}件の休講があります";
        }
        else
        {
            kyukouText = "休講情報: 本日の休講はありません";
        }

        Debug.Log($"休講情報取得完了: {response.summary.total_cancellations}件");
    }

    /// <summary>
    /// 休講情報取得失敗時のコールバック
    /// </summary>
    void OnKyukouApiError(string errorMessage)
    {
        isLoadingKyukou = false;
        kyukouText = $"休講情報: エラー - {errorMessage}";
        Debug.LogError($"休講情報取得エラー: {errorMessage}");
    }

}
