"""
並列処理によるパフォーマンス最適化

複数のCanvas APIリクエストを並列実行し、
レスポンス時間を改善する
"""

import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

from config import get_logger

logger = get_logger(__name__)

@dataclass
class RequestTask:
    """並列実行するリクエストタスク"""
    url: str
    headers: Dict[str, str]
    params: Optional[Dict[str, Any]] = None
    method: str = 'GET'
    task_id: str = ""

class ParallelProcessor:
    """並列処理を管理するクラス"""
    
    def __init__(self, max_workers: int = 5, timeout: int = 30):
        """
        Args:
            max_workers: 最大並列実行数
            timeout: リクエストタイムアウト（秒）
        """
        self.max_workers = max_workers
        self.timeout = timeout
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def execute_async_requests(self, tasks: List[RequestTask]) -> List[Tuple[str, Dict[str, Any]]]:
        """
        非同期でHTTPリクエストを並列実行
        
        Args:
            tasks: 実行するタスクのリスト
            
        Returns:
            List[Tuple[task_id, response_data]]: 結果のリスト
        """
        start_time = time.time()
        results = []
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            # 全タスクを並列実行
            tasks_futures = [
                self._execute_single_async_request(session, task)
                for task in tasks
            ]
            
            # 完了を待機
            completed_results = await asyncio.gather(*tasks_futures, return_exceptions=True)
            
            for i, result in enumerate(completed_results):
                task_id = tasks[i].task_id or f"task_{i}"
                
                if isinstance(result, Exception):
                    logger.error(f"タスク {task_id} でエラー発生: {result}")
                    results.append((task_id, {"error": str(result), "success": False}))
                else:
                    results.append((task_id, result))
        
        execution_time = time.time() - start_time
        logger.info(f"並列処理完了: {len(tasks)}タスク, {execution_time:.2f}秒")
        
        return results
    
    async def _execute_single_async_request(self, session: aiohttp.ClientSession, task: RequestTask) -> Dict[str, Any]:
        """
        単一の非同期HTTPリクエストを実行
        
        Args:
            session: aiohttp セッション
            task: 実行するタスク
            
        Returns:
            Dict[str, Any]: レスポンスデータ
        """
        try:
            async with session.request(
                method=task.method,
                url=task.url,
                headers=task.headers,
                params=task.params
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    return {"data": data, "success": True, "status": response.status}
                else:
                    error_text = await response.text()
                    return {
                        "error": f"HTTP {response.status}: {error_text}",
                        "success": False,
                        "status": response.status
                    }
                    
        except asyncio.TimeoutError:
            return {"error": "リクエストタイムアウト", "success": False, "status": 408}
        except Exception as e:
            return {"error": str(e), "success": False, "status": 500}
    
    def execute_sync_requests(self, tasks: List[RequestTask]) -> List[Tuple[str, Dict[str, Any]]]:
        """
        同期的にHTTPリクエストを並列実行（ThreadPoolExecutor使用）
        
        Args:
            tasks: 実行するタスクのリスト
            
        Returns:
            List[Tuple[task_id, response_data]]: 結果のリスト
        """
        start_time = time.time()
        results = []
        
        # 並列実行
        future_to_task = {
            self.executor.submit(self._execute_single_sync_request, task): task
            for task in tasks
        }
        
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            task_id = task.task_id or f"task_{id(task)}"
            
            try:
                result = future.result()
                results.append((task_id, result))
            except Exception as e:
                logger.error(f"タスク {task_id} でエラー発生: {e}")
                results.append((task_id, {"error": str(e), "success": False}))
        
        execution_time = time.time() - start_time
        logger.info(f"同期並列処理完了: {len(tasks)}タスク, {execution_time:.2f}秒")
        
        return results
    
    def _execute_single_sync_request(self, task: RequestTask) -> Dict[str, Any]:
        """
        単一の同期HTTPリクエストを実行
        
        Args:
            task: 実行するタスク
            
        Returns:
            Dict[str, Any]: レスポンスデータ
        """
        import requests
        
        try:
            response = requests.request(
                method=task.method,
                url=task.url,
                headers=task.headers,
                params=task.params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {"data": response.json(), "success": True, "status": response.status_code}
            else:
                return {
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "success": False,
                    "status": response.status_code
                }
                
        except requests.Timeout:
            return {"error": "リクエストタイムアウト", "success": False, "status": 408}
        except Exception as e:
            return {"error": str(e), "success": False, "status": 500}
    
    def close(self):
        """リソースをクリーンアップ"""
        self.executor.shutdown(wait=True)

class CanvasParallelFetcher:
    """Canvas API専用の並列取得クラス"""
    
    def __init__(self, access_token: str, base_url: str = "https://keio.instructure.com"):
        """
        Args:
            access_token: Canvas APIアクセストークン
            base_url: Canvas LMSのベースURL
        """
        self.access_token = access_token
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        self.processor = ParallelProcessor()
    
    async def fetch_all_courses_data_async(self, course_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        複数のコース情報を並列で取得（非同期）
        
        Args:
            course_ids: 取得するコースIDのリスト
            
        Returns:
            Dict[course_id, course_data]: コースデータの辞書
        """
        tasks = []
        
        for course_id in course_ids:
            # コース情報取得タスク
            course_task = RequestTask(
                url=f"{self.base_url}/api/v1/courses/{course_id}",
                headers=self.headers,
                params={"include[]": ["term", "course_progress"]},
                task_id=f"course_{course_id}"
            )
            tasks.append(course_task)
            
            # 課題情報取得タスク
            assignments_task = RequestTask(
                url=f"{self.base_url}/api/v1/courses/{course_id}/assignments",
                headers=self.headers,
                params={
                    "per_page": 50,
                    "include[]": ["submission"]
                },
                task_id=f"assignments_{course_id}"
            )
            tasks.append(assignments_task)
        
        # 並列実行
        results = await self.processor.execute_async_requests(tasks)
        
        # 結果を整理
        course_data = {}
        for task_id, result in results:
            if "course_" in task_id and result.get("success"):
                course_id = int(task_id.split("_")[1])
                if course_id not in course_data:
                    course_data[course_id] = {}
                course_data[course_id]["course_info"] = result["data"]
            elif "assignments_" in task_id and result.get("success"):
                course_id = int(task_id.split("_")[1])
                if course_id not in course_data:
                    course_data[course_id] = {}
                course_data[course_id]["assignments"] = result["data"]
        
        return course_data
    
    def fetch_all_courses_data_sync(self, course_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        複数のコース情報を並列で取得（同期）
        
        Args:
            course_ids: 取得するコースIDのリスト
            
        Returns:
            Dict[course_id, course_data]: コースデータの辞書
        """
        tasks = []
        
        for course_id in course_ids:
            # コース情報取得タスク
            course_task = RequestTask(
                url=f"{self.base_url}/api/v1/courses/{course_id}",
                headers=self.headers,
                params={"include[]": ["term", "course_progress"]},
                task_id=f"course_{course_id}"
            )
            tasks.append(course_task)
        
        # 並列実行
        results = self.processor.execute_sync_requests(tasks)
        
        # 結果を整理
        course_data = {}
        for task_id, result in results:
            if result.get("success"):
                course_id = int(task_id.split("_")[1])
                course_data[course_id] = result["data"]
            else:
                course_id = int(task_id.split("_")[1])
                course_data[course_id] = {"error": result.get("error")}
        
        return course_data
    
    def close(self):
        """リソースをクリーンアップ"""
        self.processor.close()

# パフォーマンス測定用ユーティリティ
class PerformanceProfiler:
    """パフォーマンス測定クラス"""
    
    @staticmethod
    def measure_execution_time(func, *args, **kwargs):
        """
        関数の実行時間を測定
        
        Returns:
            Tuple[result, execution_time]: 結果と実行時間
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        return result, execution_time
    
    @staticmethod
    async def measure_async_execution_time(async_func, *args, **kwargs):
        """
        非同期関数の実行時間を測定
        
        Returns:
            Tuple[result, execution_time]: 結果と実行時間
        """
        start_time = time.time()
        result = await async_func(*args, **kwargs)
        execution_time = time.time() - start_time
        return result, execution_time
    
    @staticmethod
    def compare_performance(sync_func, async_func, *args, **kwargs):
        """
        同期処理と非同期処理のパフォーマンスを比較
        
        Returns:
            Dict: パフォーマンス比較結果
        """
        # 同期処理測定
        sync_result, sync_time = PerformanceProfiler.measure_execution_time(
            sync_func, *args, **kwargs
        )
        
        # 非同期処理測定
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            async_result, async_time = loop.run_until_complete(
                PerformanceProfiler.measure_async_execution_time(
                    async_func, *args, **kwargs
                )
            )
        finally:
            loop.close()
        
        improvement = ((sync_time - async_time) / sync_time) * 100
        
        return {
            "sync_time": sync_time,
            "async_time": async_time,
            "improvement_percent": improvement,
            "faster_method": "async" if async_time < sync_time else "sync"
        }