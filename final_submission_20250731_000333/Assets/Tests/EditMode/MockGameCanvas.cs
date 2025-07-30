using GameCanvas;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// テスト用のGameCanvasモック実装
/// </summary>
public class MockGameCanvas : IGameCanvasLite
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
    
    public void Save(string key, string value)
    {
        storage[key] = value;
    }
    
    public void Save(string key, float value)
    {
        storage[key] = value;
    }
    
    public void Save(string key, int value)
    {
        storage[key] = value;
    }
    
    public bool TryLoad(string key, out string value)
    {
        if (storage.ContainsKey(key) && storage[key] is string)
        {
            value = (string)storage[key];
            return true;
        }
        value = default(string);
        return false;
    }
    
    public bool TryLoad(string key, out float value)
    {
        if (storage.ContainsKey(key) && storage[key] is float)
        {
            value = (float)storage[key];
            return true;
        }
        value = default(float);
        return false;
    }
    
    public bool TryLoad(string key, out int value)
    {
        if (storage.ContainsKey(key) && storage[key] is int)
        {
            value = (int)storage[key];
            return true;
        }
        value = default(int);
        return false;
    }
    
    // 以下は使用しないメソッドのダミー実装
    public void SetResolution(int width, int height) { }
    public void ClearScreen() { }
    public void SetColor(byte r, byte g, byte b) { }
    public void DrawString(string text, float x, float y) { }
    public void FillRect(GcRect rect) { }
    public void DrawRect(GcRect rect) { }
    public float GetPointerX(int pointerId) => 0f;
    public float GetPointerY(int pointerId) => 0f;
    public int GetPointerFrameCount(int pointerId) => 0;
    public bool TryGetKeyEventAll(GcKeyEventPhase phase, out System.ReadOnlySpan<GcKeyEvent> events) 
    { 
        events = System.ReadOnlySpan<GcKeyEvent>.Empty; 
        return false; 
    }
    
    // その他の必要なプロパティ（ダミー値）
    public int CanvasWidth => 720;
    public int CanvasHeight => 1280;
    public float DeltaTime => 0.016f;
    public float Time => UnityEngine.Time.time;
}