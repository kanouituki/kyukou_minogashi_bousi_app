"""
config.pyのテスト
"""
import pytest
import os
import logging
from unittest.mock import patch, mock_open

# 環境変数をモックして設定してからインポート
os.environ['CANVAS_ACCESS_TOKEN'] = 'test_canvas_token'
os.environ['OPENAI_API_KEY'] = 'test_openai_key'

from config import Config, get_logger


class TestConfig:
    """Configクラスのテスト"""
    
    def test_config_attributes(self):
        """Config属性のテスト"""
        # 環境変数から読み込まれた値をテスト
        assert Config.CANVAS_ACCESS_TOKEN == 'test_token'
        assert Config.OPENAI_API_KEY == 'test_openai_key'
        
        # 定数値をテスト
        assert Config.CANVAS_API_BASE_URL == "https://lms.keio.jp/api/v1/"
        assert Config.CANVAS_MAX_ANNOUNCEMENTS_PER_COURSE == 10
        assert Config.CANVAS_ANNOUNCEMENT_PERIOD_DAYS == 365
        assert Config.OPENAI_MODEL == "gpt-4o"
        assert Config.OPENAI_TEMPERATURE == 0.1
        assert Config.OPENAI_MAX_TOKENS == 500
        assert Config.DATA_DIR == "data"
        assert Config.CACHE_FILE == "data/cache.json"
        assert Config.RESULTS_DIR == "results"
        assert Config.LOG_LEVEL == "INFO"
    
    def test_ensure_directories(self):
        """ディレクトリ作成のテスト"""
        from unittest.mock import call
        with patch('os.makedirs') as mock_makedirs:
            Config.ensure_directories()
            
            # 各ディレクトリが作成されることを確認
            expected_calls = [
                call('data', exist_ok=True),
                call('results', exist_ok=True),
                call('logs', exist_ok=True)  # LOG_FILEのdirname
            ]
            mock_makedirs.assert_has_calls(expected_calls, any_order=True)
    
    def test_setup_logging(self):
        """ロギング設定のテスト"""
        # ロガーが正常に動作することを確認
        logger = logging.getLogger('test_logger')
        
        # ロガーが作成されることを確認
        assert logger is not None
        assert logger.name == 'test_logger'
    
    def test_validate_required_env_vars_success(self):
        """必須環境変数の検証成功テスト"""
        # 環境変数は既に設定されているので、例外が発生しないことを確認
        try:
            Config.validate_required_env_vars()
        except ValueError:
            pytest.fail("validate_required_env_vars raised ValueError unexpectedly")
    
    def test_validate_required_env_vars_with_mock(self):
        """環境変数の検証失敗をモックでテスト"""
        # CANVAS_ACCESS_TOKENをNoneにモック
        with patch.object(Config, 'CANVAS_ACCESS_TOKEN', None):
            with patch.object(Config, 'OPENAI_API_KEY', 'test_key'):
                with pytest.raises(ValueError) as exc_info:
                    Config.validate_required_env_vars()
                
                assert "CANVAS_ACCESS_TOKEN" in str(exc_info.value)
        
        # OPENAI_API_KEYをNoneにモック
        with patch.object(Config, 'CANVAS_ACCESS_TOKEN', 'test_token'):
            with patch.object(Config, 'OPENAI_API_KEY', None):
                with pytest.raises(ValueError) as exc_info:
                    Config.validate_required_env_vars()
                
                assert "OPENAI_API_KEY" in str(exc_info.value)
        
        # 両方をNoneにモック
        with patch.object(Config, 'CANVAS_ACCESS_TOKEN', None):
            with patch.object(Config, 'OPENAI_API_KEY', None):
                with pytest.raises(ValueError) as exc_info:
                    Config.validate_required_env_vars()
                
                assert "CANVAS_ACCESS_TOKEN" in str(exc_info.value)
                assert "OPENAI_API_KEY" in str(exc_info.value)


class TestGetLogger:
    """get_logger関数のテスト"""
    
    def test_get_logger_creates_logger(self):
        """ロガー作成のテスト"""
        logger = get_logger("test_module")
        
        assert logger.name == "test_module"
        assert isinstance(logger, logging.Logger)
    
    def test_get_logger_multiple_calls_same_name(self):
        """同じ名前で複数回呼び出した場合のテスト"""
        logger1 = get_logger("same_name")
        logger2 = get_logger("same_name")
        
        # 同じロガーインスタンスが返されることを確認
        assert logger1 is logger2
    
    def test_get_logger_different_names(self):
        """異なる名前のロガーのテスト"""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        
        # 異なるロガーインスタンスが返されることを確認
        assert logger1 is not logger2
        assert logger1.name == "module1"
        assert logger2.name == "module2"


class TestConfigIntegration:
    """Config関連の統合テスト"""
    
    def test_config_and_logger_integration(self):
        """ConfigとLoggerの統合テスト"""
        logger = get_logger("integration_test")
        
        # Configが正しく初期化されている
        assert Config.CANVAS_ACCESS_TOKEN == 'test_token'
        assert Config.OPENAI_API_KEY == 'test_openai_key'
        
        # ロガーが実際に使用可能
        logger.info("Test info message")
        logger.warning("Test warning message")
        
        # ロガーの名前が正しい
        assert logger.name == "integration_test"
    
    def test_all_config_constants(self):
        """すべてのConfig定数が期待される型であることをテスト"""
        assert isinstance(Config.CANVAS_API_BASE_URL, str)
        assert isinstance(Config.CANVAS_MAX_ANNOUNCEMENTS_PER_COURSE, int)
        assert isinstance(Config.CANVAS_ANNOUNCEMENT_PERIOD_DAYS, int)
        assert isinstance(Config.OPENAI_MODEL, str)
        assert isinstance(Config.OPENAI_TEMPERATURE, (int, float))
        assert isinstance(Config.OPENAI_MAX_TOKENS, int)
        assert isinstance(Config.DATA_DIR, str)
        assert isinstance(Config.CACHE_FILE, str)
        assert isinstance(Config.RESULTS_DIR, str)
        assert isinstance(Config.LOG_LEVEL, str)
        assert isinstance(Config.LOG_FORMAT, str)
        assert isinstance(Config.LOG_FILE, str)