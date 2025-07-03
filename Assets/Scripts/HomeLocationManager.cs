using UnityEngine;

/// <summary>
/// Manages the home location. The home location is saved to PlayerPrefs on first launch.
/// </summary>
public static class HomeLocationManager
{
    private const string HomeLatKey = "HOME_LAT";
    private const string HomeLonKey = "HOME_LON";

    /// <summary>
    /// Returns true if a home location has been saved.
    /// </summary>
    public static bool HasHomeLocation()
    {
        return PlayerPrefs.HasKey(HomeLatKey) && PlayerPrefs.HasKey(HomeLonKey);
    }

    /// <summary>
    /// Saves the given location as the user's home coordinates.
    /// </summary>
    public static void SaveHomeLocation(float latitude, float longitude)
    {
        PlayerPrefs.SetFloat(HomeLatKey, latitude);
        PlayerPrefs.SetFloat(HomeLonKey, longitude);
        PlayerPrefs.Save();
    }

    /// <summary>
    /// Gets the stored home location.
    /// </summary>
    public static Vector2 GetHomeLocation()
    {
        return new Vector2(PlayerPrefs.GetFloat(HomeLatKey), PlayerPrefs.GetFloat(HomeLonKey));
    }
}
