#nullable enable
using System;

/// <summary>
/// 休講情報APIのレスポンスデータモデル
/// </summary>
namespace KyukouApp
{
    /// <summary>
    /// API全体のレスポンス
    /// </summary>
    [Serializable]
    public class KyukouResponse
    {
        public Summary summary = new Summary();
        public Cancellation[] cancellations = new Cancellation[0];
    }

    /// <summary>
    /// 休講情報の概要
    /// </summary>
    [Serializable]
    public class Summary
    {
        public int total_courses = 0;
        public int total_cancellations = 0;
        public string analyzed_at = "";
        public string api_version = "";
        public string source = "";
        public string source_file = "";
    }

    /// <summary>
    /// 個別の休講情報
    /// </summary>
    [Serializable]
    public class Cancellation
    {
        public int course_id = 0;
        public string course_name = "";
        public int announcement_id = 0;
        public string announcement_title = "";
        public string analyzed_at = "";
        public bool canceled = false;
        public string course = "";
        public string date = "";
        public string period = "";
        public string message = "";
        public string reason = "";
        public double confidence = 0.0;
    }

    /// <summary>
    /// API エラーレスポンス
    /// </summary>
    [Serializable]
    public class ApiError
    {
        public string detail = "";
        public int status_code = 0;
    }
}