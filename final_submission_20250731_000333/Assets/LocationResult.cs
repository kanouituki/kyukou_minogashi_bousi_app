#nullable enable
using System;

/// <summary>
/// 位置情報サービスの結果を表す型安全なクラス
/// </summary>
public class LocationResult
{
    public float Latitude { get; }
    public float Longitude { get; }
    public LocationAccuracy Accuracy { get; }
    public DateTime Timestamp { get; }
    public bool IsValid { get; }
    public string? ErrorMessage { get; }

    private LocationResult(float latitude, float longitude, LocationAccuracy accuracy, DateTime timestamp, string? errorMessage = null)
    {
        Latitude = latitude;
        Longitude = longitude;
        Accuracy = accuracy;
        Timestamp = timestamp;
        IsValid = errorMessage == null;
        ErrorMessage = errorMessage;
    }

    /// <summary>
    /// 成功した位置情報結果を作成
    /// </summary>
    public static LocationResult Success(float latitude, float longitude, LocationAccuracy accuracy)
    {
        return new LocationResult(latitude, longitude, accuracy, DateTime.Now);
    }

    /// <summary>
    /// 失敗した位置情報結果を作成
    /// </summary>
    public static LocationResult Failure(string errorMessage)
    {
        return new LocationResult(0, 0, LocationAccuracy.Unknown, DateTime.Now, errorMessage);
    }
}

/// <summary>
/// 位置情報の精度を表すEnum
/// </summary>
public enum LocationAccuracy
{
    Unknown = 0,
    Poor = 1,      // 100m以上の誤差
    Fair = 2,      // 10-100mの誤差
    Good = 3,      // 3-10mの誤差
    Excellent = 4  // 3m未満の誤差
}