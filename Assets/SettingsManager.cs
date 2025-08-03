#nullable enable
using GameCanvas;
using UnityEngine;
using System;

/// <summary>
/// 設定管理クラス
/// アプリの各種設定の保存・読み込みを担当
/// </summary>
public class SettingsManager
{
    private readonly IGameCanvasLite gc;
    
    // 設定値
    private string canvasApiToken = "";
    private int commuteTimeMinutes = 0;
    
    // 設定更新イベント
    public event Action<string>? OnCanvasTokenChanged;
    public event Action<int>? OnCommuteTimeChanged;
    
    public SettingsManager(IGameCanvasLite gameCanvas)
    {
        gc = gameCanvas ?? throw new ArgumentNullException(nameof(gameCanvas));
        LoadAllSettings();
    }
    
    /// <summary>
    /// Canvas APIトークン
    /// </summary>
    public string CanvasApiToken => canvasApiToken;
    
    /// <summary>
    /// 通学時間（分）
    /// </summary>
    public int CommuteTimeMinutes => commuteTimeMinutes;
    
    /// <summary>
    /// Canvas APIトークンが設定されているかどうか
    /// </summary>
    public bool HasCanvasApiToken => !string.IsNullOrEmpty(canvasApiToken);
    
    /// <summary>
    /// 通学時間が設定されているかどうか
    /// </summary>
    public bool HasCommuteTime => commuteTimeMinutes > 0;
    
    /// <summary>
    /// Canvas APIトークンを保存
    /// </summary>
    /// <param name="token">APIトークン</param>
    public void SaveCanvasApiToken(string token)
    {
        if (string.IsNullOrEmpty(token))
        {
            Debug.LogWarning("[SettingsManager] 空のAPIトークンを保存しようとしました");
            return;
        }
        
        canvasApiToken = token;
        gc.Save("canvas_api_token", canvasApiToken);
        OnCanvasTokenChanged?.Invoke(canvasApiToken);
        
        Debug.Log("[SettingsManager] Canvas APIトークンを保存しました");
    }
    
    /// <summary>
    /// 通学時間を保存
    /// </summary>
    /// <param name="minutes">通学時間（分）</param>
    public void SaveCommuteTime(int minutes)
    {
        if (minutes < 0)
        {
            Debug.LogWarning("[SettingsManager] 負の通学時間を保存しようとしました");
            return;
        }
        
        if (minutes > 300) // 5時間以上は異常値として扱う
        {
            Debug.LogWarning("[SettingsManager] 異常に長い通学時間です: " + minutes + "分");
        }
        
        commuteTimeMinutes = minutes;
        gc.Save("commute_time", commuteTimeMinutes);
        OnCommuteTimeChanged?.Invoke(commuteTimeMinutes);
        
        Debug.Log($"[SettingsManager] 通学時間を保存しました: {commuteTimeMinutes}分");
    }
    
    /// <summary>
    /// Canvas APIトークンを削除
    /// </summary>
    public void ClearCanvasApiToken()
    {
        canvasApiToken = "";
        gc.Save("canvas_api_token", canvasApiToken);
        OnCanvasTokenChanged?.Invoke(canvasApiToken);
        
        Debug.Log("[SettingsManager] Canvas APIトークンを削除しました");
    }
    
    /// <summary>
    /// 通学時間をリセット
    /// </summary>
    public void ClearCommuteTime()
    {
        commuteTimeMinutes = 20; // デフォルト値
        gc.Save("commute_time", commuteTimeMinutes);
        OnCommuteTimeChanged?.Invoke(commuteTimeMinutes);
        
        Debug.Log("[SettingsManager] 通学時間をリセットしました");
    }
    
    /// <summary>
    /// マスク表示用のトークン文字列を取得
    /// </summary>
    /// <returns>マスクされたトークン文字列</returns>
    public string GetMaskedToken()
    {
        if (string.IsNullOrEmpty(canvasApiToken))
            return "未設定";
        
        if (canvasApiToken.Length <= 8)
            return new string('●', canvasApiToken.Length);
        
        // 最初の4文字と最後の4文字以外をマスク
        string start = canvasApiToken.Substring(0, 4);
        string end = canvasApiToken.Substring(canvasApiToken.Length - 4);
        int maskCount = Math.Min(canvasApiToken.Length - 8, 12); // 最大12文字のマスク
        
        return $"{start}{new string('●', maskCount)}{end}";
    }
    
    /// <summary>
    /// 設定の検証を行う
    /// </summary>
    /// <returns>検証結果のメッセージ</returns>
    public string ValidateSettings()
    {
        var messages = new System.Collections.Generic.List<string>();
        
        if (!HasCanvasApiToken)
        {
            messages.Add("Canvas APIトークンが未設定");
        }
        else if (canvasApiToken.Length < 32)
        {
            messages.Add("Canvas APIトークンの形式が不正");
        }
        
        if (!HasCommuteTime)
        {
            messages.Add("通学時間が未設定");
        }
        else if (commuteTimeMinutes > 300)
        {
            messages.Add("通学時間が異常に長い");
        }
        
        return messages.Count > 0 ? string.Join(", ", messages) : "設定OK";
    }
    
    /// <summary>
    /// 全設定を読み込み
    /// </summary>
    private void LoadAllSettings()
    {
        // Canvas APIトークンの読み込み
        if (gc.TryLoad("canvas_api_token", out string loadedToken))
        {
            canvasApiToken = loadedToken;
            Debug.Log("[SettingsManager] Canvas APIトークンを読み込みました");
        }
        else
        {
            canvasApiToken = "";
            Debug.Log("[SettingsManager] Canvas APIトークンは未設定");
        }
        
        // 通学時間の読み込み
        if (gc.TryLoad("commute_time", out int loadedTime))
        {
            commuteTimeMinutes = loadedTime;
            Debug.Log($"[SettingsManager] 通学時間を読み込みました: {commuteTimeMinutes}分");
        }
        else
        {
            commuteTimeMinutes = 0;
            Debug.Log("[SettingsManager] 通学時間は未設定");
        }
    }
    
    /// <summary>
    /// Canvas APIトークンを取得
    /// </summary>
    public string GetCanvasApiToken()
    {
        return canvasApiToken;
    }
    
    /// <summary>
    /// 通学時間を取得
    /// </summary>
    public int GetCommuteTime()
    {
        return commuteTimeMinutes;
    }
    
    /// <summary>
    /// 設定が有効かどうか
    /// </summary>
    public bool HasValidSettings()
    {
        return HasCanvasApiToken && 
               HasCommuteTime && 
               canvasApiToken.Length >= 20 && 
               commuteTimeMinutes > 0 && 
               commuteTimeMinutes <= 300;
    }
    
    /// <summary>
    /// 全設定をクリア
    /// </summary>
    public void ClearAllSettings()
    {
        ClearCanvasApiToken();
        ClearCommuteTime();
        Debug.Log("[SettingsManager] 全設定をクリアしました");
    }
    
    /// <summary>
    /// 設定情報をデバッグ出力
    /// </summary>
    public void LogSettings()
    {
        Debug.Log($"[SettingsManager] === 設定情報 ===");
        Debug.Log($"[SettingsManager] Canvas API: {(HasCanvasApiToken ? "設定済み" : "未設定")}");
        Debug.Log($"[SettingsManager] 通学時間: {commuteTimeMinutes}分");
        Debug.Log($"[SettingsManager] 検証結果: {ValidateSettings()}");
    }
}