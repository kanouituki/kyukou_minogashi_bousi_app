"""
cache_manager.py のテスト
"""
import pytest
import os
import json
import tempfile
from unittest.mock import patch, mock_open
from datetime import datetime

from cache_manager import (
    ensure_data_directory,
    load_cache,
    save_cache,
    get_new_announcements,
    update_cache_with_announcements
)
from config import Config


class TestEnsureDataDirectory:
    """ensure_data_directory関数のテスト"""
    
    @patch('cache_manager.os.makedirs')
    @patch('cache_manager.Config.DATA_DIR', '/test/data/dir')
    def test_ensure_data_directory_creates_directory(self, mock_makedirs):
        """データディレクトリの作成をテスト"""
        ensure_data_directory()
        mock_makedirs.assert_called_once_with('/test/data/dir', exist_ok=True)


class TestLoadCache:
    """load_cache関数のテスト"""
    
    @patch('cache_manager.ensure_data_directory')
    @patch('cache_manager.os.path.exists')
    def test_load_cache_file_not_exists(self, mock_exists, mock_ensure):
        """キャッシュファイルが存在しない場合のテスト"""
        mock_exists.return_value = False
        
        result = load_cache()
        
        expected = {
            'last_updated': None,
            'announcements': {}
        }
        assert result == expected
        mock_ensure.assert_called_once()
    
    @patch('cache_manager.ensure_data_directory')
    @patch('cache_manager.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"last_updated": "2023-01-01", "announcements": {"123": []}}')
    def test_load_cache_file_exists_valid_json(self, mock_file, mock_exists, mock_ensure):
        """有効なJSONキャッシュファイルの読み込みテスト"""
        mock_exists.return_value = True
        
        result = load_cache()
        
        expected = {
            "last_updated": "2023-01-01",
            "announcements": {"123": []}
        }
        assert result == expected
        mock_ensure.assert_called_once()
    
    @patch('cache_manager.ensure_data_directory')
    @patch('cache_manager.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    @patch('cache_manager.logger')
    def test_load_cache_invalid_json(self, mock_logger, mock_file, mock_exists, mock_ensure):
        """無効なJSONキャッシュファイルの処理テスト"""
        mock_exists.return_value = True
        
        result = load_cache()
        
        # デフォルト値が返されることを確認
        expected = {
            'last_updated': None,
            'announcements': {}
        }
        assert result == expected
        mock_logger.error.assert_called()


class TestSaveCache:
    """save_cache関数のテスト"""
    
    @patch('cache_manager.ensure_data_directory')
    @patch('builtins.open', new_callable=mock_open)
    @patch('cache_manager.json.dump')
    def test_save_cache_success(self, mock_json_dump, mock_file, mock_ensure):
        """キャッシュの正常保存テスト"""
        test_cache = {
            'last_updated': '2023-01-01T00:00:00',
            'announcements': {'123': []}
        }
        
        save_cache(test_cache)
        
        mock_ensure.assert_called_once()
        mock_file.assert_called_once()
        mock_json_dump.assert_called_once()
    
    @patch('cache_manager.ensure_data_directory')
    @patch('builtins.open', side_effect=IOError("Write error"))
    @patch('cache_manager.logger')
    def test_save_cache_io_error(self, mock_logger, mock_file, mock_ensure):
        """キャッシュ保存時のIOエラーテスト"""
        test_cache = {'test': 'data'}
        
        save_cache(test_cache)
        
        mock_logger.error.assert_called()


class TestGetNewAnnouncements:
    """get_new_announcements関数のテスト"""
    
    def test_get_new_announcements_empty_cache(self):
        """空のキャッシュでの新規お知らせ取得テスト"""
        course_id = '123'
        announcements = [
            {'id': 'ann1', 'title': 'Test 1'},
            {'id': 'ann2', 'title': 'Test 2'}
        ]
        cache = {'announcements': {}}
        
        result = get_new_announcements(course_id, announcements, cache)
        
        assert result == announcements
    
    def test_get_new_announcements_with_existing_cache(self):
        """既存キャッシュがある場合の新規お知らせ取得テスト"""
        course_id = 123
        announcements = [
            {'id': 'ann1', 'title': 'Test 1'},
            {'id': 'ann2', 'title': 'Test 2'},
            {'id': 'ann3', 'title': 'Test 3'}
        ]
        cache = {
            'announcements': {
                '123': {
                    'ann1': {'title': 'Test 1', 'updated_at': None},
                    'ann2': {'title': 'Test 2', 'updated_at': None}
                }
            }
        }
        
        result = get_new_announcements(course_id, announcements, cache)
        
        # 新しいお知らせのみが返されることを確認
        expected = [{'id': 'ann3', 'title': 'Test 3'}]
        assert result == expected
    
    def test_get_new_announcements_no_new_announcements(self):
        """新しいお知らせがない場合のテスト"""
        course_id = 123
        announcements = [
            {'id': 'ann1', 'title': 'Test 1'},
            {'id': 'ann2', 'title': 'Test 2'}
        ]
        cache = {
            'announcements': {
                '123': {
                    'ann1': {'title': 'Test 1', 'updated_at': None},
                    'ann2': {'title': 'Test 2', 'updated_at': None}
                }
            }
        }
        
        result = get_new_announcements(course_id, announcements, cache)
        
        assert result == []


class TestUpdateCacheWithAnnouncements:
    """update_cache_with_announcements関数のテスト"""
    
    def test_update_cache_new_course(self):
        """新しいコースのキャッシュ更新テスト"""
        course_id = 123
        announcements = [
            {'id': 'ann1', 'title': 'Test 1'},
            {'id': 'ann2', 'title': 'Test 2'}
        ]
        cache = {'announcements': {}}
        
        update_cache_with_announcements(course_id, announcements, cache)
        
        assert '123' in cache['announcements']
        assert 'ann1' in cache['announcements']['123']
        assert 'ann2' in cache['announcements']['123']
        assert cache['announcements']['123']['ann1']['title'] == 'Test 1'
        assert 'last_updated' in cache
    
    def test_update_cache_existing_course(self):
        """既存コースのキャッシュ更新テスト"""
        course_id = 123
        announcements = [
            {'id': 'ann2', 'title': 'Test 2'},
            {'id': 'ann3', 'title': 'Test 3'}
        ]
        cache = {
            'announcements': {
                '123': {
                    'ann1': {'title': 'Test 1', 'updated_at': None}
                }
            }
        }
        
        update_cache_with_announcements(course_id, announcements, cache)
        
        # 既存のIDと新しいIDがマージされることを確認
        assert 'ann1' in cache['announcements']['123']
        assert 'ann2' in cache['announcements']['123']
        assert 'ann3' in cache['announcements']['123']
        assert 'last_updated' in cache
    
    def test_update_cache_duplicate_announcements(self):
        """重複するお知らせの処理テスト"""
        course_id = 123
        announcements = [
            {'id': 'ann1', 'title': 'Test 1'},
            {'id': 'ann1', 'title': 'Test 1 Updated'}  # 同じID
        ]
        cache = {'announcements': {}}
        
        update_cache_with_announcements(course_id, announcements, cache)
        
        # 最後の更新が保存される
        assert cache['announcements']['123']['ann1']['title'] == 'Test 1 Updated'