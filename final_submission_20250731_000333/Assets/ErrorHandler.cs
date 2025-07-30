#nullable enable
using System;
using UnityEngine;

/// <summary>
/// 統一エラーハンドリングクラス
/// </summary>
public static class ErrorHandler
{
    /// <summary>
    /// API関連のエラーを処理
    /// </summary>
    /// <param name="operation">実行していた操作名</param>
    /// <param name="ex">発生した例外</param>
    /// <param name="additionalInfo">追加情報（任意）</param>
    public static void HandleApiError(string operation, Exception ex, string? additionalInfo = null)
    {
        var message = $"[API エラー] {operation}: {ex.Message}";
        if (!string.IsNullOrEmpty(additionalInfo))
        {
            message += $" - 追加情報: {additionalInfo}";
        }
        
        Debug.LogError(message);
        Debug.LogException(ex);
    }

    /// <summary>
    /// 位置情報関連のエラーを処理
    /// </summary>
    /// <param name="operation">実行していた操作名</param>
    /// <param name="errorMessage">エラーメッセージ</param>
    public static void HandleLocationError(string operation, string errorMessage)
    {
        var message = $"[位置情報 エラー] {operation}: {errorMessage}";
        Debug.LogError(message);
    }

    /// <summary>
    /// UI関連のエラーを処理
    /// </summary>
    /// <param name="operation">実行していた操作名</param>
    /// <param name="errorMessage">エラーメッセージ</param>
    public static void HandleUIError(string operation, string errorMessage)
    {
        var message = $"[UI エラー] {operation}: {errorMessage}";
        Debug.LogError(message);
    }

    /// <summary>
    /// 設定関連のエラーを処理
    /// </summary>
    /// <param name="operation">実行していた操作名</param>
    /// <param name="errorMessage">エラーメッセージ</param>
    public static void HandleSettingsError(string operation, string errorMessage)
    {
        var message = $"[設定 エラー] {operation}: {errorMessage}";
        Debug.LogError(message);
    }

    /// <summary>
    /// 通知関連のエラーを処理
    /// </summary>
    /// <param name="operation">実行していた操作名</param>
    /// <param name="errorMessage">エラーメッセージ</param>
    public static void HandleNotificationError(string operation, string errorMessage)
    {
        var message = $"[通知 エラー] {operation}: {errorMessage}";
        Debug.LogError(message);
    }

    /// <summary>
    /// 一般的なエラーを処理
    /// </summary>
    /// <param name="component">コンポーネント名</param>
    /// <param name="operation">実行していた操作名</param>
    /// <param name="ex">発生した例外</param>
    public static void HandleGeneralError(string component, string operation, Exception ex)
    {
        var message = $"[{component}] {operation}でエラーが発生: {ex.Message}";
        Debug.LogError(message);
        Debug.LogException(ex);
    }

    /// <summary>
    /// 一般的なエラーを処理（例外なし）
    /// </summary>
    /// <param name="component">コンポーネント名</param>
    /// <param name="operation">実行していた操作名</param>
    /// <param name="errorMessage">エラーメッセージ</param>
    public static void HandleGeneralError(string component, string operation, string errorMessage)
    {
        var message = $"[{component}] {operation}でエラーが発生: {errorMessage}";
        Debug.LogError(message);
    }
}