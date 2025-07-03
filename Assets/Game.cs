#nullable enable
using GameCanvas;
using Unity.Mathematics;
using UnityEngine;
using UnityEngine.InputSystem;

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

    GcRect record_button = new GcRect(0, 50, 160, 80);

    /// <summary>
    /// 初期化処理
    /// </summary>
    public override void InitGame()
    {
        gc.SetResolution(720, 1280);
        lat = 35.685410f;
        lng = 139.752842f;
        text = "取得中";
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

        gc.FillRect(record_button);
        gc.DrawString("記録された緯度:"+recorded_lat.ToString(), 0, 180);
        gc.DrawString("記録された経度:"+recorded_lng.ToString(), 0, 210);
        gc.DrawString("現在地までの距離："+distance.ToString(), 0, 240);

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

}
