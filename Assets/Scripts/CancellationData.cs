using System;
using System.Collections.Generic;
using UnityEngine;

[Serializable]
public class CancellationSummary
{
    public int total_courses;
    public int total_cancellations;
    public string analyzed_at;
}

[Serializable]
public class CancellationEntry
{
    public string course;
    public string date;
    public string period;
    public bool canceled;
    public string message;
}

[Serializable]
public class CancellationResponse
{
    public CancellationSummary summary;
    public List<CancellationEntry> cancellations;
}
