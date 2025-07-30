"""
インメモリキャッシュシステム
パフォーマンス向上のためのLRUキャッシュとTTLキャッシュ実装
"""

import time
import threading
from typing import Any, Dict, Optional, TypeVar, Generic, Callable
from datetime import datetime, timedelta
from collections import OrderedDict
from functools import wraps
from config import get_logger

logger = get_logger(__name__)

T = TypeVar('T')

class LRUCache(Generic[T]):
    """
    LRU (Least Recently Used) キャッシュ実装
    """
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache: OrderedDict[str, T] = OrderedDict()
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[T]:
        """キーでアイテムを取得"""
        with self.lock:
            if key in self.cache:
                # アクセス時にアイテムを最新に移動
                self.cache.move_to_end(key)
                return self.cache[key]
            return None
    
    def put(self, key: str, value: T) -> None:
        """キー・値のペアを保存"""
        with self.lock:
            if key in self.cache:
                # 既存キーの場合は更新して最新に移動
                self.cache[key] = value
                self.cache.move_to_end(key)
            else:
                # 新規キーの場合
                if len(self.cache) >= self.max_size:
                    # 容量超過時は最も古いアイテムを削除
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                    logger.debug(f"LRUCache: 古いエントリを削除 - {oldest_key}")
                
                self.cache[key] = value
    
    def remove(self, key: str) -> bool:
        """キーを削除"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """キャッシュをクリア"""
        with self.lock:
            self.cache.clear()
    
    def size(self) -> int:
        """現在のキャッシュサイズを取得"""
        return len(self.cache)
    
    def keys(self) -> list:
        """キャッシュのキー一覧を取得"""
        with self.lock:
            return list(self.cache.keys())


class TTLCache(Generic[T]):
    """
    TTL (Time To Live) キャッシュ実装
    """
    
    def __init__(self, default_ttl: int = 300):  # デフォルト5分
        self.default_ttl = default_ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[T]:
        """キーでアイテムを取得（期限切れチェック付き）"""
        with self.lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            current_time = time.time()
            
            # TTL期限切れチェック
            if current_time > entry['expires_at']:
                del self.cache[key]
                logger.debug(f"TTLCache: 期限切れエントリを削除 - {key}")
                return None
            
            return entry['value']
    
    def put(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """キー・値のペアを保存（TTL指定可）"""
        with self.lock:
            ttl_seconds = ttl or self.default_ttl
            expires_at = time.time() + ttl_seconds
            
            self.cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': time.time()
            }
    
    def remove(self, key: str) -> bool:
        """キーを削除"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def cleanup_expired(self) -> int:
        """期限切れエントリをクリーンアップ"""
        with self.lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self.cache.items()
                if current_time > entry['expires_at']
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                logger.debug(f"TTLCache: {len(expired_keys)}個の期限切れエントリを削除")
            
            return len(expired_keys)
    
    def clear(self) -> None:
        """キャッシュをクリア"""
        with self.lock:
            self.cache.clear()
    
    def size(self) -> int:
        """現在のキャッシュサイズを取得"""
        return len(self.cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """キャッシュ統計を取得"""
        with self.lock:
            current_time = time.time()
            total_entries = len(self.cache)
            expired_entries = sum(
                1 for entry in self.cache.values()
                if current_time > entry['expires_at']
            )
            
            return {
                'total_entries': total_entries,
                'active_entries': total_entries - expired_entries,
                'expired_entries': expired_entries,
                'cache_size_mb': self._calculate_memory_usage()
            }
    
    def _calculate_memory_usage(self) -> float:
        """概算メモリ使用量を計算（MB）"""
        try:
            import sys
            total_size = 0
            for key, entry in self.cache.items():
                total_size += sys.getsizeof(key)
                total_size += sys.getsizeof(entry)
                total_size += sys.getsizeof(entry['value'])
            return total_size / (1024 * 1024)  # MB変換
        except:
            return 0.0


class CacheManager:
    """
    統合キャッシュマネージャー
    """
    
    def __init__(self):
        # 異なる用途に応じたキャッシュインスタンス
        self.api_response_cache = TTLCache[Dict[str, Any]](default_ttl=300)  # 5分
        self.course_cache = TTLCache[List[Dict[str, Any]]](default_ttl=3600)  # 1時間
        self.analysis_cache = LRUCache[Dict[str, Any]](max_size=1000)
        
        # クリーンアップタイマー
        self._setup_cleanup_timer()
    
    def _setup_cleanup_timer(self):
        """定期的なクリーンアップタイマーを設定"""
        def cleanup_task():
            while True:
                try:
                    time.sleep(300)  # 5分間隔
                    self.cleanup_expired()
                except Exception as e:
                    logger.error(f"キャッシュクリーンアップエラー: {e}")
        
        import threading
        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()
        logger.info("キャッシュクリーンアップタイマーを開始しました")
    
    def get_api_response(self, key: str) -> Optional[Dict[str, Any]]:
        """APIレスポンスキャッシュから取得"""
        return self.api_response_cache.get(key)
    
    def cache_api_response(self, key: str, response: Dict[str, Any], ttl: int = 300):
        """APIレスポンスをキャッシュ"""
        self.api_response_cache.put(key, response, ttl)
    
    def get_courses(self, token_hash: str) -> Optional[List[Dict[str, Any]]]:
        """コース情報キャッシュから取得"""
        return self.course_cache.get(f"courses_{token_hash}")
    
    def cache_courses(self, token_hash: str, courses: List[Dict[str, Any]]):
        """コース情報をキャッシュ"""
        self.course_cache.put(f"courses_{token_hash}", courses)
    
    def get_analysis(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """分析結果キャッシュから取得"""
        return self.analysis_cache.get(content_hash)
    
    def cache_analysis(self, content_hash: str, analysis: Dict[str, Any]):
        """分析結果をキャッシュ"""
        self.analysis_cache.put(content_hash, analysis)
    
    def cleanup_expired(self):
        """期限切れエントリのクリーンアップ"""
        api_cleaned = self.api_response_cache.cleanup_expired()
        course_cleaned = self.course_cache.cleanup_expired()
        
        logger.debug(f"キャッシュクリーンアップ完了: API({api_cleaned}), Courses({course_cleaned})")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """全キャッシュの統計情報を取得"""
        return {
            'api_response_cache': self.api_response_cache.get_stats(),
            'course_cache': self.course_cache.get_stats(),
            'analysis_cache': {
                'total_entries': self.analysis_cache.size(),
                'max_size': self.analysis_cache.max_size,
                'keys': self.analysis_cache.keys()[:10]  # 最初の10個のキーのみ
            }
        }
    
    def clear_all(self):
        """全キャッシュをクリア"""
        self.api_response_cache.clear()
        self.course_cache.clear()
        self.analysis_cache.clear()
        logger.info("全キャッシュをクリアしました")


# グローバルキャッシュマネージャーインスタンス
cache_manager = CacheManager()


def cache_result(ttl: int = 300, key_func: Optional[Callable] = None):
    """
    関数の戻り値をキャッシュするデコレーター
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # キャッシュキーの生成
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}_{hash((args, tuple(sorted(kwargs.items()))))}"
            
            # キャッシュから取得を試行
            cached_result = cache_manager.get_api_response(cache_key)
            if cached_result is not None:
                logger.debug(f"キャッシュヒット: {func.__name__}")
                return cached_result
            
            # キャッシュミスの場合は関数を実行
            logger.debug(f"キャッシュミス: {func.__name__}")
            result = func(*args, **kwargs)
            
            # 結果をキャッシュ
            cache_manager.cache_api_response(cache_key, result, ttl)
            
            return result
        
        return wrapper
    
    return decorator