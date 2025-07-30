"""
canvas_api.py のテスト
"""
import pytest
import requests
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

from canvas_api import get_courses, get_announcements
from config import Config


class TestGetCourses:
    """get_courses関数のテスト"""
    
    @patch('canvas_api.requests.get')
    def test_get_courses_success_with_token(self, mock_get):
        """Canvas APIトークン指定でのコース取得成功テスト"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = [
            {'id': 1, 'name': 'Test Course 1'},
            {'id': 2, 'name': 'Test Course 2'}
        ]
        mock_get.return_value = mock_response
        test_token = 'test_token_12345'
        
        # Act
        result = get_courses(test_token)
        
        # Assert
        assert result == [
            {'id': 1, 'name': 'Test Course 1'},
            {'id': 2, 'name': 'Test Course 2'}
        ]
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[1]['headers']['Authorization'] == f'Bearer {test_token}'
    
    @patch('canvas_api.requests.get')
    @patch('canvas_api.Config.CANVAS_ACCESS_TOKEN', 'env_token_12345')
    def test_get_courses_success_with_env_token(self, mock_get):
        """環境変数トークンでのコース取得成功テスト"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = [{'id': 1, 'name': 'Test Course'}]
        mock_get.return_value = mock_response
        
        # Act
        result = get_courses()
        
        # Assert
        assert result == [{'id': 1, 'name': 'Test Course'}]
        call_args = mock_get.call_args
        assert call_args[1]['headers']['Authorization'] == 'Bearer env_token_12345'
    
    @patch('canvas_api.requests.get')
    @patch('canvas_api.logger')
    def test_get_courses_request_exception(self, mock_logger, mock_get):
        """リクエスト例外のテスト"""
        # Arrange
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")
        
        # Act
        result = get_courses('test_token')
        
        # Assert
        assert result is None
        mock_logger.error.assert_called_once()
    
    @patch('canvas_api.requests.get')
    @patch('canvas_api.logger')
    def test_get_courses_http_error(self, mock_logger, mock_get):
        """HTTPエラーのテスト"""
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        # Act
        result = get_courses('test_token')
        
        # Assert
        assert result is None
        mock_logger.error.assert_called_once()


class TestGetAnnouncements:
    """get_announcements関数のテスト"""
    
    @patch('canvas_api.requests.get')
    def test_get_announcements_success_with_token(self, mock_get):
        """Canvas APIトークン指定でのお知らせ取得成功テスト"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                'id': 1,
                'title': 'Test Announcement 1',
                'message': 'Test message 1',
                'posted_at': '2023-01-01T00:00:00Z'
            },
            {
                'id': 2, 
                'title': 'Test Announcement 2',
                'message': 'Test message 2',
                'posted_at': '2023-01-02T00:00:00Z'
            }
        ]
        mock_get.return_value = mock_response
        test_token = 'test_token_12345'
        course_id = 123
        
        # Act
        result = get_announcements(course_id, test_token)
        
        # Assert
        assert len(result) == 2
        assert result[0]['title'] == 'Test Announcement 1'
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[1]['headers']['Authorization'] == f'Bearer {test_token}'
        assert 'announcements' in call_args[0][0]
    
    @patch('canvas_api.requests.get')
    @patch('canvas_api.Config.CANVAS_ACCESS_TOKEN', 'env_token_12345')
    def test_get_announcements_success_with_env_token(self, mock_get):
        """環境変数トークンでのお知らせ取得成功テスト"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = [
            {'id': 1, 'title': 'Test Announcement', 'message': 'Test message'}
        ]
        mock_get.return_value = mock_response
        course_id = 123
        
        # Act
        result = get_announcements(course_id)
        
        # Assert
        assert len(result) == 1
        call_args = mock_get.call_args
        assert call_args[1]['headers']['Authorization'] == 'Bearer env_token_12345'
    
    @patch('canvas_api.requests.get')
    def test_get_announcements_with_date_filtering(self, mock_get):
        """日付フィルタリング付きお知らせ取得テスト"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        course_id = 123
        
        # Act
        result = get_announcements(course_id, 'test_token')
        
        # Assert
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        # start_dateパラメータが含まれていることを確認
        assert 'start_date' in call_args[1]['params']
    
    @patch('canvas_api.requests.get')
    @patch('canvas_api.logger')
    def test_get_announcements_request_exception(self, mock_logger, mock_get):
        """リクエスト例外のテスト"""
        # Arrange
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")
        
        # Act
        result = get_announcements(123, 'test_token')
        
        # Assert
        assert result is None
        mock_logger.error.assert_called_once()
    
    @patch('canvas_api.requests.get')
    @patch('canvas_api.logger')
    def test_get_announcements_http_error(self, mock_logger, mock_get):
        """HTTPエラーのテスト"""
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("403 Forbidden")
        mock_get.return_value = mock_response
        
        # Act
        result = get_announcements(123, 'test_token')
        
        # Assert
        assert result is None
        mock_logger.error.assert_called_once()
    
    @patch('canvas_api.requests.get')
    def test_get_announcements_empty_response(self, mock_get):
        """空のレスポンスのテスト"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        # Act
        result = get_announcements(123, 'test_token')
        
        # Assert
        assert result == []