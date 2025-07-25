#nullable enable
using GameCanvas;
using Unity.Mathematics;
using UnityEngine;
using UnityEngine.InputSystem;
using KyukouApp;
using System;

/// <summary>
/// ゲームクラス。
/// 学生が編集すべきソースコードです。
/// </summary>
public sealed class Game : GameBase
{
    // 変数の宣言
    float lat;
    float lng;
    float recorded_lat;
    float recorded_lng;
    float distance;
    string text;
    bool isStartGPS = false;

    // 通学時間入力関連
    string commuteTimeInput = "";
    int savedCommuteTime = 0;
    bool isCommuteInputActive = false;
    TouchScreenKeyboard? commuteKeyboard = null;

    GcRect commute_input_area = new GcRect(50, 650, 300, 40);

    // 休講情報関連
    KyukouApiClient? kyukouApiClient;
    KyukouResponse? lastKyukouResponse;
    string kyukouText = "休講情報: 未取得";
    bool isLoadingKyukou = false;

    // Canvas APIトークン入力関連
    string canvasTokenInput = "";
    string savedCanvasToken = "";
    bool isTokenInputActive = false;
    bool showTokenInput = false;
    TouchScreenKeyboard? mobileKeyboard = null;

    string kyukouNotification = ""; // 画面表示用
    bool hasNotifiedToday = false;  // 一度だけ通知する

    // UIレイアウトの改善
    GcRect record_button = new GcRect(50, 100, 200, 60);
    GcRect kyukou_button = new GcRect(50, 180, 200, 60);
    GcRect token_toggle_button = new GcRect(50, 260, 200, 60);
    GcRect token_input_area = new GcRect(50, 750, 400, 50);
    GcRect token_save_button = new GcRect(470, 750, 100, 50);

    /// <summary>
    /// 初期化処理
    /// </summary>
    public override void InitGame()
    {
        gc.SetResolution(720, 1280);
        lat = 35.685410f;
        lng = 139.752842f;
        text = "取得中";

        // 休講情報APIクライアントの初期化
        InitializeKyukouApiClient();

        // 保存されたCanvas APIトークンを読み込み
        LoadSavedCanvasToken();

        // 通学時間の保存済みデータ読み込み
        if (!gc.TryLoad("commute_time", out savedCommuteTime))
        {
            savedCommuteTime = 0;
        }
    }

    /// <summary>
    /// 休講情報APIクライアントの初期化
    /// </summary>
    void InitializeKyukouApiClient()
    {
        // KyukouApiClientコンポーネントを追加
        kyukouApiClient = gameObject.AddComponent<KyukouApiClient>();

        // コールバック設定
        kyukouApiClient.OnKyukouReceived += OnKyukouInfoReceived;
        kyukouApiClient.OnApiError += OnKyukouApiError;

        Debug.Log("KyukouApiClient 初期化完了");
    }

    /// <summary>
    /// 保存されたCanvas APIトークンを読み込み
    /// </summary>
    void LoadSavedCanvasToken()
    {
        if (gc.TryLoad("canvas_api_token", out savedCanvasToken))
        {
            Debug.Log("保存されたCanvas APIトークンを読み込みました");
        }
        else
        {
            savedCanvasToken = "";
            Debug.Log("保存されたCanvas APIトークンはありません");
        }
    }

    /// <summary>
    /// 動きなどの更新処理
    /// </summary>
    public override void UpdateGame()
    {
        if (!isStartGPS)
        {
            gc.StartGeolocationService();
            isStartGPS = true;
        }

        if (!gc.HasGeolocationPermission)
        {
            text = "位置情報サービスが無効です";
        }

        if (gc.HasGeolocationUpdate)
        {
            lat = gc.GeolocationLastLatitude;
            lng = gc.GeolocationLastLongitude;
            text = string.Format("緯度: {0}\n経度: {1}", lat, lng);
        }

        if (touch_object(record_button))
        {
            if (gc.GetPointerFrameCount(0) == 1)
            {
                // 現在の緯度経度を直接保存
                gc.Save("recorded_lat", lat);
                gc.Save("recorded_lng", lng);
                
                // 保存した値を読み込んで確認
                gc.TryLoad("recorded_lat", out recorded_lat);
                gc.TryLoad("recorded_lng", out recorded_lng);
                
                text = $"位置を記録しました ({lat:F4}, {lng:F4})";
                Debug.Log($"位置記録: lat={lat}, lng={lng}");
            }
        }

        // 休講情報取得ボタン（タップ時のみ実行）
        if (touch_object(kyukou_button))
        {
            Debug.Log("休講情報ボタンがタッチされました");
            if (gc.GetPointerFrameCount(0) == 1)
            {
                Debug.Log("フレームカウント条件OK");
                if (kyukouApiClient != null && !isLoadingKyukou)
                {
                    kyukouText = "休講情報: 取得中...";
                    isLoadingKyukou = true;
                    // 保存されたトークンがある場合はそれを使用
                    string tokenToUse = !string.IsNullOrEmpty(savedCanvasToken) ? savedCanvasToken : null;
                    kyukouApiClient.GetKyukouInfo(tokenToUse);
                    Debug.Log($"休講情報取得開始 (トークン: {(tokenToUse != null ? "あり" : "なし")})");
                }
                else
                {
                    Debug.Log($"API呼び出し失敗: kyukouApiClient={kyukouApiClient}, isLoadingKyukou={isLoadingKyukou}");
                }
            }
        }

        // Canvas APIトークン設定ボタン
        if (touch_object(token_toggle_button))
        {
            if (gc.GetPointerFrameCount(0) == 1)
            {
                showTokenInput = !showTokenInput;
                isTokenInputActive = false;
                Debug.Log($"トークン入力画面切り替え: {showTokenInput}");
            }
        }

        // テキスト入力処理
        if (showTokenInput)
        {
            HandleTokenInput();
        }

        distance = CalculateDistance(recorded_lat, recorded_lng, lat, lng);

        // 通学時間入力エリア
        if (touch_object(commute_input_area))
        {
            if (gc.GetPointerFrameCount(0) == 1)
            {
                isCommuteInputActive = true;
                Debug.Log("通学時間入力がアクティブになりました");
                
                // モバイルキーボードを開く
                #if UNITY_IOS || UNITY_ANDROID
                commuteKeyboard = TouchScreenKeyboard.Open(commuteTimeInput, TouchScreenKeyboardType.NumberPad, false, false, false);
                #endif
            }
        }

        // 入力中の通学時間にキーボード入力処理
        if (isCommuteInputActive)
        {
            #if UNITY_IOS || UNITY_ANDROID
            // モバイルキーボードからの入力を取得
            if (commuteKeyboard != null)
            {
                if (commuteKeyboard.status == TouchScreenKeyboard.Status.Done)
                {
                    commuteTimeInput = commuteKeyboard.text;
                    SaveCommuteTime();
                    commuteKeyboard = null;
                }
                else if (commuteKeyboard.status == TouchScreenKeyboard.Status.Canceled)
                {
                    isCommuteInputActive = false;
                    commuteKeyboard = null;
                }
                else if (commuteKeyboard.active)
                {
                    commuteTimeInput = commuteKeyboard.text;
                }
            }
            #else
            // PC用のキーボード入力処理
            if (gc.TryGetKeyEventAll(GcKeyEventPhase.Down, out var keyEvents))
            {
                foreach (var keyEvent in keyEvents)
                {
                    if (keyEvent.Key.TryGetChar(out char c) && char.IsDigit(c) && commuteTimeInput.Length < 3)
                    {
                        commuteTimeInput += c;
                    }
                    else if (keyEvent.Key == Key.Backspace && commuteTimeInput.Length > 0)
                    {
                        commuteTimeInput = commuteTimeInput.Substring(0, commuteTimeInput.Length - 1);
                    }
                    else if (keyEvent.Key == Key.Enter)
                    {
                        SaveCommuteTime();
                    }
                    else if (keyEvent.Key == Key.Escape)
                    {
                        isCommuteInputActive = false;
                        commuteTimeInput = "";
                    }
                }
            }
            #endif
        }
    }

    /// <summary>
    /// 描画の処理
    /// </summary>
    public override void DrawGame()
    {
        gc.ClearScreen();
        gc.SetColor(0, 0, 0);
        gc.DrawString(text, 50, 30);

        // 位置記録ボタン
        gc.SetColor(100, 100, 100);
        gc.FillRect(record_button);
        gc.SetColor(255, 255, 255);
        gc.DrawString("位置記録", record_button.Position.x + 10, record_button.Position.y + 30);

        // 休講情報取得ボタン（強制表示）
        gc.SetColor(200, 100, 100);  // 赤色で強制表示
        gc.FillRect(kyukou_button);
        gc.SetColor(255, 255, 255);
        gc.DrawString("休講情報", kyukou_button.Position.x + 10, kyukou_button.Position.y + 30);

        // デバッグ表示は削除

        // 位置情報表示
        gc.SetColor(0, 0, 0);
        gc.DrawString("記録された緯度:" + recorded_lat.ToString(), 50, 350);
        gc.DrawString("記録された経度:" + recorded_lng.ToString(), 50, 380);
        gc.DrawString("現在地までの距離：" + distance.ToString("F1") + "m", 50, 410);

        // 休講情報表示
        gc.DrawString(kyukouText, 50, 450);

        // 休講詳細表示
        if (lastKyukouResponse != null && lastKyukouResponse.cancellations.Length > 0)
        {
            int yOffset = 490;
            gc.DrawString("=== 休講一覧 ===", 50, yOffset);
            yOffset += 30;

            for (int i = 0; i < lastKyukouResponse.cancellations.Length && i < 5; i++) // 最大5件表示
            {
                var cancel = lastKyukouResponse.cancellations[i];
                gc.DrawString($"{cancel.course}", 50, yOffset);
                gc.DrawString($"{cancel.date} {cancel.period}", 50, yOffset + 20);
                yOffset += 50;
            }

            if (lastKyukouResponse.cancellations.Length > 5)
            {
                gc.DrawString($"...他{lastKyukouResponse.cancellations.Length - 5}件", 50, yOffset);
            }
        }

        // Canvas APIトークン設定ボタン
        gc.SetColor(150, 150, 200);
        gc.FillRect(token_toggle_button);
        gc.SetColor(255, 255, 255);
        gc.DrawString("API設定", token_toggle_button.Position.x + 10, token_toggle_button.Position.y + 20);

        // 現在のトークン状態表示
        gc.SetColor(0, 0, 0);
        gc.DrawString($"Canvas API: {GetMaskedToken(savedCanvasToken)}", 50, 490);

        // 通学時間設定ボタン
        DrawCommuteTimeInputUI();
        
        // 休講通知表示
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
        
        // トークン入力UI（表示時のみ）
        if (showTokenInput)
        {
            DrawTokenInputUI();
        }

        CheckKyukouNotification();
    }


    public bool touch_object(GcRect rect)
    {
        float px = gc.GetPointerX(0);
        float py = gc.GetPointerY(0);

        return (rect.Position.x < px && px < rect.Position.x + rect.Size.x) && (rect.Position.y < py && py < rect.Position.y + rect.Size.y);
    }

    float CalculateDistance(float lat1, float lon1, float lat2, float lon2)
    {
        const float R = 6371000f; // 地球の半径（メートル）

        float radLat1 = Mathf.Deg2Rad * lat1;
        float radLat2 = Mathf.Deg2Rad * lat2;
        float dLat = Mathf.Deg2Rad * (lat2 - lat1);
        float dLon = Mathf.Deg2Rad * (lon2 - lon1);

        float a = Mathf.Sin(dLat / 2) * Mathf.Sin(dLat / 2) +
                Mathf.Cos(radLat1) * Mathf.Cos(radLat2) *
                Mathf.Sin(dLon / 2) * Mathf.Sin(dLon / 2);
        float c = 2 * Mathf.Atan2(Mathf.Sqrt(a), Mathf.Sqrt(1 - a));

        return R * c;
    }

    /// <summary>
    /// 休講情報取得成功時のコールバック
    /// </summary>
    void OnKyukouInfoReceived(KyukouResponse response)
    {
        lastKyukouResponse = response;
        isLoadingKyukou = false;

        if (response.summary.total_cancellations > 0)
        {
            kyukouText = $"休講情報: {response.summary.total_cancellations}件の休講があります";

        }
        else
        {
            kyukouText = "休講情報: 本日の休講はありません";
        }

        Debug.Log($"休講情報取得完了: {response.summary.total_cancellations}件");
    }

    /// <summary>
    /// 休講情報取得失敗時のコールバック
    /// </summary>
    void OnKyukouApiError(string errorMessage)
    {
        isLoadingKyukou = false;
        kyukouText = $"休講情報: エラー - {errorMessage}";
        Debug.LogError($"休講情報取得エラー: {errorMessage}");
    }

    /// <summary>
    /// Canvas APIトークン入力処理
    /// </summary>
    void HandleTokenInput()
    {
        // 入力エリアクリック検出
        if (touch_object(token_input_area))
        {
            if (gc.GetPointerFrameCount(0) == 1)
            {
                isTokenInputActive = true;
                Debug.Log("トークン入力がアクティブになりました");
                
                // モバイルキーボードを開く
                #if UNITY_IOS || UNITY_ANDROID
                mobileKeyboard = TouchScreenKeyboard.Open(canvasTokenInput, TouchScreenKeyboardType.Default, false, false, true);
                #endif
            }
        }

        // 保存ボタンクリック検出
        if (touch_object(token_save_button))
        {
            if (gc.GetPointerFrameCount(0) == 1)
            {
                SaveCanvasToken();
            }
        }

        // キーボード入力処理（アクティブ時のみ）
        if (isTokenInputActive)
        {
            #if UNITY_IOS || UNITY_ANDROID
            // モバイルキーボードからの入力を取得
            if (mobileKeyboard != null)
            {
                if (mobileKeyboard.status == TouchScreenKeyboard.Status.Done)
                {
                    canvasTokenInput = mobileKeyboard.text;
                    SaveCanvasToken();
                    mobileKeyboard = null;
                }
                else if (mobileKeyboard.status == TouchScreenKeyboard.Status.Canceled)
                {
                    isTokenInputActive = false;
                    mobileKeyboard = null;
                }
                else if (mobileKeyboard.active)
                {
                    canvasTokenInput = mobileKeyboard.text;
                }
            }
            #else
            ProcessKeyboardInput();
            #endif
        }
    }

    /// <summary>
    /// キーボード入力処理
    /// </summary>
    void ProcessKeyboardInput()
    {
        if (gc.TryGetKeyEventAll(GcKeyEventPhase.Down, out var keyEvents))
        {
            foreach (var keyEvent in keyEvents)
            {
                // 文字入力
                if (keyEvent.Key.TryGetChar(out char c) && canvasTokenInput.Length < 100)
                {
                    canvasTokenInput += c;
                    Debug.Log($"文字入力: {c}");
                }
                // バックスペース
                else if (keyEvent.Key == Key.Backspace && canvasTokenInput.Length > 0)
                {
                    canvasTokenInput = canvasTokenInput.Substring(0, canvasTokenInput.Length - 1);
                    Debug.Log("バックスペース");
                }
                // エンター（保存）
                else if (keyEvent.Key == Key.Enter)
                {
                    SaveCanvasToken();
                }
                // エスケープ（キャンセル）
                else if (keyEvent.Key == Key.Escape)
                {
                    isTokenInputActive = false;
                    canvasTokenInput = "";
                    Debug.Log("入力をキャンセルしました");
                }
            }
        }
    }

    /// <summary>
    /// Canvas APIトークンの保存
    /// </summary>
    void SaveCanvasToken()
    {
        if (!string.IsNullOrEmpty(canvasTokenInput))
        {
            savedCanvasToken = canvasTokenInput;
            gc.Save("canvas_api_token", savedCanvasToken);
            Debug.Log("Canvas APIトークンを保存しました");

            // 入力状態をリセット
            canvasTokenInput = "";
            isTokenInputActive = false;
            showTokenInput = false;
        }
        else
        {
            Debug.Log("空のトークンは保存できません");
        }
    }

    /// <summary>
    /// マスク表示用の文字列生成
    /// </summary>
    string GetMaskedToken(string token)
    {
        if (string.IsNullOrEmpty(token))
            return "未設定";

        return new string('●', Mathf.Min(token.Length, 20)) + (token.Length > 20 ? "..." : "");
    }

    /// <summary>
    /// トークン入力UI描画
    /// </summary>
    void DrawTokenInputUI()
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
            gc.SetColor(255, 255, 200); // アクティブ時は黄色
        }
        else
        {
            gc.SetColor(255, 255, 255); // 非アクティブ時は白
        }
        gc.FillRect(token_input_area);
        gc.SetColor(0, 0, 0);
        gc.DrawRect(token_input_area);

        // 入力中のテキスト表示
        string displayText = canvasTokenInput.Length > 0 ? canvasTokenInput : "クリックして入力開始";
        if (displayText.Length > 30)
        {
            displayText = displayText.Substring(0, 27) + "...";
        }
        gc.DrawString(displayText, token_input_area.Position.x + 5, token_input_area.Position.y + 25);

        // カーソル表示（アクティブ時のみ）
        if (isTokenInputActive && (Time.time * 2) % 2 < 1) // 点滅
        {
            float cursorX = token_input_area.Position.x + 5 + displayText.Length * 8;
            gc.DrawString("|", cursorX, token_input_area.Position.y + 25);
        }

        // 保存ボタン
        gc.SetColor(100, 200, 100);
        gc.FillRect(token_save_button);
        gc.SetColor(255, 255, 255);
        gc.DrawString("保存", token_save_button.Position.x + 30, token_save_button.Position.y + 25);

        // 操作説明
        gc.SetColor(100, 100, 100);
        gc.DrawString("Enter: 保存 / Esc: キャンセル", 40, 820);
    }
    void DrawCommuteTimeInputUI()
    {
        gc.SetColor(0, 0, 0);
        gc.DrawString("通学時間（分）を入力:", 50, 610);

        if (isCommuteInputActive)
            gc.SetColor(255, 255, 200);
        else
            gc.SetColor(255, 255, 255);
        gc.FillRect(commute_input_area);
        gc.SetColor(0, 0, 0);
        gc.DrawRect(commute_input_area);

        string display = isCommuteInputActive == true ? commuteTimeInput : $"{savedCommuteTime}";
        gc.DrawString(display + "分", commute_input_area.Position.x + 10, commute_input_area.Position.y + 12);

        if (isCommuteInputActive && (Time.time * 2) % 2 < 1)
        {
            float cursorX = commute_input_area.Position.x + 10 + display.Length * 8;
            gc.DrawString("|", cursorX, commute_input_area.Position.y + 12);
        }
    }

    void SaveCommuteTime()
    {
        if (int.TryParse(commuteTimeInput, out int result))
        {
            savedCommuteTime = result;
            gc.Save("commute_time", savedCommuteTime);
            commuteTimeInput = "";
            isCommuteInputActive = false;
            Debug.Log($"通学時間を保存: {savedCommuteTime} 分");
        }
        else
        {
            Debug.Log("無効な数値です");
        }
    }

    void CheckKyukouNotification()
    {
        if (lastKyukouResponse == null || lastKyukouResponse.cancellations.Length == 0)
            return;

        if (!gc.HasGeolocationUpdate || hasNotifiedToday)
            return;

        var now = DateTime.Now;
        string today = now.ToString("yyyy-MM-dd");

        foreach (var cancel in lastKyukouResponse.cancellations)
        {
            if (cancel.date != today) continue;

            var startTime = GetStartTimeForPeriod(cancel.period, now);
            if (startTime == DateTime.MinValue) continue;

            // 出発すべき時刻（授業開始 - 通学時間）
            var departTime = startTime.AddMinutes(-savedCommuteTime);

            // 許容範囲 ±5分
            var rangeStart = departTime.AddMinutes(-5);
            var rangeEnd = departTime.AddMinutes(5);

            if (now >= rangeStart && now <= rangeEnd)
            {
                float d = CalculateDistance(recorded_lat, recorded_lng, lat, lng);
                if (d >= 500f)
                {
                    kyukouNotification = $"休講 ({cancel.course})：出発時間です！現在地が500m以上離れています（{d:F1}m）";
                    hasNotifiedToday = true;
                    Debug.Log(kyukouNotification);
                }
            }
        }
    }

    
    DateTime GetStartTimeForPeriod(string period, DateTime day)
    {
        return period switch
        {
            "1" => new DateTime(day.Year, day.Month, day.Day, 9, 25, 0),
            "2" => new DateTime(day.Year, day.Month, day.Day, 11, 10, 0),
            "3" => new DateTime(day.Year, day.Month, day.Day, 13, 0, 0),
            "4" => new DateTime(day.Year, day.Month, day.Day, 14, 45, 0),
            "5" => new DateTime(day.Year, day.Month, day.Day, 16, 30, 0),
            "6" => new DateTime(day.Year, day.Month, day.Day, 18, 0, 0),
            _ => DateTime.MinValue
        };
    }





}
