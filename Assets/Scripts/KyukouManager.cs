using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Networking;

/// <summary>
/// Main manager that handles fetching cancellation information, monitoring location, and sending notifications.
/// Attach this script to a GameObject in the Unity scene.
/// </summary>
public class KyukouManager : MonoBehaviour
{
    [SerializeField]
    private string apiUrl = "https://example.com/cancellation.json"; // TODO: replace with real API URL

    private const float DistanceThresholdMeters = 500f;

    private CancellationResponse todayData;

    private void Start()
    {
        StartCoroutine(Initialize());
    }

    private IEnumerator Initialize()
    {
        // If first launch, save current location as home.
        if (!HomeLocationManager.HasHomeLocation())
        {
            yield return StartCoroutine(InitializeHomeLocation());
        }

        yield return StartCoroutine(FetchCancellationInfo());
        CheckTodayCancellations();
    }

    /// <summary>
    /// Obtains the user's current location and saves it as the home coordinates.
    /// </summary>
    private IEnumerator InitializeHomeLocation()
    {
        if (!Input.location.isEnabledByUser)
        {
            Debug.LogWarning("Location service is disabled by the user.");
            yield break;
        }

        Input.location.Start();
        int maxWait = 20;
        while (Input.location.status == LocationServiceStatus.Initializing && maxWait > 0)
        {
            yield return new WaitForSeconds(1);
            maxWait--;
        }

        if (Input.location.status == LocationServiceStatus.Running)
        {
            var loc = Input.location.lastData;
            HomeLocationManager.SaveHomeLocation(loc.latitude, loc.longitude);
            Input.location.Stop();
        }
        else
        {
            Debug.LogError("Unable to determine device location.");
        }
    }

    /// <summary>
    /// Fetches cancellation JSON from the server.
    /// </summary>
    private IEnumerator FetchCancellationInfo()
    {
        using (UnityWebRequest www = UnityWebRequest.Get(apiUrl))
        {
            yield return www.SendWebRequest();

            if (www.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError($"Failed to download cancellation info: {www.error}");
            }
            else
            {
                File.WriteAllText(GetLocalPath(), www.downloadHandler.text);
            }
        }
    }

    /// <summary>
    /// Reads the saved JSON file and extracts today's cancellations.
    /// </summary>
    private void CheckTodayCancellations()
    {
        string path = GetLocalPath();
        if (!File.Exists(path))
        {
            Debug.LogWarning("No cancellation file found.");
            return;
        }

        string json = File.ReadAllText(path);
        todayData = JsonUtility.FromJson<CancellationResponse>(json);
        string today = DateTime.Now.ToString("yyyy-MM-dd");

        foreach (var entry in todayData.cancellations)
        {
            if (entry.date == today && entry.canceled)
            {
                DateTime classTime = GetClassTime(entry.period, today);
                DateTime monitorStart = classTime.AddHours(-1);
                StartCoroutine(MonitorLocation(monitorStart, entry));
            }
        }
    }

    /// <summary>
    /// Starts monitoring location from the given time until the user is 500m away from home.
    /// </summary>
    private IEnumerator MonitorLocation(DateTime startTime, CancellationEntry entry)
    {
        // Wait until monitoring should begin
        while (DateTime.Now < startTime)
        {
            yield return new WaitForSeconds(30); // check every 30 seconds
        }

        if (!Input.location.isEnabledByUser)
        {
            yield break;
        }

        Input.location.Start();
        while (true)
        {
            if (Input.location.status == LocationServiceStatus.Running)
            {
                var current = Input.location.lastData;
                Vector2 home = HomeLocationManager.GetHomeLocation();
                float dist = HaversineDistance(home, new Vector2(current.latitude, current.longitude));
                if (dist > DistanceThresholdMeters)
                {
                    SendLocalNotification(entry);
                    break;
                }
            }
            yield return new WaitForSeconds(10);
        }
        Input.location.Stop();
    }

    /// <summary>
    /// Calculates the Haversine distance between two coordinates in meters.
    /// </summary>
    private float HaversineDistance(Vector2 a, Vector2 b)
    {
        const float R = 6371000f; // Earth radius in meters
        float lat1 = a.x * Mathf.Deg2Rad;
        float lat2 = b.x * Mathf.Deg2Rad;
        float dLat = (b.x - a.x) * Mathf.Deg2Rad;
        float dLon = (b.y - a.y) * Mathf.Deg2Rad;

        float h = Mathf.Sin(dLat / 2) * Mathf.Sin(dLat / 2) +
                  Mathf.Cos(lat1) * Mathf.Cos(lat2) *
                  Mathf.Sin(dLon / 2) * Mathf.Sin(dLon / 2);
        float c = 2 * Mathf.Atan2(Mathf.Sqrt(h), Mathf.Sqrt(1 - h));
        return R * c;
    }

    /// <summary>
    /// Converts period string (e.g., "2限") into a DateTime on the given date.
    /// </summary>
    private DateTime GetClassTime(string period, string date)
    {
        int hour = 9; // default for 1st period
        switch (period)
        {
            case "1限": hour = 9; break;
            case "2限": hour = 11; break;
            case "3限": hour = 13; break;
            case "4限": hour = 15; break;
            case "5限": hour = 17; break;
            default: break;
        }
        return DateTime.Parse(date).AddHours(hour);
    }

    /// <summary>
    /// Sends a simple local notification about the canceled class.
    /// </summary>
    private void SendLocalNotification(CancellationEntry entry)
    {
#if UNITY_IOS
        var notif = new UnityEngine.iOS.LocalNotification();
        notif.alertBody = $"今日の{entry.period}の『{entry.course}』は休講です。";
        notif.fireDate = DateTime.Now;
        UnityEngine.iOS.NotificationServices.ScheduleLocalNotification(notif);
#elif UNITY_ANDROID
        // Minimal example using Unity's AndroidJavaClass for local notification
        using (var unityPlayer = new AndroidJavaClass("com.unity3d.player.UnityPlayer"))
        using (var currentActivity = unityPlayer.GetStatic<AndroidJavaObject>("currentActivity"))
        using (var context = currentActivity.Call<AndroidJavaObject>("getApplicationContext"))
        {
            // Here you would call into a Java plugin to show notification
            Debug.Log($"Notification: 今日の{entry.period}の『{entry.course}』は休講です。");
        }
#else
        Debug.Log($"Notification: 今日の{entry.period}の『{entry.course}』は休講です。");
#endif
    }

    private string GetLocalPath()
    {
        return Path.Combine(Application.persistentDataPath, "cancellations.json");
    }
}
