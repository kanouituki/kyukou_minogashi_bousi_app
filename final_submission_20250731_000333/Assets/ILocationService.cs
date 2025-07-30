#nullable enable
using System;
using System.Threading.Tasks;

/// <summary>
/// 型安全な位置情報サービスのインターフェース
/// </summary>
public interface ILocationService
{
    /// <summary>
    /// 位置情報の許可状態を取得
    /// </summary>
    LocationPermissionStatus GetPermissionStatus();

    /// <summary>
    /// 位置情報サービスを開始
    /// </summary>
    Task<bool> StartLocationServiceAsync();

    /// <summary>
    /// 現在の位置情報を取得
    /// </summary>
    Task<LocationResult> GetCurrentLocationAsync();

    /// <summary>
    /// 位置情報の更新が利用可能かどうか
    /// </summary>
    bool HasLocationUpdate();

    /// <summary>
    /// 2点間の距離を計算（メートル）
    /// </summary>
    double CalculateDistance(float lat1, float lon1, float lat2, float lon2);

    /// <summary>
    /// 指定位置から大学までの距離を取得
    /// </summary>
    Task<DistanceResult> GetDistanceToUniversityAsync(float currentLat, float currentLon);
}

/// <summary>
/// 位置情報の許可状態を表すEnum
/// </summary>
public enum LocationPermissionStatus
{
    Unknown = 0,
    Denied = 1,
    Granted = 2,
    GrantedWhenInUse = 3,
    GrantedAlways = 4
}

/// <summary>
/// 距離計算の結果を表すクラス
/// </summary>
public class DistanceResult
{
    public double DistanceInMeters { get; }
    public TimeSpan EstimatedTravelTime { get; }
    public TravelMethod RecommendedMethod { get; }
    public bool IsWithinCommuteRange { get; }

    public DistanceResult(double distanceInMeters, TimeSpan estimatedTravelTime, TravelMethod recommendedMethod, bool isWithinCommuteRange)
    {
        DistanceInMeters = distanceInMeters;
        EstimatedTravelTime = estimatedTravelTime;
        RecommendedMethod = recommendedMethod;
        IsWithinCommuteRange = isWithinCommuteRange;
    }

    public static DistanceResult FromDistance(double distanceInMeters)
    {
        var travelMethod = distanceInMeters switch
        {
            < 1000 => TravelMethod.Walking,
            < 5000 => TravelMethod.Bicycle,
            < 15000 => TravelMethod.PublicTransport,
            _ => TravelMethod.Car
        };

        var estimatedTime = travelMethod switch
        {
            TravelMethod.Walking => TimeSpan.FromMinutes(distanceInMeters / 80),        // 80m/分
            TravelMethod.Bicycle => TimeSpan.FromMinutes(distanceInMeters / 200),       // 200m/分
            TravelMethod.PublicTransport => TimeSpan.FromMinutes(distanceInMeters / 500), // 500m/分
            TravelMethod.Car => TimeSpan.FromMinutes(distanceInMeters / 800),           // 800m/分
            _ => TimeSpan.Zero
        };

        var isWithinRange = distanceInMeters < 30000; // 30km以内

        return new DistanceResult(distanceInMeters, estimatedTime, travelMethod, isWithinRange);
    }
}

/// <summary>
/// 移動手段を表すEnum
/// </summary>
public enum TravelMethod
{
    Unknown = 0,
    Walking = 1,
    Bicycle = 2,
    PublicTransport = 3,
    Car = 4
}