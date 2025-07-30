#nullable enable
using System;

/// <summary>
/// 型安全な設定管理サービスのインターフェース
/// </summary>
public interface ISettingsService
{
    /// <summary>
    /// Canvas APIトークンを取得
    /// </summary>
    string? GetCanvasApiToken();

    /// <summary>
    /// Canvas APIトークンを保存
    /// </summary>
    void SaveCanvasApiToken(string token);

    /// <summary>
    /// 通勤時間を取得（分単位）
    /// </summary>
    TimeSpan GetCommuteTime();

    /// <summary>
    /// 通勤時間を保存
    /// </summary>
    void SaveCommuteTime(TimeSpan commuteTime);

    /// <summary>
    /// 通知設定を取得
    /// </summary>
    NotificationSettings GetNotificationSettings();

    /// <summary>
    /// 通知設定を保存
    /// </summary>
    void SaveNotificationSettings(NotificationSettings settings);

    /// <summary>
    /// 設定が有効かどうかを確認
    /// </summary>
    ValidationResult ValidateSettings();

    /// <summary>
    /// すべての設定をクリア
    /// </summary>
    void ClearAllSettings();
}

/// <summary>
/// 通知設定を表すクラス
/// </summary>
public class NotificationSettings
{
    public bool IsEnabled { get; }
    public TimeSpan NotificationTime { get; }
    public NotificationFrequency Frequency { get; }

    public NotificationSettings(bool isEnabled, TimeSpan notificationTime, NotificationFrequency frequency)
    {
        IsEnabled = isEnabled;
        NotificationTime = notificationTime;
        Frequency = frequency;
    }

    public static NotificationSettings Default => new(true, TimeSpan.FromMinutes(30), NotificationFrequency.OncePerDay);
}

/// <summary>
/// 通知頻度を表すEnum
/// </summary>
public enum NotificationFrequency
{
    Disabled = 0,
    OncePerDay = 1,
    TwicePerDay = 2,
    Hourly = 3
}

/// <summary>
/// 設定の検証結果を表すクラス
/// </summary>
public class ValidationResult
{
    public bool IsValid { get; }
    public string[] ErrorMessages { get; }

    private ValidationResult(bool isValid, string[] errorMessages)
    {
        IsValid = isValid;
        ErrorMessages = errorMessages;
    }

    public static ValidationResult Success() => new(true, Array.Empty<string>());
    
    public static ValidationResult Failure(params string[] errorMessages) => new(false, errorMessages);
}