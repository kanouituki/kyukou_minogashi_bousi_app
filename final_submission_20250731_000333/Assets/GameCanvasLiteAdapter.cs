#nullable enable
using GameCanvas;
using System;

/// <summary>
/// IGameCanvasをIGameCanvasLiteに適合させるアダプター
/// </summary>
public class GameCanvasLiteAdapter : IGameCanvasLite
{
    private readonly IGameCanvas gameCanvas;

    public GameCanvasLiteAdapter(IGameCanvas gameCanvas)
    {
        this.gameCanvas = gameCanvas ?? throw new ArgumentNullException(nameof(gameCanvas));
    }

    // 位置情報関連
    public bool HasGeolocationPermission => gameCanvas.HasGeolocationPermission;
    public bool HasGeolocationUpdate => gameCanvas.HasGeolocationUpdate;
    public float GeolocationLastLatitude => gameCanvas.GeolocationLastLatitude;
    public float GeolocationLastLongitude => gameCanvas.GeolocationLastLongitude;
    public void StartGeolocationService() => gameCanvas.StartGeolocationService();

    // データ保存・読み込み
    public void Save(string key, string value) => gameCanvas.Save(in key, value);
    public void Save(string key, float value) => gameCanvas.Save(in key, value);
    public void Save(string key, int value) => gameCanvas.Save(in key, value);
    public bool TryLoad(string key, out string value) => gameCanvas.TryLoad(in key, out value);
    public bool TryLoad(string key, out float value) => gameCanvas.TryLoad(in key, out value);
    public bool TryLoad(string key, out int value) => gameCanvas.TryLoad(in key, out value);

    // UI描画関連
    public void ClearScreen() => gameCanvas.ClearScreen();
    public void SetColor(byte r, byte g, byte b) => gameCanvas.SetColor(in r, in g, in b);
    public void SetResolution(int width, int height) => gameCanvas.SetResolution(width, height);
    public void DrawString(string text, float x, float y) => gameCanvas.DrawString(in text, x, y);
    public void DrawRect(GcRect rect) => gameCanvas.DrawRect(in rect);
    public void FillRect(GcRect rect) => gameCanvas.FillRect(in rect);

    // 入力関連
    public int GetPointerFrameCount(int pointerId) => gameCanvas.GetPointerFrameCount(pointerId);
    public float GetPointerX(int pointerId) => gameCanvas.GetPointerX(pointerId);
    public float GetPointerY(int pointerId) => gameCanvas.GetPointerY(pointerId);
    public bool TryGetKeyEventAll(GcKeyEventPhase phase, out System.ReadOnlySpan<GcKeyEvent> events) 
        => gameCanvas.TryGetKeyEventAll(phase, out events);
}