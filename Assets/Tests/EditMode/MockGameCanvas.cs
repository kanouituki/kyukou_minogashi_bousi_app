using GameCanvas;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// テスト用のGameCanvasモック実装
/// </summary>
public class MockGameCanvas : IGameCanvas
{
    private Dictionary<string, object> storage = new Dictionary<string, object>();
    
    // テスト用の設定可能なプロパティ
    public bool HasGeolocationPermission { get; set; } = true;
    public bool HasGeolocationUpdate { get; set; } = false;
    public float GeolocationLastLatitude { get; set; } = 35.685410f;
    public float GeolocationLastLongitude { get; set; } = 139.752842f;
    
    // 呼び出し回数をトラッキング
    public int StartGeolocationServiceCallCount { get; private set; } = 0;
    
    public void StartGeolocationService()
    {
        StartGeolocationServiceCallCount++;
    }
    
    public void Save<T>(string key, T value)
    {
        storage[key] = value;
    }
    
    public bool TryLoad<T>(string key, out T value)
    {
        if (storage.ContainsKey(key) && storage[key] is T)
        {
            value = (T)storage[key];
            return true;
        }
        value = default(T);
        return false;
    }
    
    // 以下は使用しないメソッドのダミー実装
    public void SetResolution(int width, int height) { }
    public void ClearScreen() { }
    public void SetColor(int r, int g, int b) { }
    public void DrawString(string text, float x, float y) { }
    public void FillRect(GcRect rect) { }
    public void DrawRect(GcRect rect) { }
    public float GetPointerX(int index) => 0f;
    public float GetPointerY(int index) => 0f;
    public int GetPointerFrameCount(int index) => 0;
    public bool TryGetKeyEventAll(GcKeyEventPhase phase, out GcKeyEvent[] keyEvents) 
    { 
        keyEvents = null; 
        return false; 
    }
    
    // その他の必要なプロパティ（ダミー値）
    public int CanvasWidth => 720;
    public int CanvasHeight => 1280;
    public float DeltaTime => 0.016f;
    public float Time => UnityEngine.Time.time;
}