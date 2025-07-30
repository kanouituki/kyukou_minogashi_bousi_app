using NUnit.Framework;
using UnityEngine;
using GameCanvas;
using System;
using System.Threading;

/// <summary>
/// 統合テスト - メインシナリオのテスト
/// </summary>
public class IntegrationTests
{
    private MockGameCanvas mockGameCanvas;
    private LocationManager locationManager;
    private SettingsManager settingsManager;
    private KyukouNotificationManager notificationManager;

    [SetUp]
    public void SetUp()
    {
        mockGameCanvas = new MockGameCanvas();
        locationManager = new LocationManager(mockGameCanvas);
        settingsManager = new SettingsManager(mockGameCanvas);
        notificationManager = new KyukouNotificationManager();
    }

    [TearDown]
    public void TearDown()
    {
        notificationManager = null;
        settingsManager = null;
        locationManager = null;
        mockGameCanvas = null;
    }

    [Test]
    public void FullWorkflow_ValidSettings_LocationRecording_NotificationCheck()
    {
        // Arrange: 有効な設定を保存
        string validToken = "valid_canvas_token_1234567890abcdef";
        int commuteTime = 30;
        settingsManager.SaveCanvasApiToken(validToken);
        settingsManager.SaveCommuteTime(commuteTime);

        // Arrange: GPSを有効にして位置情報を設定
        mockGameCanvas.HasGeolocationPermission = true;
        mockGameCanvas.HasGeolocationUpdate = true;
        float testLat = 35.681382f;
        float testLng = 139.766084f;
        mockGameCanvas.GeolocationLastLatitude = testLat;
        mockGameCanvas.GeolocationLastLongitude = testLng;

        // Act: ワークフロー実行
        // 1. 位置情報サービス開始
        locationManager.StartLocationService();
        
        // 2. 位置情報更新
        locationManager.UpdateLocation();
        
        // 3. 現在位置記録
        locationManager.RecordCurrentLocation();
        
        // 4. 設定検証
        string validationResult = settingsManager.ValidateSettings();
        
        // 5. 通知チェック
        notificationManager.CheckNotification(locationManager, settingsManager);

        // Assert: 各ステップの結果を検証
        Assert.AreEqual(1, mockGameCanvas.StartGeolocationServiceCallCount);
        Assert.AreEqual(testLat, locationManager.CurrentLatitude, 0.000001f);
        Assert.AreEqual(testLng, locationManager.CurrentLongitude, 0.000001f);
        Assert.IsTrue(mockGameCanvas.TryLoad("recorded_lat", out float savedLat));
        Assert.IsTrue(mockGameCanvas.TryLoad("recorded_lng", out float savedLng));
        Assert.AreEqual(testLat, savedLat, 0.000001f);
        Assert.AreEqual(testLng, savedLng, 0.000001f);
        Assert.AreEqual("", validationResult);
        Assert.IsTrue(settingsManager.HasValidSettings());
    }

    [Test]
    public void ErrorHandling_InvalidSettings_ReturnsProperErrors()
    {
        // Arrange: 無効な設定
        settingsManager.SaveCanvasApiToken(""); // 空のトークン
        settingsManager.SaveCommuteTime(-5); // 負の値

        // Act: 設定検証
        string validationResult = settingsManager.ValidateSettings();
        bool hasValidSettings = settingsManager.HasValidSettings();

        // Assert: エラーが適切に返される
        Assert.IsFalse(hasValidSettings);
        Assert.IsTrue(validationResult.Contains("Canvas APIトークン"));
        Assert.IsTrue(validationResult.Contains("通学時間"));
    }

    [Test]
    public void LocationWorkflow_NoPermission_HandlesGracefully()
    {
        // Arrange: 位置情報許可なし
        mockGameCanvas.HasGeolocationPermission = false;
        mockGameCanvas.HasGeolocationUpdate = false;

        // Act: 位置情報関連の操作
        locationManager.StartLocationService();
        locationManager.UpdateLocation();
        string statusText = locationManager.GetLocationStatusText();

        // Assert: 適切なエラーメッセージが返される
        Assert.AreEqual("位置情報サービスが無効です", statusText);
        Assert.AreEqual(35.685410f, locationManager.CurrentLatitude, 0.000001f); // デフォルト値
        Assert.AreEqual(139.752842f, locationManager.CurrentLongitude, 0.000001f); // デフォルト値
    }

    [Test]
    public void LocationWorkflow_NoUpdate_ShowsWaitingMessage()
    {
        // Arrange: 許可はあるが更新なし
        mockGameCanvas.HasGeolocationPermission = true;
        mockGameCanvas.HasGeolocationUpdate = false;

        // Act: 位置情報関連の操作
        locationManager.StartLocationService();
        locationManager.UpdateLocation();
        string statusText = locationManager.GetLocationStatusText();

        // Assert: 待機メッセージが表示される
        Assert.AreEqual("取得中", statusText);
    }

    [Test]
    public void DistanceCalculation_BetweenRecordedAndCurrent_ReturnsCorrectValue()
    {
        // Arrange: 記録位置を設定
        float recordedLat = 35.681382f;
        float recordedLng = 139.766084f;
        mockGameCanvas.Save("recorded_lat", recordedLat);
        mockGameCanvas.Save("recorded_lng", recordedLng);

        // 新しいLocationManagerで記録位置を読み込み
        var locationManagerWithRecord = new LocationManager(mockGameCanvas);

        // 現在位置を異なる場所に設定
        float currentLat = 35.685410f;
        float currentLng = 139.752842f;
        mockGameCanvas.HasGeolocationUpdate = true;
        mockGameCanvas.GeolocationLastLatitude = currentLat;
        mockGameCanvas.GeolocationLastLongitude = currentLng;
        locationManagerWithRecord.UpdateLocation();

        // Act: 距離計算
        float distance = locationManagerWithRecord.GetDistanceFromRecordedLocation();
        float expectedDistance = LocationManager.CalculateDistance(recordedLat, recordedLng, currentLat, currentLng);

        // Assert: 距離が正しく計算される
        Assert.AreEqual(expectedDistance, distance, 0.1f);
        Assert.Greater(distance, 0f);
        Assert.Less(distance, 2000f); // 東京内の距離なので2km以下
    }

    [Test]
    public void TokenMasking_PreventsSensitiveDataExposure()
    {
        // Arrange: 機密情報を含むトークン
        string sensitiveToken = "sk_test_1234567890abcdef1234567890abcdef";
        settingsManager.SaveCanvasApiToken(sensitiveToken);

        // Act: マスク化されたトークンを取得
        string maskedToken = settingsManager.GetMaskedToken();

        // Assert: 機密情報が適切にマスクされている
        Assert.IsFalse(maskedToken.Contains(sensitiveToken));
        Assert.IsTrue(maskedToken.Contains("***"));
        Assert.AreEqual("sk_t***cdef", maskedToken);
    }

    [Test]
    public void NotificationTiming_GetStartTimeForPeriod_ReturnsCorrectTimes()
    {
        // Arrange: テスト用の日付
        DateTime testDay = new DateTime(2024, 1, 15); // 月曜日

        // Act & Assert: 各時限の開始時間をテスト
        DateTime period1 = KyukouNotificationManager.GetStartTimeForPeriod("1", testDay);
        DateTime period2 = KyukouNotificationManager.GetStartTimeForPeriod("2", testDay);
        DateTime period3 = KyukouNotificationManager.GetStartTimeForPeriod("3", testDay);
        DateTime period4 = KyukouNotificationManager.GetStartTimeForPeriod("4", testDay);
        DateTime period5 = KyukouNotificationManager.GetStartTimeForPeriod("5", testDay);

        Assert.AreEqual(new DateTime(2024, 1, 15, 9, 0, 0), period1);
        Assert.AreEqual(new DateTime(2024, 1, 15, 10, 40, 0), period2);
        Assert.AreEqual(new DateTime(2024, 1, 15, 13, 0, 0), period3);
        Assert.AreEqual(new DateTime(2024, 1, 15, 14, 40, 0), period4);
        Assert.AreEqual(new DateTime(2024, 1, 15, 16, 20, 0), period5);
    }

    [Test]
    public void NotificationTiming_InvalidPeriod_ReturnsDefaultTime()
    {
        // Arrange: 無効な時限
        DateTime testDay = new DateTime(2024, 1, 15);

        // Act: 無効な時限の開始時間を取得
        DateTime invalidPeriod = KyukouNotificationManager.GetStartTimeForPeriod("invalid", testDay);

        // Assert: デフォルト時間（9:00）が返される
        Assert.AreEqual(new DateTime(2024, 1, 15, 9, 0, 0), invalidPeriod);
    }

    [Test]
    public void CompleteSettings_Workflow_AllOperationsSucceed()
    {
        // Arrange: 完全なワークフローテスト
        string testToken = "complete_workflow_test_token_12345678";
        int testCommuteTime = 25;

        // Act: 設定保存ワークフロー
        settingsManager.SaveCanvasApiToken(testToken);
        settingsManager.SaveCommuteTime(testCommuteTime);

        // 設定読み込みと検証
        string savedToken = settingsManager.GetCanvasApiToken();
        int savedCommuteTime = settingsManager.GetCommuteTime();
        string maskedToken = settingsManager.GetMaskedToken();
        string validation = settingsManager.ValidateSettings();
        bool isValid = settingsManager.HasValidSettings();

        // Assert: すべての操作が正しく動作
        Assert.AreEqual(testToken, savedToken);
        Assert.AreEqual(testCommuteTime, savedCommuteTime);
        Assert.AreEqual("comp***5678", maskedToken);
        Assert.AreEqual("", validation);
        Assert.IsTrue(isValid);
    }

    [Test]
    public void SettingsClearance_RemovesAllData()
    {
        // Arrange: データを設定
        settingsManager.SaveCanvasApiToken("test_token_to_clear");
        settingsManager.SaveCommuteTime(30);
        locationManager.RecordCurrentLocation();

        // Act: 設定をクリア
        settingsManager.ClearAllSettings();

        // Assert: データが削除されている
        Assert.AreEqual("", settingsManager.GetCanvasApiToken());
        Assert.AreEqual(20, settingsManager.GetCommuteTime()); // デフォルト値に戻る
        Assert.AreEqual("未設定", settingsManager.GetMaskedToken());
        Assert.IsFalse(settingsManager.HasValidSettings());
    }
}