"""
監視・メトリクス収集エンドポイント
システムの健全性とパフォーマンスを監視
"""

import os
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from structured_logging import metrics_collector, structured_logger, EventType
from memory_cache import cache_manager
from config import Config, get_logger

logger = get_logger(__name__)


@dataclass
class SystemMetrics:
    """システムメトリクス"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_free_gb: float
    process_count: int
    uptime_seconds: float


@dataclass
class ApplicationMetrics:
    """アプリケーションメトリクス"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    cache_hit_rate: float
    active_connections: int


class HealthChecker:
    """健全性チェッククラス"""
    
    def __init__(self):
        self.start_time = time.time()
        self.last_check = None
        self.health_status = "healthy"
        self.health_checks = {
            "database": self._check_cache,
            "external_apis": self._check_external_apis,
            "memory": self._check_memory_usage,
            "disk": self._check_disk_usage,
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """総合的な健全性ステータスを取得"""
        try:
            check_results = {}
            overall_status = "healthy"
            
            # 各チェックを実行
            for check_name, check_func in self.health_checks.items():
                try:
                    result = check_func()
                    check_results[check_name] = result
                    
                    if not result.get("healthy", True):
                        overall_status = "unhealthy"
                        
                except Exception as e:
                    check_results[check_name] = {
                        "healthy": False,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                    overall_status = "unhealthy"
            
            self.health_status = overall_status
            self.last_check = datetime.now()
            
            # ヘルスチェック結果をログに記録
            structured_logger.info(
                EventType.PERFORMANCE_METRIC,
                f"Health check completed: {overall_status}",
                metadata={
                    "health_status": overall_status,
                    "check_results": check_results
                }
            )
            
            return {
                "status": overall_status,
                "timestamp": self.last_check.isoformat(),
                "uptime_seconds": time.time() - self.start_time,
                "checks": check_results
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def _check_cache(self) -> Dict[str, Any]:
        """キャッシュシステムの健全性チェック"""
        try:
            cache_stats = cache_manager.get_cache_stats()
            
            # キャッシュの健全性評価
            healthy = True
            issues = []
            
            # メモリ使用量チェック
            for cache_name, stats in cache_stats.items():
                if "cache_size_mb" in stats and stats["cache_size_mb"] > 100:  # 100MB制限
                    healthy = False
                    issues.append(f"{cache_name}: メモリ使用量が制限を超過")
            
            return {
                "healthy": healthy,
                "cache_stats": cache_stats,
                "issues": issues,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _check_external_apis(self) -> Dict[str, Any]:
        """外部API接続の健全性チェック"""
        try:
            import requests
            
            # Canvas API基本接続チェック
            canvas_healthy = True
            canvas_error = None
            
            try:
                canvas_url = f"{Config.CANVAS_API_BASE_URL}courses"
                response = requests.get(
                    canvas_url, 
                    headers={"Authorization": f"Bearer {Config.CANVAS_ACCESS_TOKEN}"},
                    timeout=10
                )
                if response.status_code not in [200, 401]:  # 401は認証エラーだが接続は可能
                    canvas_healthy = False
                    canvas_error = f"Unexpected status: {response.status_code}"
            except Exception as e:
                canvas_healthy = False
                canvas_error = str(e)
            
            # OpenAI API基本接続チェック（実際のリクエストは送信しない）
            openai_healthy = bool(Config.OPENAI_API_KEY and len(Config.OPENAI_API_KEY) > 10)
            
            overall_healthy = canvas_healthy and openai_healthy
            
            return {
                "healthy": overall_healthy,
                "canvas_api": {
                    "healthy": canvas_healthy,
                    "error": canvas_error
                },
                "openai_api": {
                    "healthy": openai_healthy,
                    "configured": bool(Config.OPENAI_API_KEY)
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _check_memory_usage(self) -> Dict[str, Any]:
        """メモリ使用量チェック"""
        try:
            memory = psutil.virtual_memory()
            process = psutil.Process()
            
            # 閾値: システム全体80%、プロセス500MB
            system_healthy = memory.percent < 80
            process_memory_mb = process.memory_info().rss / 1024 / 1024
            process_healthy = process_memory_mb < 500
            
            overall_healthy = system_healthy and process_healthy
            
            return {
                "healthy": overall_healthy,
                "system_memory_percent": memory.percent,
                "process_memory_mb": process_memory_mb,
                "system_threshold": 80,
                "process_threshold_mb": 500,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _check_disk_usage(self) -> Dict[str, Any]:
        """ディスク使用量チェック"""
        try:
            disk = psutil.disk_usage('/')
            
            # 閾値: 90%
            healthy = disk.percent < 90
            
            return {
                "healthy": healthy,
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / 1024 / 1024 / 1024,
                "threshold_percent": 90,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


class MetricsCollector:
    """システムメトリクス収集クラス"""
    
    def __init__(self):
        self.start_time = time.time()
    
    def get_system_metrics(self) -> SystemMetrics:
        """システムメトリクスを取得"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # メモリ使用量
            memory = psutil.virtual_memory()
            
            # ディスク使用量
            disk = psutil.disk_usage('/')
            
            # プロセス数
            process_count = len(psutil.pids())
            
            # 稼働時間
            uptime_seconds = time.time() - self.start_time
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / 1024 / 1024,
                memory_available_mb=memory.available / 1024 / 1024,
                disk_percent=disk.percent,
                disk_used_gb=disk.used / 1024 / 1024 / 1024,
                disk_free_gb=disk.free / 1024 / 1024 / 1024,
                process_count=process_count,
                uptime_seconds=uptime_seconds
            )
            
        except Exception as e:
            logger.error(f"System metrics collection failed: {e}")
            raise
    
    def get_application_metrics(self) -> ApplicationMetrics:
        """アプリケーションメトリクスを取得"""
        try:
            # メトリクス収集器から統計を取得
            all_metrics = metrics_collector.get_all_metrics()
            
            # リクエスト統計
            total_requests = metrics_collector.get_counter("api.request.total")
            successful_requests = metrics_collector.get_counter("api.request.success")
            failed_requests = metrics_collector.get_counter("api.request.error")
            
            # レスポンス時間統計
            response_time_stats = metrics_collector.get_metric_stats("api.response_time.timing")
            avg_response_time = response_time_stats.get("avg", 0.0)
            
            # キャッシュヒット率
            cache_hits = metrics_collector.get_counter("cache.hit")
            cache_misses = metrics_collector.get_counter("cache.miss")
            total_cache_requests = cache_hits + cache_misses
            cache_hit_rate = (cache_hits / total_cache_requests * 100) if total_cache_requests > 0 else 0.0
            
            return ApplicationMetrics(
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                avg_response_time_ms=avg_response_time,
                cache_hit_rate=cache_hit_rate,
                active_connections=0  # FastAPIから取得する場合は別途実装
            )
            
        except Exception as e:
            logger.error(f"Application metrics collection failed: {e}")
            raise
    
    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """包括的なメトリクスを取得"""
        try:
            system_metrics = self.get_system_metrics()
            app_metrics = self.get_application_metrics()
            cache_stats = cache_manager.get_cache_stats()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "system": {
                    "cpu_percent": system_metrics.cpu_percent,
                    "memory_percent": system_metrics.memory_percent,
                    "memory_used_mb": system_metrics.memory_used_mb,
                    "memory_available_mb": system_metrics.memory_available_mb,
                    "disk_percent": system_metrics.disk_percent,
                    "disk_used_gb": system_metrics.disk_used_gb,
                    "disk_free_gb": system_metrics.disk_free_gb,
                    "process_count": system_metrics.process_count,
                    "uptime_seconds": system_metrics.uptime_seconds
                },
                "application": {
                    "total_requests": app_metrics.total_requests,
                    "successful_requests": app_metrics.successful_requests,
                    "failed_requests": app_metrics.failed_requests,
                    "avg_response_time_ms": app_metrics.avg_response_time_ms,
                    "cache_hit_rate": app_metrics.cache_hit_rate,
                    "active_connections": app_metrics.active_connections
                },
                "cache": cache_stats,
                "custom_metrics": metrics_collector.get_all_metrics()
            }
            
        except Exception as e:
            logger.error(f"Comprehensive metrics collection failed: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }


# グローバルインスタンス
health_checker = HealthChecker()
system_metrics_collector = MetricsCollector()