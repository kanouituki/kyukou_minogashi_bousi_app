"""
pytest設定ファイル
テスト共通の設定とフィクスチャを定義
"""
import pytest
import tempfile
import os
from unittest.mock import Mock


@pytest.fixture
def temp_log_file():
    """一時的なログファイルのフィクスチャ"""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.log') as f:
        yield f.name
    # クリーンアップ
    if os.path.exists(f.name):
        os.unlink(f.name)


@pytest.fixture
def mock_canvas_response():
    """Canvas API レスポンスのモック"""
    return {
        "id": 12345,
        "name": "テストコース",
        "course_code": "TEST101",
        "enrollments": [{"type": "student"}]
    }


@pytest.fixture(scope="function")
def clean_rate_limit_data():
    """レート制限データをクリーンアップするフィクスチャ"""
    # テスト前にデータをクリア
    from api_validation import check_rate_limit
    if hasattr(check_rate_limit, '_rate_limit_data'):
        check_rate_limit._rate_limit_data.clear()
    
    yield
    
    # テスト後にもクリア
    if hasattr(check_rate_limit, '_rate_limit_data'):
        check_rate_limit._rate_limit_data.clear()


@pytest.fixture
def sample_canvas_token():
    """テスト用の有効なCanvas APIトークン"""
    return "1234567890abcdef1234567890abcdef12345678"


@pytest.fixture
def sample_invalid_token():
    """テスト用の無効なCanvas APIトークン"""
    return "invalid_token"


@pytest.fixture
def sample_client_ip():
    """テスト用のクライアントIP"""
    return "192.168.1.100"