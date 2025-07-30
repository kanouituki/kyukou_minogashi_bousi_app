"""
API検証機能のテスト
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import os
import tempfile

# 環境変数をモックして設定
with patch.dict(os.environ, {
    'CANVAS_ACCESS_TOKEN': 'test_token',
    'OPENAI_API_KEY': 'test_openai_key'
}):
    from api_validation import (
        validate_canvas_token,
        check_rate_limit,
        validate_request_parameters,
        sanitize_error_message,
        log_security_event
    )


class TestValidateCanvasToken:
    """Canvas APIトークン検証のテスト"""
    
    def test_validate_canvas_token_none(self):
        """Noneトークンの検証"""
        is_valid, error = validate_canvas_token(None)
        assert not is_valid
        assert "APIトークンが提供されていません" in error
    
    def test_validate_canvas_token_empty(self):
        """空文字トークンの検証"""
        is_valid, error = validate_canvas_token("")
        assert not is_valid
        assert "APIトークンが提供されていません" in error
    
    def test_validate_canvas_token_too_short(self):
        """短すぎるトークンの検証"""
        is_valid, error = validate_canvas_token("short")
        assert not is_valid
        assert "APIトークンが短すぎます" in error
    
    def test_validate_canvas_token_invalid_characters(self):
        """無効な文字を含むトークンの検証"""
        # 32文字以上で無効な文字を含むトークン
        is_valid, error = validate_canvas_token("invalid_token_with_spaces_and_symbols!@#$")
        assert not is_valid
        assert "APIトークンに無効な文字が含まれています" in error
    
    def test_validate_canvas_token_test_pattern(self):
        """テストパターンの検証"""
        # testで始まる無効なパターン
        test_token = "test" + "a" * 32  # 36文字のtestで始まるトークン
        is_valid, error = validate_canvas_token(test_token)
        assert not is_valid
        assert "無効なAPIトークンパターンです" in error
    
    def test_validate_canvas_token_valid(self):
        """有効なトークンの検証"""
        # 実際のCanvas APIトークンに近い形式（123で始まらない）
        valid_token = "abcd567890abcdef1234567890abcdef12345678"
        is_valid, error = validate_canvas_token(valid_token)
        assert is_valid
        assert error is None


class TestRateLimit:
    """レート制限のテスト"""
    
    def setup_method(self):
        """各テスト前の初期化"""
        # レート制限データをクリア
        if hasattr(check_rate_limit, '_rate_limit_data'):
            check_rate_limit._rate_limit_data.clear()
    
    def test_check_rate_limit_first_request(self):
        """初回リクエストの検証"""
        is_allowed, error = check_rate_limit("test_client", max_requests=5, window_minutes=1)
        assert is_allowed is True
        assert error is None
    
    def test_check_rate_limit_within_limit(self):
        """制限内リクエストの検証"""
        client_id = "test_client_2"
        for i in range(4):
            is_allowed, error = check_rate_limit(client_id, max_requests=5, window_minutes=1)
            assert is_allowed is True
            assert error is None
    
    def test_check_rate_limit_exceeds_limit(self):
        """制限超過リクエストの検証"""
        client_id = "test_client_3"
        # 制限まで送信
        for i in range(5):
            check_rate_limit(client_id, max_requests=5, window_minutes=1)
        
        # 制限超過
        is_allowed, error = check_rate_limit(client_id, max_requests=5, window_minutes=1)
        assert is_allowed is False
        assert "レート制限に達しました" in error
    
    @patch('api_validation.datetime')
    def test_check_rate_limit_window_reset(self, mock_datetime):
        """時間窓リセットの検証"""
        client_id = "test_client"
        base_time = datetime(2023, 1, 1, 12, 0, 0)
        
        # 最初の時間
        mock_datetime.now.return_value = base_time
        for i in range(5):
            check_rate_limit(client_id, max_requests=5, window_minutes=1)
        
        # 制限超過
        is_allowed, error = check_rate_limit(client_id, max_requests=5, window_minutes=1)
        assert is_allowed is False
        
        # 時間窓経過後
        mock_datetime.now.return_value = base_time + timedelta(minutes=2)
        is_allowed, error = check_rate_limit(client_id, max_requests=5, window_minutes=1)
        assert is_allowed is True
        assert error is None


class TestSanitizeErrorMessage:
    """エラーメッセージサニタイズのテスト"""
    
    def test_sanitize_error_message_normal_string(self):
        """通常エラーメッセージのサニタイズ"""
        result = sanitize_error_message("Normal error message")
        assert result == "Normal error message"
    
    def test_sanitize_error_message_with_token(self):
        """トークンを含むエラーメッセージのサニタイズ"""
        result = sanitize_error_message("Error with token 1234567890abcdef1234567890abcdef12345678")
        # マスク化されてトークン全体が見えないことを確認
        assert "1234567890abcdef1234567890abcdef12345678" not in result
        assert "***" in result
    
    def test_sanitize_error_message_bearer_token(self):
        """Bearerトークンのサニタイズ"""
        result = sanitize_error_message("Authorization: Bearer abc123def456")
        # Bearer トークンがマスクされることを確認（大文字小文字変換も考慮）
        assert "***" in result
        assert "abc123def456" not in result
    
    def test_sanitize_error_message_empty_string(self):
        """空文字列のサニタイズ"""
        result = sanitize_error_message("")
        assert result == ""


class TestLogSecurityEvent:
    """セキュリティイベントログのテスト"""
    
    def test_log_security_event_masks_sensitive_data(self):
        """機密データがマスクされることの検証"""
        with patch('api_validation.logger') as mock_logger:
            details = {
                "token": "sensitive_token_123",
                "user_id": "user123",
                "request_path": "/api/courses"
            }
            log_security_event("INVALID_TOKEN", details, "192.168.1.1")
            
            # ログが呼び出されたか確認
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args[0][0]
            
            # 機密情報がマスクされているか確認
            assert "***masked***" in call_args
            assert "sensitive_token_123" not in call_args
            assert "user123" in call_args  # 非機密情報は残る


# 統合テスト
class TestAPIValidationIntegration:
    """API検証機能の統合テスト"""
    
    def test_complete_validation_flow_valid(self):
        """有効なリクエストの完全検証フロー"""
        client_ip = "192.168.1.100"
        token = "abcd567890abcdef1234567890abcdef12345678"
        
        # レート制限チェック
        rate_ok, rate_error = check_rate_limit(client_ip, max_requests=10, window_minutes=1)
        assert rate_ok
        assert rate_error is None
        
        # トークン検証
        token_valid, token_error = validate_canvas_token(token)
        assert token_valid
        assert token_error is None
        
        # リクエストパラメータ検証
        params = {"canvas_token": token, "force_refresh": "false"}
        params_valid, params_error = validate_request_parameters(params)
        assert params_valid
        assert params_error is None
    
    def test_complete_validation_flow_invalid_token(self):
        """無効なトークンの完全検証フロー"""
        client_ip = "192.168.1.101"
        token = "invalid"
        
        # レート制限チェック
        rate_ok, rate_error = check_rate_limit(client_ip, max_requests=10, window_minutes=1)
        assert rate_ok
        assert rate_error is None
        
        # トークン検証（失敗）
        token_valid, token_error = validate_canvas_token(token)
        assert not token_valid
        assert token_error is not None
    
    def test_complete_validation_flow_rate_limited(self):
        """レート制限に引っかかる検証フロー"""
        client_ip = "192.168.1.102"
        
        # 制限まで送信
        for i in range(5):
            rate_ok, _ = check_rate_limit(client_ip, max_requests=5, window_minutes=1)
            assert rate_ok
        
        # 制限超過
        rate_ok, rate_error = check_rate_limit(client_ip, max_requests=5, window_minutes=1)
        assert not rate_ok
        assert rate_error is not None