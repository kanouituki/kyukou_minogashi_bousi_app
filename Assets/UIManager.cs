#nullable enable
using GameCanvas;
using UnityEngine;
using UnityEngine.InputSystem;
using System;
using KyukouApp;

/// <summary>
/// UI管理クラス
/// 画面描画、ユーザー入力処理、キーボード入力を担当
/// </summary>
public class UIManager
{
    private readonly IGameCanvasLite gc;
    
    // UI要素の位置とサイズ
    private readonly GcRect recordButton = new GcRect(50, 100, 200, 60);
    private readonly GcRect kyukouButton = new GcRect(50, 180, 200, 60);
    private readonly GcRect tokenToggleButton = new GcRect(50, 260, 200, 60);
    private readonly GcRect tokenInputArea = new GcRect(50, 750, 400, 50);
    private readonly GcRect tokenSaveButton = new GcRect(470, 750, 100, 50);
    private readonly GcRect commuteInputArea = new GcRect(50, 650, 300, 40);
    
    // 入力状態
    private string tokenInput = "";
    private string commuteInput = "";
    private bool isTokenInputActive = false;
    private bool isCommuteInputActive = false;
    private bool showTokenInput = false;
    
    // モバイルキーボード
    private TouchScreenKeyboard? tokenKeyboard = null;
    private TouchScreenKeyboard? commuteKeyboard = null;
    
    // UIイベント
    public event Action? OnRecordButtonClicked;
    public event Action? OnKyukouButtonClicked;
    public event Action? OnTokenToggleClicked;
    public event Action<string>? OnTokenSaved;
    public event Action<int>? OnCommuteTimeSaved;
    
    public UIManager(IGameCanvasLite gameCanvas)
    {
        gc = gameCanvas ?? throw new ArgumentNullException(nameof(gameCanvas));
    }
    
    /// <summary>
    /// トークン入力画面の表示状態
    /// </summary>
    public bool ShowTokenInput
    {
        get => showTokenInput;
        set
        {
            showTokenInput = value;
            if (!value)
            {
                isTokenInputActive = false;
                tokenInput = "";
            }
        }
    }
    
    /// <summary>
    /// ユーザー入力を処理（毎フレーム呼び出し）
    /// </summary>
    public void HandleInput()
    {
        HandleButtonClicks();
        HandleTextInput();
    }
    
    /// <summary>
    /// メイン画面を描画
    /// </summary>
    public void DrawMainScreen(string locationText, LocationManager? locationManager, 
                              string kyukouText, KyukouResponse? kyukouResponse, 
                              string canvasTokenStatus, string kyukouNotification)
    {
        gc.ClearScreen();
        
        // 位置情報表示
        gc.SetColor(0, 0, 0);
        gc.DrawString(locationText, 50, 30);
        
        // ボタン描画
        DrawButtons();
        
        // 位置情報詳細表示
        DrawLocationInfo(locationManager);
        
        // 休講情報表示
        DrawKyukouInfo(kyukouText, kyukouResponse);
        
        // API設定状態表示
        gc.SetColor(0, 0, 0);
        gc.DrawString($"Canvas API: {canvasTokenStatus}", 50, 490);
        
        // 通学時間入力UI
        DrawCommuteTimeInput();
        
        // 休講通知表示
        DrawKyukouNotification(kyukouNotification);
        
        // トークン入力UI（表示時のみ）
        if (showTokenInput)
        {
            DrawTokenInputUI();
        }
    }
    
    /// <summary>
    /// ボタンクリック処理
    /// </summary>
    private void HandleButtonClicks()
    {
        if (IsTouchingObject(recordButton) && gc.GetPointerFrameCount(0) == 1)
        {
            OnRecordButtonClicked?.Invoke();
        }
        
        if (IsTouchingObject(kyukouButton) && gc.GetPointerFrameCount(0) == 1)
        {
            OnKyukouButtonClicked?.Invoke();
        }
        
        if (IsTouchingObject(tokenToggleButton) && gc.GetPointerFrameCount(0) == 1)
        {
            OnTokenToggleClicked?.Invoke();
        }
        
        // 通学時間入力エリア
        if (IsTouchingObject(commuteInputArea) && gc.GetPointerFrameCount(0) == 1)
        {
            StartCommuteInput();
        }
        
        // トークン入力関連
        if (showTokenInput)
        {
            if (IsTouchingObject(tokenInputArea) && gc.GetPointerFrameCount(0) == 1)
            {
                StartTokenInput();
            }
            
            if (IsTouchingObject(tokenSaveButton) && gc.GetPointerFrameCount(0) == 1)
            {
                SaveTokenInput();
            }
        }
    }
    
    /// <summary>
    /// テキスト入力処理
    /// </summary>
    private void HandleTextInput()
    {
        HandleTokenTextInput();
        HandleCommuteTextInput();
    }
    
    /// <summary>
    /// トークン入力処理
    /// </summary>
    private void HandleTokenTextInput()
    {
        if (!isTokenInputActive) return;
        
        #if UNITY_IOS || UNITY_ANDROID
        HandleMobileTokenInput();
        #else
        HandlePCTokenInput();
        #endif
    }
    
    /// <summary>
    /// 通学時間入力処理
    /// </summary>
    private void HandleCommuteTextInput()
    {
        if (!isCommuteInputActive) return;
        
        #if UNITY_IOS || UNITY_ANDROID
        HandleMobileCommuteInput();
        #else
        HandlePCCommuteInput();
        #endif
    }
    
    /// <summary>
    /// モバイル用トークン入力
    /// </summary>
    private void HandleMobileTokenInput()
    {
        if (tokenKeyboard != null)
        {
            if (tokenKeyboard.status == TouchScreenKeyboard.Status.Done)
            {
                tokenInput = tokenKeyboard.text;
                SaveTokenInput();
                tokenKeyboard = null;
            }
            else if (tokenKeyboard.status == TouchScreenKeyboard.Status.Canceled)
            {
                isTokenInputActive = false;
                tokenKeyboard = null;
            }
            else if (tokenKeyboard.active)
            {
                tokenInput = tokenKeyboard.text;
            }
        }
    }
    
    /// <summary>
    /// PC用トークン入力
    /// </summary>
    private void HandlePCTokenInput()
    {
        if (gc.TryGetKeyEventAll(GcKeyEventPhase.Down, out var keyEvents))
        {
            foreach (var keyEvent in keyEvents)
            {
                // Ctrl+V でクリップボードから貼り付け
                if ((keyEvent.Key == Key.V) && (Input.GetKey(KeyCode.LeftControl) || Input.GetKey(KeyCode.RightControl)))
                {
                    string clipboardText = GUIUtility.systemCopyBuffer;
                    if (!string.IsNullOrEmpty(clipboardText))
                    {
                        tokenInput = clipboardText;
                    }
                }
                // Ctrl+A で全選択
                else if ((keyEvent.Key == Key.A) && (Input.GetKey(KeyCode.LeftControl) || Input.GetKey(KeyCode.RightControl)))
                {
                    tokenInput = "";
                }
                // 通常の文字入力
                else if (keyEvent.Key.TryGetChar(out char c) && 
                        (char.IsLetterOrDigit(c) || char.IsPunctuation(c) || char.IsSymbol(c)) && 
                        tokenInput.Length < 100)
                {
                    tokenInput += c;
                }
                else if (keyEvent.Key == Key.Backspace && tokenInput.Length > 0)
                {
                    tokenInput = tokenInput.Substring(0, tokenInput.Length - 1);
                }
                else if (keyEvent.Key == Key.Enter)
                {
                    SaveTokenInput();
                }
                else if (keyEvent.Key == Key.Escape)
                {
                    isTokenInputActive = false;
                    tokenInput = "";
                }
            }
        }
    }
    
    /// <summary>
    /// モバイル用通学時間入力
    /// </summary>
    private void HandleMobileCommuteInput()
    {
        if (commuteKeyboard != null)
        {
            if (commuteKeyboard.status == TouchScreenKeyboard.Status.Done)
            {
                commuteInput = commuteKeyboard.text;
                SaveCommuteInput();
                commuteKeyboard = null;
            }
            else if (commuteKeyboard.status == TouchScreenKeyboard.Status.Canceled)
            {
                isCommuteInputActive = false;
                commuteKeyboard = null;
            }
            else if (commuteKeyboard.active)
            {
                commuteInput = commuteKeyboard.text;
            }
        }
    }
    
    /// <summary>
    /// PC用通学時間入力
    /// </summary>
    private void HandlePCCommuteInput()
    {
        if (gc.TryGetKeyEventAll(GcKeyEventPhase.Down, out var keyEvents))
        {
            foreach (var keyEvent in keyEvents)
            {
                if (keyEvent.Key.TryGetChar(out char c) && char.IsDigit(c) && commuteInput.Length < 3)
                {
                    commuteInput += c;
                }
                else if (keyEvent.Key == Key.Backspace && commuteInput.Length > 0)
                {
                    commuteInput = commuteInput.Substring(0, commuteInput.Length - 1);
                }
                else if (keyEvent.Key == Key.Enter)
                {
                    SaveCommuteInput();
                }
                else if (keyEvent.Key == Key.Escape)
                {
                    isCommuteInputActive = false;
                    commuteInput = "";
                }
            }
        }
    }
    
    /// <summary>
    /// ボタン描画
    /// </summary>
    private void DrawButtons()
    {
        // 位置記録ボタン
        gc.SetColor(100, 100, 100);
        gc.FillRect(recordButton);
        gc.SetColor(255, 255, 255);
        gc.DrawString("位置記録", recordButton.Position.x + 10, recordButton.Position.y + 30);
        
        // 休講情報取得ボタン
        gc.SetColor(200, 100, 100);
        gc.FillRect(kyukouButton);
        gc.SetColor(255, 255, 255);
        gc.DrawString("休講情報", kyukouButton.Position.x + 10, kyukouButton.Position.y + 30);
        
        // API設定ボタン
        gc.SetColor(150, 150, 200);
        gc.FillRect(tokenToggleButton);
        gc.SetColor(255, 255, 255);
        gc.DrawString("API設定", tokenToggleButton.Position.x + 10, tokenToggleButton.Position.y + 20);
    }
    
    /// <summary>
    /// 位置情報表示
    /// </summary>
    private void DrawLocationInfo(LocationManager? locationManager)
    {
        gc.SetColor(0, 0, 0);
        if (locationManager != null)
        {
            gc.DrawString($"記録された緯度: {locationManager.RecordedLatitude:F6}", 50, 350);
            gc.DrawString($"記録された経度: {locationManager.RecordedLongitude:F6}", 50, 380);
            float distance = locationManager.GetDistanceFromRecordedLocation();
            gc.DrawString($"現在地までの距離: {distance:F1}m", 50, 410);
        }
    }
    
    /// <summary>
    /// 休講情報表示
    /// </summary>
    private void DrawKyukouInfo(string kyukouText, KyukouResponse? kyukouResponse)
    {
        gc.SetColor(0, 0, 0);
        gc.DrawString(kyukouText, 50, 450);
        
        // 休講詳細表示
        if (kyukouResponse != null && kyukouResponse.cancellations.Length > 0)
        {
            DrawKyukouDetails(kyukouResponse);
        }
    }
    
    /// <summary>
    /// 休講詳細表示
    /// </summary>
    private void DrawKyukouDetails(KyukouResponse kyukouResponse)
    {
        int yOffset = 720;
        gc.DrawString("=== 休講一覧 ===", 50, yOffset);
        yOffset += 30;
        
        for (int i = 0; i < kyukouResponse.cancellations.Length && i < 5; i++)
        {
            var cancel = kyukouResponse.cancellations[i];
            gc.DrawString($"{cancel.course}", 50, yOffset);
            gc.DrawString($"    {cancel.date} {cancel.period}", 50, yOffset + 20);
            yOffset += 50;
        }
        
        if (kyukouResponse.cancellations.Length > 5)
        {
            gc.DrawString($"...他{kyukouResponse.cancellations.Length - 5}件", 50, yOffset);
        }
    }
    
    /// <summary>
    /// 通学時間入力UI描画
    /// </summary>
    private void DrawCommuteTimeInput()
    {
        gc.SetColor(0, 0, 0);
        gc.DrawString("通学時間（分）を入力:", 50, 610);
        
        if (isCommuteInputActive)
            gc.SetColor(255, 255, 200);
        else
            gc.SetColor(255, 255, 255);
        gc.FillRect(commuteInputArea);
        gc.SetColor(0, 0, 0);
        gc.DrawRect(commuteInputArea);
        
        string display = isCommuteInputActive ? commuteInput : "0";
        gc.DrawString(display + "分", commuteInputArea.Position.x + 10, commuteInputArea.Position.y + 12);
        
        if (isCommuteInputActive && (Time.time * 2) % 2 < 1)
        {
            float cursorX = commuteInputArea.Position.x + 10 + display.Length * 8;
            gc.DrawString("|", cursorX, commuteInputArea.Position.y + 12);
        }
    }
    
    /// <summary>
    /// 休講通知表示
    /// </summary>
    private void DrawKyukouNotification(string kyukouNotification)
    {
        if (!string.IsNullOrEmpty(kyukouNotification))
        {
            gc.SetColor(255, 0, 0);
            gc.DrawString(kyukouNotification, 50, 550);
        }
        else
        {
            gc.SetColor(0, 0, 0);
            gc.DrawString("休講予定はありません", 50, 550);
        }
    }
    
    /// <summary>
    /// トークン入力UI描画
    /// </summary>
    private void DrawTokenInputUI()
    {
        // 背景
        gc.SetColor(240, 240, 240);
        gc.FillRect(new GcRect(30, 700, 550, 150));
        
        // タイトル
        gc.SetColor(0, 0, 0);
        gc.DrawString("Canvas APIトークン入力:", 40, 720);
        
        // 入力フィールド
        if (isTokenInputActive)
        {
            gc.SetColor(255, 255, 200);
        }
        else
        {
            gc.SetColor(255, 255, 255);
        }
        gc.FillRect(tokenInputArea);
        gc.SetColor(0, 0, 0);
        gc.DrawRect(tokenInputArea);
        
        // 入力中のテキスト表示
        string displayText = tokenInput.Length > 0 ? tokenInput : "クリックして入力開始";
        if (displayText.Length > 30)
        {
            displayText = displayText.Substring(0, 27) + "...";
        }
        gc.DrawString(displayText, tokenInputArea.Position.x + 5, tokenInputArea.Position.y + 25);
        
        // カーソル表示
        if (isTokenInputActive && (Time.time * 2) % 2 < 1)
        {
            float cursorX = tokenInputArea.Position.x + 5 + displayText.Length * 8;
            gc.DrawString("|", cursorX, tokenInputArea.Position.y + 25);
        }
        
        // 保存ボタン
        gc.SetColor(100, 200, 100);
        gc.FillRect(tokenSaveButton);
        gc.SetColor(255, 255, 255);
        gc.DrawString("保存", tokenSaveButton.Position.x + 30, tokenSaveButton.Position.y + 25);
        
        // 操作説明
        gc.SetColor(100, 100, 100);
        gc.DrawString("Enter: 保存 / Esc: キャンセル / Ctrl+V: 貼り付け", 40, 820);
    }
    
    /// <summary>
    /// オブジェクトタッチ判定
    /// </summary>
    private bool IsTouchingObject(GcRect rect)
    {
        float px = gc.GetPointerX(0);
        float py = gc.GetPointerY(0);
        
        return (rect.Position.x < px && px < rect.Position.x + rect.Size.x) && 
               (rect.Position.y < py && py < rect.Position.y + rect.Size.y);
    }
    
    /// <summary>
    /// トークン入力開始
    /// </summary>
    private void StartTokenInput()
    {
        isTokenInputActive = true;
        
        #if UNITY_IOS || UNITY_ANDROID
        tokenKeyboard = TouchScreenKeyboard.Open(tokenInput, TouchScreenKeyboardType.Default, false, false, true);
        #endif
    }
    
    /// <summary>
    /// 通学時間入力開始
    /// </summary>
    private void StartCommuteInput()
    {
        isCommuteInputActive = true;
        
        #if UNITY_IOS || UNITY_ANDROID
        commuteKeyboard = TouchScreenKeyboard.Open(commuteInput, TouchScreenKeyboardType.NumberPad, false, false, false);
        #endif
    }
    
    /// <summary>
    /// トークン入力保存
    /// </summary>
    private void SaveTokenInput()
    {
        if (!string.IsNullOrEmpty(tokenInput))
        {
            OnTokenSaved?.Invoke(tokenInput);
            tokenInput = "";
            isTokenInputActive = false;
            showTokenInput = false;
        }
    }
    
    /// <summary>
    /// 通学時間入力保存
    /// </summary>
    private void SaveCommuteInput()
    {
        if (int.TryParse(commuteInput, out int result))
        {
            OnCommuteTimeSaved?.Invoke(result);
            commuteInput = "";
            isCommuteInputActive = false;
        }
    }
}