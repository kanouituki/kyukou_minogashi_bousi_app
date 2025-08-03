"""
parallel_processor.pyのテスト
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import time
import aiohttp

# 環境変数をモックして設定
import os
with patch.dict(os.environ, {
    'CANVAS_ACCESS_TOKEN': 'test_token',
    'OPENAI_API_KEY': 'test_openai_key'
}):
    from parallel_processor import (
        RequestTask,
        ParallelProcessor,
        CanvasParallelFetcher,
        PerformanceProfiler
    )


class TestRequestTask:
    """RequestTaskのテスト"""
    
    def test_request_task_creation(self):
        """RequestTask作成のテスト"""
        task = RequestTask(
            url="https://example.com/api",
            headers={"Authorization": "Bearer token"},
            params={"page": 1},
            method="GET",
            task_id="test_task"
        )
        
        assert task.url == "https://example.com/api"
        assert task.headers == {"Authorization": "Bearer token"}
        assert task.params == {"page": 1}
        assert task.method == "GET"
        assert task.task_id == "test_task"
    
    def test_request_task_defaults(self):
        """RequestTaskのデフォルト値テスト"""
        task = RequestTask(
            url="https://example.com/api",
            headers={"Authorization": "Bearer token"}
        )
        
        assert task.params is None
        assert task.method == "GET"
        assert task.task_id == ""


class TestParallelProcessor:
    """ParallelProcessorのテスト"""
    
    def setup_method(self):
        """各テスト前の初期化"""
        self.processor = ParallelProcessor(max_workers=2, timeout=5)
    
    def teardown_method(self):
        """各テスト後のクリーンアップ"""
        if hasattr(self, 'processor'):
            self.processor.close()
    
    def test_parallel_processor_initialization(self):
        """ParallelProcessor初期化のテスト"""
        processor = ParallelProcessor(max_workers=3, timeout=10)
        
        assert processor.max_workers == 3
        assert processor.timeout == 10
        assert processor.executor is not None
        
        processor.close()
    
    @pytest.mark.asyncio
    async def test_execute_async_requests_success(self):
        """非同期リクエスト成功のテスト"""
        # モックレスポンスを作成
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"success": True, "data": "test"})
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_request.return_value.__aenter__.return_value = mock_response
            
            tasks = [
                RequestTask(
                    url="https://example.com/api1",
                    headers={"Authorization": "Bearer token"},
                    task_id="task1"
                ),
                RequestTask(
                    url="https://example.com/api2",
                    headers={"Authorization": "Bearer token"},
                    task_id="task2"
                )
            ]
            
            results = await self.processor.execute_async_requests(tasks)
            
            assert len(results) == 2
            assert results[0][0] == "task1"
            assert results[0][1]["success"] is True
            assert results[1][0] == "task2"
            assert results[1][1]["success"] is True
    
    @pytest.mark.asyncio
    async def test_execute_async_requests_error(self):
        """非同期リクエストエラーのテスト"""
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_request.side_effect = Exception("Connection error")
            
            tasks = [
                RequestTask(
                    url="https://example.com/api",
                    headers={"Authorization": "Bearer token"},
                    task_id="error_task"
                )
            ]
            
            results = await self.processor.execute_async_requests(tasks)
            
            assert len(results) == 1
            assert results[0][0] == "error_task"
            assert results[0][1]["success"] is False
            assert "Connection error" in results[0][1]["error"]
    
    def test_execute_sync_requests_success(self):
        """同期リクエスト成功のテスト"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": "test"}
        
        with patch('requests.request', return_value=mock_response):
            tasks = [
                RequestTask(
                    url="https://example.com/api",
                    headers={"Authorization": "Bearer token"},
                    task_id="sync_task"
                )
            ]
            
            results = self.processor.execute_sync_requests(tasks)
            
            assert len(results) == 1
            assert results[0][0] == "sync_task"
            assert results[0][1]["success"] is True
    
    def test_execute_sync_requests_timeout(self):
        """同期リクエストタイムアウトのテスト"""
        import requests
        
        with patch('requests.request') as mock_request:
            mock_request.side_effect = requests.Timeout("Request timeout")
            
            tasks = [
                RequestTask(
                    url="https://example.com/api",
                    headers={"Authorization": "Bearer token"},
                    task_id="timeout_task"
                )
            ]
            
            results = self.processor.execute_sync_requests(tasks)
            
            assert len(results) == 1
            assert results[0][0] == "timeout_task"
            assert results[0][1]["success"] is False
            assert results[0][1]["status"] == 408


class TestCanvasParallelFetcher:
    """CanvasParallelFetcherのテスト"""
    
    def setup_method(self):
        """各テスト前の初期化"""
        self.fetcher = CanvasParallelFetcher(
            access_token="test_token",
            base_url="https://test.instructure.com"
        )
    
    def teardown_method(self):
        """各テスト後のクリーンアップ"""
        if hasattr(self, 'fetcher'):
            self.fetcher.close()
    
    def test_canvas_parallel_fetcher_initialization(self):
        """CanvasParallelFetcher初期化のテスト"""
        fetcher = CanvasParallelFetcher(
            access_token="test123",
            base_url="https://custom.instructure.com"
        )
        
        assert fetcher.access_token == "test123"
        assert fetcher.base_url == "https://custom.instructure.com"
        assert "Bearer test123" in fetcher.headers["Authorization"]
        
        fetcher.close()
    
    @pytest.mark.asyncio
    async def test_fetch_all_courses_data_async_success(self):
        """非同期コースデータ取得成功のテスト"""
        # モックレスポンス
        course_response = {
            "data": {"id": 123, "name": "Test Course"},
            "success": True,
            "status": 200
        }
        assignments_response = {
            "data": [{"id": 1, "name": "Test Assignment"}],
            "success": True,
            "status": 200
        }
        
        with patch.object(self.fetcher.processor, 'execute_async_requests') as mock_execute:
            mock_execute.return_value = [
                ("course_123", course_response),
                ("assignments_123", assignments_response)
            ]
            
            result = await self.fetcher.fetch_all_courses_data_async([123])
            
            assert 123 in result
            assert "course_info" in result[123]
            assert "assignments" in result[123]
            assert result[123]["course_info"]["id"] == 123
    
    def test_fetch_all_courses_data_sync_success(self):
        """同期コースデータ取得成功のテスト"""
        # モックレスポンス
        course_response = {
            "id": 456,
            "name": "Sync Test Course"
        }
        
        with patch.object(self.fetcher.processor, 'execute_sync_requests') as mock_execute:
            mock_execute.return_value = [
                ("course_456", {"data": course_response, "success": True})
            ]
            
            result = self.fetcher.fetch_all_courses_data_sync([456])
            
            assert 456 in result
            assert result[456]["id"] == 456
            assert result[456]["name"] == "Sync Test Course"
    
    def test_fetch_all_courses_data_sync_error(self):
        """同期コースデータ取得エラーのテスト"""
        with patch.object(self.fetcher.processor, 'execute_sync_requests') as mock_execute:
            mock_execute.return_value = [
                ("course_789", {"success": False, "error": "API Error"})
            ]
            
            result = self.fetcher.fetch_all_courses_data_sync([789])
            
            assert 789 in result
            assert "error" in result[789]
            assert result[789]["error"] == "API Error"


class TestPerformanceProfiler:
    """PerformanceProfilerのテスト"""
    
    def test_measure_execution_time(self):
        """実行時間測定のテスト"""
        def test_function(delay):
            time.sleep(delay)
            return "completed"
        
        result, execution_time = PerformanceProfiler.measure_execution_time(
            test_function, 0.1
        )
        
        assert result == "completed"
        assert 0.09 <= execution_time <= 0.15  # 多少の誤差を許容
    
    @pytest.mark.asyncio
    async def test_measure_async_execution_time(self):
        """非同期実行時間測定のテスト"""
        async def async_test_function(delay):
            await asyncio.sleep(delay)
            return "async_completed"
        
        result, execution_time = await PerformanceProfiler.measure_async_execution_time(
            async_test_function, 0.1
        )
        
        assert result == "async_completed"
        assert 0.09 <= execution_time <= 0.15  # 多少の誤差を許容
    
    def test_compare_performance(self):
        """パフォーマンス比較のテスト"""
        def sync_function():
            time.sleep(0.05)
            return "sync_result"
        
        async def async_function():
            await asyncio.sleep(0.02)
            return "async_result"
        
        comparison = PerformanceProfiler.compare_performance(
            sync_function, async_function
        )
        
        assert "sync_time" in comparison
        assert "async_time" in comparison
        assert "improvement_percent" in comparison
        assert "faster_method" in comparison
        assert comparison["faster_method"] in ["sync", "async"]


# 統合テスト
class TestParallelProcessingIntegration:
    """並列処理の統合テスト"""
    
    def test_parallel_vs_sequential_performance(self):
        """並列処理と逐次処理のパフォーマンス比較"""
        def mock_request_function(delay=0.1):
            time.sleep(delay)
            return {"status": "ok", "delay": delay}
        
        # 逐次処理のシミュレーション
        start_time = time.time()
        sequential_results = []
        for i in range(3):
            result = mock_request_function(0.05)
            sequential_results.append(result)
        sequential_time = time.time() - start_time
        
        # 並列処理のシミュレーション（ThreadPoolExecutor使用）
        from concurrent.futures import ThreadPoolExecutor
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(mock_request_function, 0.05) for _ in range(3)]
            parallel_results = [future.result() for future in futures]
        parallel_time = time.time() - start_time
        
        # 並列処理の方が高速であることを確認
        assert parallel_time < sequential_time
        assert len(parallel_results) == len(sequential_results)
    
    def test_error_handling_in_parallel_processing(self):
        """並列処理でのエラーハンドリングテスト"""
        processor = ParallelProcessor(max_workers=2)
        
        def failing_request():
            raise Exception("Simulated failure")
        
        def success_request():
            return {"status": "success"}
        
        with patch('requests.request') as mock_request:
            # 1つ目は失敗、2つ目は成功
            mock_request.side_effect = [
                Exception("Simulated failure"),
                Mock(status_code=200, json=lambda: {"status": "success"})
            ]
            
            tasks = [
                RequestTask(
                    url="https://example.com/fail",
                    headers={},
                    task_id="fail_task"
                ),
                RequestTask(
                    url="https://example.com/success",
                    headers={},
                    task_id="success_task"
                )
            ]
            
            results = processor.execute_sync_requests(tasks)
            
            # 失敗したタスクと成功したタスクの両方が結果に含まれることを確認
            assert len(results) == 2
            
            # 結果をタスクIDでソート
            results_dict = {task_id: result for task_id, result in results}
            
            assert not results_dict["fail_task"]["success"]
            assert results_dict["success_task"]["success"]
        
        processor.close()