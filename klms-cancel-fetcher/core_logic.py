"""
統合コアロジックモジュール
main.pyとapi_server.pyの重複処理を統合し、パフォーマンスを最適化
"""

import asyncio
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from canvas_api import get_courses, get_announcements
from gpt_analyzer import analyze_announcement
from cache_manager import load_cache, save_cache, get_new_announcements, update_cache_with_announcements
from memory_cache import cache_manager, cache_result
from parallel_processor import ParallelProcessor, RequestTask
from config import Config, get_logger

logger = get_logger(__name__)


class CoreProcessor:
    """
    休講情報処理のコアロジック
    """
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.parallel_processor = ParallelProcessor(max_concurrent=max_workers)
    
    async def process_kyukou_info(
        self, 
        canvas_token: Optional[str] = None, 
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        休講情報を非同期で処理（統合版）
        
        Args:
            canvas_token: Canvas APIトークン
            force_refresh: キャッシュを無視して強制更新
            
        Returns:
            処理結果の辞書
        """
        start_time = datetime.now()
        logger.info(f"休講情報処理開始 - force_refresh: {force_refresh}")
        
        try:
            # キャッシュキーの生成
            token_hash = self._generate_token_hash(canvas_token)
            
            # キャッシュの読み込み
            cache = load_cache()
            if force_refresh:
                logger.info("強制更新: キャッシュをクリア")
                cache = {}
                cache_manager.clear_all()
            
            # コース一覧の取得（キャッシュ利用）
            courses = await self._get_courses_cached(canvas_token, token_hash, force_refresh)
            if not courses:
                raise ValueError("コースの取得に失敗しました")
            
            logger.info(f"取得したコース数: {len(courses)}")
            
            # 各コースの処理を並列実行
            all_results = await self._process_courses_parallel(
                courses, canvas_token, cache
            )
            
            # キャッシュを保存
            save_cache(cache)
            
            # レスポンスの構築
            processing_time = (datetime.now() - start_time).total_seconds()
            response_data = self._build_response(courses, all_results, start_time, processing_time)
            
            logger.info(
                f"休講情報処理完了 - "
                f"コース数: {len(courses)}, "
                f"休講件数: {len(all_results)}, "
                f"処理時間: {processing_time:.2f}秒"
            )
            
            return response_data
            
        except Exception as e:
            logger.error(f"休講情報処理中にエラーが発生: {e}")
            raise
    
    async def _get_courses_cached(
        self, 
        canvas_token: Optional[str], 
        token_hash: str, 
        force_refresh: bool
    ) -> Optional[List[Dict[str, Any]]]:
        """
        コース一覧をキャッシュ利用で取得
        """
        if not force_refresh:
            # インメモリキャッシュから取得を試行
            cached_courses = cache_manager.get_courses(token_hash)
            if cached_courses:
                logger.debug("コース一覧をインメモリキャッシュから取得")
                return cached_courses
        
        # Canvas APIから取得
        courses = await asyncio.get_event_loop().run_in_executor(
            None, get_courses, canvas_token
        )
        
        if courses:
            # キャッシュに保存
            cache_manager.cache_courses(token_hash, courses)
        
        return courses
    
    async def _process_courses_parallel(
        self, 
        courses: List[Dict[str, Any]], 
        canvas_token: Optional[str], 
        cache: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        コース処理を並列実行
        """
        all_results = []
        
        # 並列処理のためのタスク作成
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 各コースの処理を並列に投入
            future_to_course = {
                executor.submit(
                    self._process_single_course, 
                    course, canvas_token, cache
                ): course
                for course in courses
            }
            
            # 結果を収集
            for future in as_completed(future_to_course):
                course = future_to_course[future]
                try:
                    course_results = future.result()
                    all_results.extend(course_results)
                except Exception as e:
                    course_name = course.get('name', 'Unknown')
                    logger.error(f"コース'{course_name}'の処理でエラー: {e}")
        
        return all_results
    
    def _process_single_course(
        self, 
        course: Dict[str, Any], 
        canvas_token: Optional[str], 
        cache: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        単一コースの処理
        """
        course_id = course.get('id')
        course_name = course.get('name', 'Unknown')
        
        if not course_id:
            logger.warning(f"コースID取得失敗: {course_name}")
            return []
        
        logger.debug(f"コース処理開始: {course_name} (ID: {course_id})")
        
        try:
            # お知らせを取得
            announcements = get_announcements(course_id, canvas_token)
            if not announcements:
                logger.debug(f"お知らせなし: {course_name}")
                return []
            
            # 新しいお知らせのみを抽出
            new_announcements = get_new_announcements(course_id, announcements, cache)
            if not new_announcements:
                logger.debug(f"新しいお知らせなし: {course_name}")
                # キャッシュは更新
                update_cache_with_announcements(course_id, announcements, cache)
                return []
            
            logger.debug(f"新しいお知らせ数: {len(new_announcements)} - {course_name}")
            
            # 新しいお知らせを分析
            course_results = []
            for ann in new_announcements:
                result = self._analyze_announcement_cached(ann, course, course_id)
                if result and result.get('canceled', False):
                    course_results.append(result)
            
            # キャッシュを更新
            update_cache_with_announcements(course_id, announcements, cache)
            
            if course_results:
                logger.info(f"休講検出: {len(course_results)}件 - {course_name}")
            
            return course_results
            
        except Exception as e:
            logger.error(f"コース処理エラー ({course_name}): {e}")
            return []
    
    def _analyze_announcement_cached(
        self, 
        announcement: Dict[str, Any], 
        course: Dict[str, Any], 
        course_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        お知らせ分析（キャッシュ利用）
        """
        ann_title = announcement.get('title', '')
        ann_body = announcement.get('message', '')
        ann_id = announcement.get('id')
        
        # 分析キャッシュキーの生成
        content_hash = hashlib.md5(
            f"{ann_title}|{ann_body}".encode('utf-8')
        ).hexdigest()
        
        # キャッシュから分析結果を取得
        cached_analysis = cache_manager.get_analysis(content_hash)
        if cached_analysis:
            logger.debug(f"分析結果をキャッシュから取得: {ann_title}")
            analysis_result = cached_analysis.copy()
        else:
            # GPTで新規分析
            logger.debug(f"GPT分析実行: {ann_title}")
            analysis_result = analyze_announcement(ann_title, ann_body)
            
            # エラーチェック
            if 'error' in analysis_result:
                logger.error(f"分析エラー: {analysis_result['error']}")
                return None
            
            # 分析結果をキャッシュ
            cache_manager.cache_analysis(content_hash, analysis_result)
        
        # メタデータを追加
        analysis_result.update({
            'course_id': course_id,
            'course_name': course.get('name', ''),
            'announcement_id': ann_id,
            'announcement_title': ann_title,
            'analyzed_at': datetime.now().isoformat()
        })
        
        return analysis_result
    
    def _generate_token_hash(self, canvas_token: Optional[str]) -> str:
        """
        Canvas APIトークンのハッシュを生成
        """
        token = canvas_token or Config.CANVAS_ACCESS_TOKEN or ""
        return hashlib.sha256(token.encode('utf-8')).hexdigest()[:16]
    
    def _build_response(
        self, 
        courses: List[Dict[str, Any]], 
        all_results: List[Dict[str, Any]], 
        start_time: datetime,
        processing_time: float
    ) -> Dict[str, Any]:
        """
        APIレスポンスを構築
        """
        return {
            'summary': {
                'total_courses': len(courses),
                'total_cancellations': len(all_results),
                'analyzed_at': start_time.isoformat(),
                'api_version': '1.0.0',
                'processing_time_seconds': processing_time,
                'cache_stats': cache_manager.get_cache_stats()
            },
            'cancellations': all_results
        }


# 使いやすくするための関数インターフェース
@cache_result(ttl=600)  # 10分キャッシュ
async def process_courses_optimized(
    canvas_token: Optional[str] = None,
    force_refresh: bool = False,
    max_workers: int = 4
) -> Dict[str, Any]:
    """
    最適化されたコース処理関数
    """
    processor = CoreProcessor(max_workers=max_workers)
    return await processor.process_kyukou_info(canvas_token, force_refresh)


def process_courses_sync(
    canvas_token: Optional[str] = None,
    force_refresh: bool = False,
    max_workers: int = 4
) -> Dict[str, Any]:
    """
    同期版のコース処理関数（main.py用）
    """
    return asyncio.run(
        process_courses_optimized(canvas_token, force_refresh, max_workers)
    )