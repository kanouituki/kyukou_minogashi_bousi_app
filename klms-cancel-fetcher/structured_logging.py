"""
構造化ログシステム
JSON形式での構造化ログ出力とメトリクス収集
"""

import json
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, asdict
from functools import wraps
import logging

from config import get_logger

# 基本ロガー
base_logger = get_logger(__name__)


class LogLevel(str, Enum):
    """ログレベル定義"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventType(str, Enum):
    """イベントタイプ定義"""
    API_REQUEST = "api_request"
    API_RESPONSE = "api_response"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    ANALYSIS_START = "analysis_start"
    ANALYSIS_COMPLETE = "analysis_complete"
    ERROR_OCCURRED = "error_occurred"
    PERFORMANCE_METRIC = "performance_metric"
    SECURITY_EVENT = "security_event"
    USER_ACTION = "user_action"


@dataclass
class LogEntry:
    """構造化ログエントリ"""
    timestamp: str
    level: LogLevel
    event_type: EventType
    message: str
    service: str = "klms-cancel-fetcher"
    version: str = "1.0.0"
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    duration_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    error_details: Optional[Dict[str, Any]] = None
    
    def to_json(self) -> str:
        """JSON文字列に変換"""
        data = asdict(self)
        # Noneの値を除去
        data = {k: v for k, v in data.items() if v is not None}
        return json.dumps(data, ensure_ascii=False)


class StructuredLogger:
    """構造化ログ出力クラス"""
    
    def __init__(self, service_name: str = "klms-cancel-fetcher"):
        self.service_name = service_name
        self.logger = logging.getLogger(f"{service_name}.structured")
        self._setup_logger()
    
    def _setup_logger(self):
        """ロガーの初期設定"""
        # ハンドラーが既に存在する場合はスキップ
        if self.logger.handlers:
            return
        
        # JSONフォーマッターでハンドラーを設定
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        
        # カスタムフォーマッター（構造化ログ用）
        class StructuredFormatter(logging.Formatter):
            def format(self, record):
                if hasattr(record, 'structured_data'):
                    return record.structured_data
                return super().format(record)
        
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
    
    def log(
        self,
        level: LogLevel,
        event_type: EventType,
        message: str,
        **kwargs
    ):
        """構造化ログを出力"""
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level,
            event_type=event_type,
            message=message,
            service=self.service_name,
            **kwargs
        )
        
        # ログレベルに応じて出力
        log_level_map = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL,
        }
        
        log_record = logging.LogRecord(
            name=self.logger.name,
            level=log_level_map[level],
            pathname="",
            lineno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        log_record.structured_data = entry.to_json()
        
        self.logger.handle(log_record)
    
    def debug(self, event_type: EventType, message: str, **kwargs):
        """DEBUGレベルログ"""
        self.log(LogLevel.DEBUG, event_type, message, **kwargs)
    
    def info(self, event_type: EventType, message: str, **kwargs):
        """INFOレベルログ"""
        self.log(LogLevel.INFO, event_type, message, **kwargs)
    
    def warning(self, event_type: EventType, message: str, **kwargs):
        """WARNINGレベルログ"""
        self.log(LogLevel.WARNING, event_type, message, **kwargs)
    
    def error(self, event_type: EventType, message: str, **kwargs):
        """ERRORレベルログ"""
        self.log(LogLevel.ERROR, event_type, message, **kwargs)
    
    def critical(self, event_type: EventType, message: str, **kwargs):
        """CRITICALレベルログ"""
        self.log(LogLevel.CRITICAL, event_type, message, **kwargs)


class MetricsCollector:
    """メトリクス収集クラス"""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.counters: Dict[str, int] = {}
        self.lock = threading.RLock()
        self.logger = StructuredLogger("metrics")
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """カウンターをインクリメント"""
        with self.lock:
            key = self._build_key(name, tags)
            self.counters[key] = self.counters.get(key, 0) + value
            
            self.logger.info(
                EventType.PERFORMANCE_METRIC,
                f"Counter incremented: {name}",
                metadata={
                    "metric_name": name,
                    "metric_type": "counter",
                    "value": value,
                    "total": self.counters[key],
                    "tags": tags
                }
            )
    
    def record_value(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """値を記録"""
        with self.lock:
            key = self._build_key(name, tags)
            if key not in self.metrics:
                self.metrics[key] = []
            
            self.metrics[key].append(value)
            
            # 最新100件のみ保持
            if len(self.metrics[key]) > 100:
                self.metrics[key] = self.metrics[key][-100:]
            
            self.logger.info(
                EventType.PERFORMANCE_METRIC,
                f"Value recorded: {name}",
                metadata={
                    "metric_name": name,
                    "metric_type": "gauge",
                    "value": value,
                    "tags": tags
                }
            )
    
    def record_timing(self, name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None):
        """実行時間を記録"""
        self.record_value(f"{name}.timing", duration_ms, tags)
    
    def get_counter(self, name: str, tags: Optional[Dict[str, str]] = None) -> int:
        """カウンター値を取得"""
        key = self._build_key(name, tags)
        return self.counters.get(key, 0)
    
    def get_metric_stats(self, name: str, tags: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """メトリクス統計を取得"""
        key = self._build_key(name, tags)
        values = self.metrics.get(key, [])
        
        if not values:
            return {}
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1]
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """全メトリクスを取得"""
        with self.lock:
            return {
                "counters": self.counters.copy(),
                "metrics": {
                    name: self.get_metric_stats(name.split("|")[0], self._parse_tags(name))
                    for name in self.metrics.keys()
                }
            }
    
    def _build_key(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """メトリクスキーを構築"""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}|{tag_str}"
    
    def _parse_tags(self, key: str) -> Optional[Dict[str, str]]:
        """キーからタグを解析"""
        if "|" not in key:
            return None
        
        tag_str = key.split("|", 1)[1]
        tags = {}
        for tag_pair in tag_str.split(","):
            if "=" in tag_pair:
                k, v = tag_pair.split("=", 1)
                tags[k] = v
        return tags if tags else None


class PerformanceTracker:
    """パフォーマンス追跡デコレーター"""
    
    def __init__(self, metrics_collector: MetricsCollector, logger: StructuredLogger):
        self.metrics = metrics_collector
        self.logger = logger
    
    def track_performance(
        self,
        operation_name: str,
        log_start: bool = True,
        log_end: bool = True,
        tags: Optional[Dict[str, str]] = None
    ):
        """パフォーマンス追跡デコレーター"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                correlation_id = f"{operation_name}_{int(start_time * 1000)}"
                
                if log_start:
                    self.logger.info(
                        EventType.ANALYSIS_START,
                        f"Operation started: {operation_name}",
                        correlation_id=correlation_id,
                        metadata={"operation": operation_name, "tags": tags}
                    )
                
                try:
                    # 関数実行
                    result = func(*args, **kwargs)
                    
                    # 成功メトリクス
                    self.metrics.increment_counter(
                        f"{operation_name}.success",
                        tags=tags
                    )
                    
                    # 実行時間記録
                    duration_ms = (time.time() - start_time) * 1000
                    self.metrics.record_timing(operation_name, duration_ms, tags)
                    
                    if log_end:
                        self.logger.info(
                            EventType.ANALYSIS_COMPLETE,
                            f"Operation completed: {operation_name}",
                            correlation_id=correlation_id,
                            duration_ms=duration_ms,
                            metadata={"operation": operation_name, "status": "success", "tags": tags}
                        )
                    
                    return result
                    
                except Exception as e:
                    # エラーメトリクス
                    self.metrics.increment_counter(
                        f"{operation_name}.error",
                        tags=tags
                    )
                    
                    duration_ms = (time.time() - start_time) * 1000
                    
                    self.logger.error(
                        EventType.ERROR_OCCURRED,
                        f"Operation failed: {operation_name}",
                        correlation_id=correlation_id,
                        duration_ms=duration_ms,
                        error_details={
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                            "operation": operation_name
                        },
                        metadata={"tags": tags}
                    )
                    
                    raise
            
            return wrapper
        return decorator


# グローバルインスタンス
structured_logger = StructuredLogger()
metrics_collector = MetricsCollector()
performance_tracker = PerformanceTracker(metrics_collector, structured_logger)

# 使いやすいエイリアス
log = structured_logger
metrics = metrics_collector
track_performance = performance_tracker.track_performance