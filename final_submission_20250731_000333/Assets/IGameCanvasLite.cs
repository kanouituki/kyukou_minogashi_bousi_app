using GameCanvas;
using System;

/// <summary>
/// 管理クラスで実際に使用されるGameCanvas機能のインターフェース
/// 本番とテストで異なる実装を使用可能
/// </summary>
public interface IGameCanvasLite
{
    // 位置情報関連
    bool HasGeolocationPermission { get; }
    bool HasGeolocationUpdate { get; }
    float GeolocationLastLatitude { get; }
    float GeolocationLastLongitude { get; }
    void StartGeolocationService();
    
    // データ保存・読み込み
    void Save(string key, string value);
    void Save(string key, float value);
    void Save(string key, int value);
    bool TryLoad(string key, out string value);
    bool TryLoad(string key, out float value);
    bool TryLoad(string key, out int value);
    
    // UI描画関連
    void ClearScreen();
    void SetColor(byte r, byte g, byte b);
    void SetResolution(int width, int height);
    void DrawString(string text, float x, float y);
    void DrawRect(GcRect rect);
    void FillRect(GcRect rect);
    
    // 入力関連
    int GetPointerFrameCount(int pointerId);
    float GetPointerX(int pointerId);
    float GetPointerY(int pointerId);
    bool TryGetKeyEventAll(GcKeyEventPhase phase, out System.ReadOnlySpan<GcKeyEvent> events);
}