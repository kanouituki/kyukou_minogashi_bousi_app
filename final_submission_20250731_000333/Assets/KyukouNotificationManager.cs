#nullable enable
using UnityEngine;
using System;
using KyukouApp;

/// <summary>
/// 休講通知管理クラス
/// 休講情報の分析と通知タイミングの判定を担当
/// </summary>
public class KyukouNotificationManager
{
    private KyukouResponse? lastResponse;
    private string currentNotification = "";
    private bool hasNotifiedToday = false;
    
    // 通知イベント
    public event Action<string>? OnNotificationUpdated;
    
    /// <summary>
    /// 現在の通知メッセージ
    /// </summary>
    public string CurrentNotification => currentNotification;
    
    /// <summary>
    /// 今日通知済みかどうか
    /// </summary>
    public bool HasNotifiedToday => hasNotifiedToday;
    
    /// <summary>
    /// 最後に受信した休講情報
    /// </summary>
    public KyukouResponse? LastResponse => lastResponse;
    
    /// <summary>
    /// 休講情報を更新
    /// </summary>
    /// <param name="response">新しい休講情報</param>
    public void UpdateKyukouInfo(KyukouResponse response)
    {
        lastResponse = response;
        
        // 通知メッセージをクリア（新しい情報が来たらリセット）
        if (currentNotification.StartsWith("休講"))
        {
            currentNotification = "";
            OnNotificationUpdated?.Invoke(currentNotification);
        }
        
        Debug.Log($"[KyukouNotificationManager] 休講情報を更新: {response.summary.total_cancellations}件");
    }
    
    /// <summary>
    /// 通知チェックを実行
    /// </summary>
    /// <param name="locationManager">位置情報管理</param>
    /// <param name="settingsManager">設定管理</param>
    public void CheckNotification(LocationManager? locationManager, SettingsManager? settingsManager)
    {
        if (lastResponse == null || lastResponse.cancellations.Length == 0)
        {
            SetNotification("");
            return;
        }
        
        if (locationManager == null || settingsManager == null)
        {
            SetNotification("位置情報または設定が利用できません");
            return;
        }
        
        if (!locationManager.HasLocationUpdate || hasNotifiedToday)
        {
            return;
        }
        
        if (!settingsManager.HasCommuteTime)
        {
            SetNotification("通学時間が設定されていません");
            return;
        }
        
        var now = DateTime.Now;
        string today = now.ToString("yyyy-MM-dd");
        
        foreach (var cancellation in lastResponse.cancellations)
        {
            if (CheckCancellationNotification(cancellation, today, now, locationManager, settingsManager))
            {
                break; // 一つでも通知があれば終了
            }
        }
    }
    
    /// <summary>
    /// 個別の休講について通知チェック
    /// </summary>
    private bool CheckCancellationNotification(Cancellation cancellation, string today, DateTime now, 
                                             LocationManager locationManager, SettingsManager settingsManager)
    {
        if (cancellation.date != today) return false;
        
        var startTime = GetStartTimeForPeriod(cancellation.period, now);
        if (startTime == DateTime.MinValue) return false;
        
        // 出発すべき時刻（授業開始 - 通学時間）
        var departTime = startTime.AddMinutes(-settingsManager.CommuteTimeMinutes);
        
        // 許容範囲 ±5分
        var rangeStart = departTime.AddMinutes(-5);
        var rangeEnd = departTime.AddMinutes(5);
        
        if (now >= rangeStart && now <= rangeEnd)
        {
            float distance = locationManager.GetDistanceFromRecordedLocation();
            if (distance >= 500f)
            {
                string message = $"休講 ({cancellation.course})：出発時間です！現在地が500m以上離れています（{distance:F1}m）";
                SetNotification(message);
                hasNotifiedToday = true;
                Debug.Log($"[KyukouNotificationManager] 通知発生: {message}");
                return true;
            }
            else
            {
                string message = $"休講 ({cancellation.course})：既に近くにいます（{distance:F1}m）";
                SetNotification(message);
                return false; // 距離的には問題ないので、他の休講もチェック
            }
        }
        
        return false;
    }
    
    /// <summary>
    /// 通知メッセージを設定
    /// </summary>
    private void SetNotification(string message)
    {
        if (currentNotification != message)
        {
            currentNotification = message;
            OnNotificationUpdated?.Invoke(currentNotification);
        }
    }
    
    /// <summary>
    /// 時限から開始時刻を取得
    /// </summary>
    /// <param name="period">時限（文字列）</param>
    /// <param name="day">対象日</param>
    /// <returns>開始時刻（取得できない場合はDateTime.MinValue）</returns>
    public static DateTime GetStartTimeForPeriod(string period, DateTime day)
    {
        return period switch
        {
            "1" => new DateTime(day.Year, day.Month, day.Day, 9, 25, 0),
            "2" => new DateTime(day.Year, day.Month, day.Day, 11, 10, 0),
            "3" => new DateTime(day.Year, day.Month, day.Day, 13, 0, 0),
            "4" => new DateTime(day.Year, day.Month, day.Day, 14, 45, 0),
            "5" => new DateTime(day.Year, day.Month, day.Day, 16, 30, 0),
            "6" => new DateTime(day.Year, day.Month, day.Day, 18, 0, 0),
            _ => DateTime.MinValue
        };
    }
    
    /// <summary>
    /// 休講情報のサマリーテキストを生成
    /// </summary>
    /// <returns>休講情報のサマリー</returns>
    public string GetKyukouSummaryText()
    {
        if (lastResponse == null)
        {
            return "休講情報: 未取得";
        }
        
        if (lastResponse.summary.total_cancellations > 0)
        {
            return $"休講情報: {lastResponse.summary.total_cancellations}件の休講があります";
        }
        else
        {
            return "休講情報: 本日の休講はありません";
        }
    }
    
    /// <summary>
    /// 今日の休講一覧を取得
    /// </summary>
    /// <returns>今日の休講情報リスト</returns>
    public Cancellation[] GetTodayCancellations()
    {
        if (lastResponse == null || lastResponse.cancellations.Length == 0)
        {
            return new Cancellation[0];
        }
        
        string today = DateTime.Now.ToString("yyyy-MM-dd");
        var todayCancellations = new System.Collections.Generic.List<Cancellation>();
        
        foreach (var cancellation in lastResponse.cancellations)
        {
            if (cancellation.date == today)
            {
                todayCancellations.Add(cancellation);
            }
        }
        
        return todayCancellations.ToArray();
    }
    
    /// <summary>
    /// 通知状態をリセット（日付変更時用）
    /// </summary>
    public void ResetDailyNotification()
    {
        hasNotifiedToday = false;
        currentNotification = "";
        OnNotificationUpdated?.Invoke(currentNotification);
        Debug.Log("[KyukouNotificationManager] 日次通知状態をリセット");
    }
    
    /// <summary>
    /// エラーメッセージを設定
    /// </summary>
    /// <param name="errorMessage">エラーメッセージ</param>
    public void SetError(string errorMessage)
    {
        SetNotification($"エラー: {errorMessage}");
        ErrorHandler.HandleNotificationError("エラー通知設定", errorMessage);
    }
    
    /// <summary>
    /// デバッグ情報を出力
    /// </summary>
    public void LogDebugInfo()
    {
        Debug.Log($"[KyukouNotificationManager] === デバッグ情報 ===");
        Debug.Log($"[KyukouNotificationManager] 最終取得日時: {lastResponse?.summary.analyzed_at ?? "未取得"}");
        Debug.Log($"[KyukouNotificationManager] 休講件数: {lastResponse?.summary.total_cancellations ?? 0}");
        Debug.Log($"[KyukouNotificationManager] 今日通知済み: {hasNotifiedToday}");
        Debug.Log($"[KyukouNotificationManager] 現在の通知: {currentNotification}");
        
        var todayCancellations = GetTodayCancellations();
        Debug.Log($"[KyukouNotificationManager] 今日の休講: {todayCancellations.Length}件");
        
        foreach (var cancellation in todayCancellations)
        {
            var startTime = GetStartTimeForPeriod(cancellation.period, DateTime.Now);
            Debug.Log($"[KyukouNotificationManager] - {cancellation.course} {cancellation.period}限 {startTime:HH:mm}開始");
        }
    }
}