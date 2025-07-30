#nullable enable
using GameCanvas;
using UnityEngine;
using System;

/// <summary>
/// 位置情報管理クラス
/// GPS機能、位置記録、距離計算を担当
/// </summary>
public class LocationManager
{
    private readonly IGameCanvas gc;
    
    // 位置情報変数
    private float currentLatitude;
    private float currentLongitude;
    private float recordedLatitude;
    private float recordedLongitude;
    private bool isGpsStarted = false;
    
    // 位置情報更新イベント
    public event Action<float, float>? OnLocationUpdated;
    public event Action<float, float>? OnLocationRecorded;
    
    public LocationManager(IGameCanvas gameCanvas)
    {
        gc = gameCanvas ?? throw new ArgumentNullException(nameof(gameCanvas));
        
        // 初期位置（東京駅周辺）
        currentLatitude = 35.685410f;
        currentLongitude = 139.752842f;
        
        LoadRecordedLocation();
    }
    
    /// <summary>
    /// 現在地の緯度
    /// </summary>
    public float CurrentLatitude => currentLatitude;
    
    /// <summary>
    /// 現在地の経度
    /// </summary>
    public float CurrentLongitude => currentLongitude;
    
    /// <summary>
    /// 記録された緯度
    /// </summary>
    public float RecordedLatitude => recordedLatitude;
    
    /// <summary>
    /// 記録された経度
    /// </summary>
    public float RecordedLongitude => recordedLongitude;
    
    /// <summary>
    /// 位置情報が利用可能かどうか
    /// </summary>
    public bool HasLocationPermission => gc.HasGeolocationPermission;
    
    /// <summary>
    /// 位置情報が更新されたかどうか
    /// </summary>
    public bool HasLocationUpdate => gc.HasGeolocationUpdate;
    
    /// <summary>
    /// 位置情報サービスを開始
    /// </summary>
    public void StartLocationService()
    {
        if (!isGpsStarted)
        {
            gc.StartGeolocationService();
            isGpsStarted = true;
            Debug.Log("[LocationManager] GPS開始");
        }
    }
    
    /// <summary>
    /// 位置情報を更新（毎フレーム呼び出し）
    /// </summary>
    public void UpdateLocation()
    {
        if (gc.HasGeolocationUpdate)
        {
            currentLatitude = gc.GeolocationLastLatitude;
            currentLongitude = gc.GeolocationLastLongitude;
            
            OnLocationUpdated?.Invoke(currentLatitude, currentLongitude);
        }
    }
    
    /// <summary>
    /// 現在位置を記録
    /// </summary>
    public void RecordCurrentLocation()
    {
        recordedLatitude = currentLatitude;
        recordedLongitude = currentLongitude;
        
        // 保存
        gc.Save("recorded_lat", recordedLatitude);
        gc.Save("recorded_lng", recordedLongitude);
        
        OnLocationRecorded?.Invoke(recordedLatitude, recordedLongitude);
        Debug.Log($"[LocationManager] 位置記録: lat={recordedLatitude:F4}, lng={recordedLongitude:F4}");
    }
    
    /// <summary>
    /// 記録された位置情報を読み込み
    /// </summary>
    private void LoadRecordedLocation()
    {
        if (gc.TryLoad("recorded_lat", out recordedLatitude) && 
            gc.TryLoad("recorded_lng", out recordedLongitude))
        {
            Debug.Log($"[LocationManager] 記録位置読み込み: lat={recordedLatitude:F4}, lng={recordedLongitude:F4}");
        }
        else
        {
            recordedLatitude = 0f;
            recordedLongitude = 0f;
            Debug.Log("[LocationManager] 記録位置なし");
        }
    }
    
    /// <summary>
    /// 2点間の距離を計算（メートル単位）
    /// </summary>
    /// <param name="lat1">地点1の緯度</param>
    /// <param name="lon1">地点1の経度</param>
    /// <param name="lat2">地点2の緯度</param>
    /// <param name="lon2">地点2の経度</param>
    /// <returns>距離（メートル）</returns>
    public static float CalculateDistance(float lat1, float lon1, float lat2, float lon2)
    {
        const float EarthRadiusInMeters = 6371000f;

        float radLat1 = Mathf.Deg2Rad * lat1;
        float radLat2 = Mathf.Deg2Rad * lat2;
        float deltaLat = Mathf.Deg2Rad * (lat2 - lat1);
        float deltaLon = Mathf.Deg2Rad * (lon2 - lon1);

        float a = Mathf.Sin(deltaLat / 2) * Mathf.Sin(deltaLat / 2) +
                 Mathf.Cos(radLat1) * Mathf.Cos(radLat2) *
                 Mathf.Sin(deltaLon / 2) * Mathf.Sin(deltaLon / 2);
        float c = 2 * Mathf.Atan2(Mathf.Sqrt(a), Mathf.Sqrt(1 - a));

        return EarthRadiusInMeters * c;
    }
    
    /// <summary>
    /// 現在地と記録地点の距離を取得
    /// </summary>
    /// <returns>距離（メートル）</returns>
    public float GetDistanceFromRecordedLocation()
    {
        return CalculateDistance(recordedLatitude, recordedLongitude, currentLatitude, currentLongitude);
    }
    
    /// <summary>
    /// 位置情報の状態を文字列で取得
    /// </summary>
    /// <returns>位置情報状態の説明文</returns>
    public string GetLocationStatusText()
    {
        if (!HasLocationPermission)
        {
            return "位置情報サービスが無効です";
        }
        
        if (!HasLocationUpdate)
        {
            return "取得中";
        }
        
        return $"緯度: {currentLatitude:F6}\n経度: {currentLongitude:F6}";
    }
}