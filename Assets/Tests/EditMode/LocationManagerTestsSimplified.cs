using NUnit.Framework;
using UnityEngine;
using GameCanvas;

/// <summary>
/// LocationManager の単体テスト（簡略版）
/// </summary>
public class LocationManagerTestsSimplified
{
    private MockGameCanvas mockGameCanvas;
    private LocationManager locationManager;

    [SetUp]
    public void SetUp()
    {
        mockGameCanvas = new MockGameCanvas();
        locationManager = new LocationManager(mockGameCanvas);
    }

    [TearDown]
    public void TearDown()
    {
        locationManager = null;
        mockGameCanvas = null;
    }

    [Test]
    public void Constructor_ValidGameCanvas_InitializesCorrectly()
    {
        // Act & Assert
        Assert.IsNotNull(locationManager);
        Assert.AreEqual(35.685410f, locationManager.CurrentLatitude, 0.000001f);
        Assert.AreEqual(139.752842f, locationManager.CurrentLongitude, 0.000001f);
    }

    [Test]
    public void Constructor_NullGameCanvas_ThrowsArgumentNullException()
    {
        // Act & Assert
        Assert.Throws<System.ArgumentNullException>(() => new LocationManager(null));
    }

    [Test]
    public void StartLocationService_CallsGameCanvasMethod()
    {
        // Act
        locationManager.StartLocationService();
        
        // Assert
        Assert.AreEqual(1, mockGameCanvas.StartGeolocationServiceCallCount);
    }

    [Test]
    public void UpdateLocation_HasGeolocationUpdate_UpdatesCurrentLocation()
    {
        // Arrange
        float expectedLat = 35.681382f;
        float expectedLng = 139.766084f;
        
        mockGameCanvas.HasGeolocationUpdate = true;
        mockGameCanvas.GeolocationLastLatitude = expectedLat;
        mockGameCanvas.GeolocationLastLongitude = expectedLng;
        
        bool eventRaised = false;
        locationManager.OnLocationUpdated += (lat, lng) => eventRaised = true;
        
        // Act
        locationManager.UpdateLocation();
        
        // Assert
        Assert.AreEqual(expectedLat, locationManager.CurrentLatitude, 0.000001f);
        Assert.AreEqual(expectedLng, locationManager.CurrentLongitude, 0.000001f);
        Assert.IsTrue(eventRaised);
    }

    [Test]
    public void UpdateLocation_NoGeolocationUpdate_DoesNotUpdateLocation()
    {
        // Arrange
        float initialLat = locationManager.CurrentLatitude;
        float initialLng = locationManager.CurrentLongitude;
        
        mockGameCanvas.HasGeolocationUpdate = false;
        
        bool eventRaised = false;
        locationManager.OnLocationUpdated += (lat, lng) => eventRaised = true;
        
        // Act
        locationManager.UpdateLocation();
        
        // Assert
        Assert.AreEqual(initialLat, locationManager.CurrentLatitude);
        Assert.AreEqual(initialLng, locationManager.CurrentLongitude);
        Assert.IsFalse(eventRaised);
    }

    [Test]
    public void RecordCurrentLocation_SavesCurrentLocation()
    {
        // Arrange
        float expectedLat = 35.681382f;
        float expectedLng = 139.766084f;
        
        mockGameCanvas.HasGeolocationUpdate = true;
        mockGameCanvas.GeolocationLastLatitude = expectedLat;
        mockGameCanvas.GeolocationLastLongitude = expectedLng;
        
        locationManager.UpdateLocation();
        
        // Act
        locationManager.RecordCurrentLocation();
        
        // Assert
        Assert.IsTrue(mockGameCanvas.TryLoad("recorded_lat", out float savedLat));
        Assert.IsTrue(mockGameCanvas.TryLoad("recorded_lng", out float savedLng));
        Assert.AreEqual(expectedLat, savedLat, 0.000001f);
        Assert.AreEqual(expectedLng, savedLng, 0.000001f);
    }

    [Test]
    public void GetLocationStatusText_NoPermission_ReturnsErrorMessage()
    {
        // Arrange
        mockGameCanvas.HasGeolocationPermission = false;
        
        // Act
        string result = locationManager.GetLocationStatusText();
        
        // Assert
        Assert.AreEqual("位置情報サービスが無効です", result);
    }

    [Test]
    public void GetLocationStatusText_NoUpdate_ReturnsWaitingMessage()
    {
        // Arrange
        mockGameCanvas.HasGeolocationPermission = true;
        mockGameCanvas.HasGeolocationUpdate = false;
        
        // Act
        string result = locationManager.GetLocationStatusText();
        
        // Assert
        Assert.AreEqual("取得中", result);
    }

    [TestCase(35.681382f, 139.766084f, 35.685410f, 139.752842f, 1000f, 2000f)]
    [TestCase(0f, 0f, 0f, 0f, 0f, 1f)]
    public void CalculateDistance_VariousCoordinates_ReturnsExpectedRange(
        float lat1, float lng1, float lat2, float lng2, float minExpected, float maxExpected)
    {
        // Act
        float result = LocationManager.CalculateDistance(lat1, lng1, lat2, lng2);
        
        // Assert
        Assert.GreaterOrEqual(result, minExpected);
        Assert.LessOrEqual(result, maxExpected);
    }

    [Test]
    public void GetDistanceFromRecordedLocation_WithRecordedLocation_ReturnsCorrectDistance()
    {
        // Arrange
        float recordedLat = 35.681382f;
        float recordedLng = 139.766084f;
        float currentLat = 35.685410f;
        float currentLng = 139.752842f;
        
        // 記録位置を設定
        mockGameCanvas.Save("recorded_lat", recordedLat);
        mockGameCanvas.Save("recorded_lng", recordedLng);
        
        // 新しいLocationManagerを作成（記録位置付き）
        var locationManagerWithRecord = new LocationManager(mockGameCanvas);
        
        // 現在位置を更新
        mockGameCanvas.HasGeolocationUpdate = true;
        mockGameCanvas.GeolocationLastLatitude = currentLat;
        mockGameCanvas.GeolocationLastLongitude = currentLng;
        locationManagerWithRecord.UpdateLocation();
        
        // Act
        float result = locationManagerWithRecord.GetDistanceFromRecordedLocation();
        
        // Assert
        float expected = LocationManager.CalculateDistance(recordedLat, recordedLng, currentLat, currentLng);
        Assert.AreEqual(expected, result, 0.1f);
    }
}