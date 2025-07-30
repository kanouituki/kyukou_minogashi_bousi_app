#nullable enable
using System;

/// <summary>
/// API呼び出しの結果を表す型安全なクラス
/// </summary>
public class ApiResult<T> where T : class
{
    public bool IsSuccess { get; }
    public T? Data { get; }
    public string? ErrorMessage { get; }
    public ApiErrorType ErrorType { get; }

    private ApiResult(bool isSuccess, T? data, string? errorMessage, ApiErrorType errorType)
    {
        IsSuccess = isSuccess;
        Data = data;
        ErrorMessage = errorMessage;
        ErrorType = errorType;
    }

    /// <summary>
    /// 成功した結果を作成
    /// </summary>
    public static ApiResult<T> Success(T data)
    {
        return new ApiResult<T>(true, data, null, ApiErrorType.None);
    }

    /// <summary>
    /// 失敗した結果を作成
    /// </summary>
    public static ApiResult<T> Failure(string errorMessage, ApiErrorType errorType = ApiErrorType.Unknown)
    {
        return new ApiResult<T>(false, null, errorMessage, errorType);
    }

    /// <summary>
    /// ネットワークエラーの結果を作成
    /// </summary>
    public static ApiResult<T> NetworkError(string errorMessage)
    {
        return new ApiResult<T>(false, null, errorMessage, ApiErrorType.Network);
    }

    /// <summary>
    /// 認証エラーの結果を作成
    /// </summary>
    public static ApiResult<T> AuthenticationError(string errorMessage)
    {
        return new ApiResult<T>(false, null, errorMessage, ApiErrorType.Authentication);
    }

    /// <summary>
    /// パースエラーの結果を作成
    /// </summary>
    public static ApiResult<T> ParseError(string errorMessage)
    {
        return new ApiResult<T>(false, null, errorMessage, ApiErrorType.Parse);
    }

    /// <summary>
    /// タイムアウトエラーの結果を作成
    /// </summary>
    public static ApiResult<T> TimeoutError(string errorMessage)
    {
        return new ApiResult<T>(false, null, errorMessage, ApiErrorType.Timeout);
    }
}

/// <summary>
/// APIエラーの種類を表すEnum
/// </summary>
public enum ApiErrorType
{
    None = 0,
    Network = 1,
    Authentication = 2,
    Parse = 3,
    Timeout = 4,
    RateLimit = 5,
    ServerError = 6,
    Unknown = 999
}