using NUnit.Framework;
using UnityEngine;
using GameCanvas;

/// <summary>
/// SettingsManager の単体テスト
/// </summary>
public class SettingsManagerTests
{
    private MockGameCanvas mockGameCanvas;
    private SettingsManager settingsManager;

    [SetUp]
    public void SetUp()
    {
        mockGameCanvas = new MockGameCanvas();
        settingsManager = new SettingsManager(mockGameCanvas);
    }

    [TearDown]
    public void TearDown()
    {
        settingsManager = null;
        mockGameCanvas = null;
    }

    [Test]
    public void Constructor_ValidGameCanvas_InitializesCorrectly()
    {
        // Act & Assert
        Assert.IsNotNull(settingsManager);
    }

    [Test]
    public void Constructor_NullGameCanvas_ThrowsArgumentNullException()
    {
        // Act & Assert
        Assert.Throws<System.ArgumentNullException>(() => new SettingsManager(null));
    }

    [Test]
    public void SaveCanvasApiToken_ValidToken_SavesSuccessfully()
    {
        // Arrange
        string testToken = "test_token_12345";
        
        // Act
        settingsManager.SaveCanvasApiToken(testToken);
        
        // Assert
        Assert.IsTrue(mockGameCanvas.TryLoad("canvas_api_token", out string savedToken));
        Assert.AreEqual(testToken, savedToken);
    }

    [Test]
    public void SaveCanvasApiToken_NullToken_SavesEmptyString()
    {
        // Act
        settingsManager.SaveCanvasApiToken(null);
        
        // Assert
        Assert.IsTrue(mockGameCanvas.TryLoad("canvas_api_token", out string savedToken));
        Assert.AreEqual("", savedToken);
    }

    [Test]
    public void GetCanvasApiToken_WithSavedToken_ReturnsToken()
    {
        // Arrange
        string testToken = "test_token_67890";
        mockGameCanvas.Save("canvas_api_token", testToken);
        
        // Act
        string result = settingsManager.GetCanvasApiToken();
        
        // Assert
        Assert.AreEqual(testToken, result);
    }

    [Test]
    public void GetCanvasApiToken_NoSavedToken_ReturnsEmptyString()
    {
        // Act
        string result = settingsManager.GetCanvasApiToken();
        
        // Assert
        Assert.AreEqual("", result);
    }

    [Test]
    public void GetMaskedToken_WithToken_ReturnsMaskedVersion()
    {
        // Arrange
        string testToken = "1234567890abcdef";
        mockGameCanvas.Save("canvas_api_token", testToken);
        
        // Act
        string result = settingsManager.GetMaskedToken();
        
        // Assert
        Assert.AreEqual("1234***def", result);
    }

    [Test]
    public void GetMaskedToken_WithShortToken_ReturnsMaskedVersion()
    {
        // Arrange
        string testToken = "short";
        mockGameCanvas.Save("canvas_api_token", testToken);
        
        // Act
        string result = settingsManager.GetMaskedToken();
        
        // Assert
        Assert.AreEqual("***", result);
    }

    [Test]
    public void GetMaskedToken_NoToken_ReturnsNotSet()
    {
        // Act
        string result = settingsManager.GetMaskedToken();
        
        // Assert
        Assert.AreEqual("未設定", result);
    }

    [Test]
    public void SaveCommuteTime_ValidTime_SavesSuccessfully()
    {
        // Arrange
        int testTime = 30;
        
        // Act
        settingsManager.SaveCommuteTime(testTime);
        
        // Assert
        Assert.IsTrue(mockGameCanvas.TryLoad("commute_time", out int savedTime));
        Assert.AreEqual(testTime, savedTime);
    }

    [Test]
    public void SaveCommuteTime_ZeroTime_SavesSuccessfully()
    {
        // Arrange
        int testTime = 0;
        
        // Act
        settingsManager.SaveCommuteTime(testTime);
        
        // Assert
        Assert.IsTrue(mockGameCanvas.TryLoad("commute_time", out int savedTime));
        Assert.AreEqual(testTime, savedTime);
    }

    [Test]
    public void GetCommuteTime_WithSavedTime_ReturnsTime()
    {
        // Arrange
        int testTime = 45;
        mockGameCanvas.Save("commute_time", testTime);
        
        // Act
        int result = settingsManager.GetCommuteTime();
        
        // Assert
        Assert.AreEqual(testTime, result);
    }

    [Test]
    public void GetCommuteTime_NoSavedTime_ReturnsDefaultValue()
    {
        // Act
        int result = settingsManager.GetCommuteTime();
        
        // Assert
        Assert.AreEqual(20, result); // デフォルト値
    }

    [Test]
    public void ValidateSettings_ValidTokenAndTime_ReturnsEmpty()
    {
        // Arrange
        mockGameCanvas.Save("canvas_api_token", "valid_token_12345678901234567890");
        mockGameCanvas.Save("commute_time", 30);
        
        // Act
        string result = settingsManager.ValidateSettings();
        
        // Assert
        Assert.AreEqual("", result);
    }

    [Test]
    public void ValidateSettings_NoToken_ReturnsError()
    {
        // Arrange
        mockGameCanvas.Save("commute_time", 30);
        
        // Act
        string result = settingsManager.ValidateSettings();
        
        // Assert
        Assert.IsTrue(result.Contains("Canvas APIトークン"));
    }

    [Test]
    public void ValidateSettings_ShortToken_ReturnsError()
    {
        // Arrange
        mockGameCanvas.Save("canvas_api_token", "short");
        mockGameCanvas.Save("commute_time", 30);
        
        // Act
        string result = settingsManager.ValidateSettings();
        
        // Assert
        Assert.IsTrue(result.Contains("Canvas APIトークン"));
    }

    [Test]
    public void ValidateSettings_InvalidCommuteTime_ReturnsError()
    {
        // Arrange
        mockGameCanvas.Save("canvas_api_token", "valid_token_12345678901234567890");
        mockGameCanvas.Save("commute_time", -5);
        
        // Act
        string result = settingsManager.ValidateSettings();
        
        // Assert
        Assert.IsTrue(result.Contains("通学時間"));
    }

    [Test]
    public void ValidateSettings_MultipleErrors_ReturnsAllErrors()
    {
        // Arrange (両方とも無効な設定)
        mockGameCanvas.Save("canvas_api_token", "");
        mockGameCanvas.Save("commute_time", -10);
        
        // Act
        string result = settingsManager.ValidateSettings();
        
        // Assert
        Assert.IsTrue(result.Contains("Canvas APIトークン"));
        Assert.IsTrue(result.Contains("通学時間"));
    }

    [Test]
    public void HasValidSettings_ValidSettings_ReturnsTrue()
    {
        // Arrange
        mockGameCanvas.Save("canvas_api_token", "valid_token_12345678901234567890");
        mockGameCanvas.Save("commute_time", 30);
        
        // Act
        bool result = settingsManager.HasValidSettings();
        
        // Assert
        Assert.IsTrue(result);
    }

    [Test]
    public void HasValidSettings_InvalidSettings_ReturnsFalse()
    {
        // Arrange
        mockGameCanvas.Save("canvas_api_token", "short");
        mockGameCanvas.Save("commute_time", 30);
        
        // Act
        bool result = settingsManager.HasValidSettings();
        
        // Assert
        Assert.IsFalse(result);
    }

    [Test]
    public void ClearAllSettings_RemovesAllSavedData()
    {
        // Arrange
        mockGameCanvas.Save("canvas_api_token", "test_token");
        mockGameCanvas.Save("commute_time", 25);
        
        // Act
        settingsManager.ClearAllSettings();
        
        // Assert
        Assert.IsFalse(mockGameCanvas.TryLoad("canvas_api_token", out string _));
        Assert.IsFalse(mockGameCanvas.TryLoad("commute_time", out int _));
    }
}