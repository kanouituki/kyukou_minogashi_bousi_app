"""
gpt_analyzer.py のテスト
"""
import pytest
import json
from unittest.mock import patch, Mock

from gpt_analyzer import analyze_announcement


class TestAnalyzeAnnouncement:
    """analyze_announcement関数のテスト"""
    
    @patch('gpt_analyzer.client')
    def test_analyze_announcement_canceled_class(self, mock_client):
        """休講情報の分析テスト"""
        # Arrange
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = '''```json
{
  "course": "プログラミング基礎",
  "date": "2023-12-01",
  "period": "2限",
  "canceled": true,
  "source": "KLMS",
  "details": "講師の都合により休講"
}
```'''
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        title = "12月1日 プログラミング基礎 休講のお知らせ"
        body = "講師の都合により、12月1日2限のプログラミング基礎は休講いたします。"
        
        # Act
        result = analyze_announcement(title, body)
        
        # Assert
        assert result['canceled'] == True
        assert result['course'] == "プログラミング基礎"
        assert result['date'] == "2023-12-01"
        assert result['period'] == "2限"
        assert result['source'] == "KLMS"
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('gpt_analyzer.client')
    def test_analyze_announcement_not_canceled(self, mock_client):
        """通常のお知らせ（非休講）の分析テスト"""
        # Arrange
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = '''```json
{
  "course": "プログラミング基礎",
  "date": null,
  "period": null,
  "canceled": false,
  "source": "KLMS",
  "details": "課題提出について"
}
```'''
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        title = "課題提出について"
        body = "来週までに課題を提出してください。"
        
        # Act
        result = analyze_announcement(title, body)
        
        # Assert
        assert result['canceled'] == False
        assert result['course'] == "プログラミング基礎"
        assert result['date'] is None
        assert result['period'] is None
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('gpt_analyzer.client')
    @patch('gpt_analyzer.logger')
    def test_analyze_announcement_openai_exception(self, mock_logger, mock_client):
        """OpenAI API例外のテスト"""
        # Arrange
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        title = "テストタイトル"
        body = "テスト本文"
        
        # Act
        result = analyze_announcement(title, body)
        
        # Assert
        assert 'error' in result
        assert result['error'] == "API Error"
        mock_logger.error.assert_called_once()
    
    @patch('gpt_analyzer.client')
    @patch('gpt_analyzer.logger')
    def test_analyze_announcement_invalid_json_response(self, mock_logger, mock_client):
        """無効なJSONレスポンスのテスト"""
        # Arrange
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "This is not valid JSON"
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        title = "テストタイトル"
        body = "テスト本文"
        
        # Act
        result = analyze_announcement(title, body)
        
        # Assert
        assert 'error' in result
        assert 'Expecting value' in result['error']
        mock_logger.error.assert_called_once()
    
    @patch('gpt_analyzer.client')
    def test_analyze_announcement_json_with_markdown(self, mock_client):
        """マークダウンコードブロック付きJSONのテスト"""
        # Arrange
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = '''```json
{
  "course": "数学",
  "date": "2023-12-15",
  "period": "3限",
  "canceled": true,
  "source": "KLMS",
  "details": "期末試験のため休講"
}
```'''
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        title = "期末試験期間の休講について"
        body = "期末試験期間中は通常授業を休講します。"
        
        # Act
        result = analyze_announcement(title, body)
        
        # Assert
        assert result['canceled'] == True
        assert result['course'] == "数学"
        assert result['date'] == "2023-12-15"
        assert result['period'] == "3限"
    
    @patch('gpt_analyzer.client')
    def test_analyze_announcement_empty_response(self, mock_client):
        """空のレスポンスのテスト"""
        # Arrange
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = ""
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        title = "テストタイトル"
        body = "テスト本文"
        
        # Act
        result = analyze_announcement(title, body)
        
        # Assert
        assert 'error' in result
        assert 'Expecting value' in result['error']
    
    @patch('gpt_analyzer.client')
    def test_analyze_announcement_partial_data(self, mock_client):
        """部分的なデータのテスト"""
        # Arrange
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = '''```json
{
  "course": "英語",
  "date": null,
  "period": "1限",
  "canceled": true,
  "source": "KLMS",
  "details": "日程未定の休講"
}
```'''
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        title = "英語 休講のお知らせ"
        body = "1限の英語は休講です。日程は後日連絡します。"
        
        # Act
        result = analyze_announcement(title, body)
        
        # Assert
        assert result['canceled'] == True
        assert result['course'] == "英語"
        assert result['date'] is None  # 日付が不明
        assert result['period'] == "1限"
    
    @patch('gpt_analyzer.client')
    def test_analyze_announcement_prompt_content(self, mock_client):
        """プロンプトの内容が正しく構築されるかのテスト"""
        # Arrange
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = '```json\n{"canceled": false}\n```'
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        title = "テストタイトル"
        body = "テスト本文"
        
        # Act
        analyze_announcement(title, body)
        
        # Assert
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        user_message = messages[0]['content']
        
        # プロンプトにタイトルと本文が含まれていることを確認
        assert title in user_message
        assert body in user_message
        assert "JSON形式" in user_message