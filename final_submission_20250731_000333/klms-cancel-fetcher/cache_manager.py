import os
import json
from datetime import datetime
from typing import Dict, List, Set
from config import Config, get_logger

logger = get_logger(__name__)

def ensure_data_directory():
    """
    dataディレクトリが存在しない場合は作成する
    """
    os.makedirs(Config.DATA_DIR, exist_ok=True)

def load_cache() -> Dict:
    """
    キャッシュファイルから前回の取得データを読み込む
    """
    ensure_data_directory()
    
    if not os.path.exists(Config.CACHE_FILE):
        return {
            'last_updated': None,
            'announcements': {}
        }
    
    try:
        with open(Config.CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"キャッシュファイルの読み込みエラー: {e}")
        return {
            'last_updated': None,
            'announcements': {}
        }

def save_cache(cache_data: Dict):
    """
    現在の取得データをキャッシュファイルに保存する
    """
    ensure_data_directory()
    
    try:
        with open(Config.CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except IOError as e:
        logger.error(f"キャッシュファイルの保存エラー: {e}")

def get_new_announcements(course_id: int, announcements: List[Dict], cache: Dict) -> List[Dict]:
    """
    前回取得時から新しく追加されたお知らせのみを返す
    
    Args:
        course_id: コースID
        announcements: 今回取得したお知らせのリスト
        cache: キャッシュデータ
    
    Returns:
        新しいお知らせのリスト
    """
    course_key = str(course_id)
    cached_announcements = cache.get('announcements', {}).get(course_key, {})
    
    new_announcements = []
    
    for ann in announcements:
        ann_id = str(ann.get('id'))
        
        # キャッシュに存在しない、または更新されている場合は新しいお知らせとして扱う
        if ann_id not in cached_announcements:
            new_announcements.append(ann)
        else:
            # 更新日時で比較（もし利用可能な場合）
            cached_updated_at = cached_announcements[ann_id].get('updated_at')
            current_updated_at = ann.get('updated_at')
            
            if current_updated_at and cached_updated_at:
                if current_updated_at != cached_updated_at:
                    new_announcements.append(ann)
            # 更新日時が取得できない場合は、タイトルで比較
            elif ann.get('title') != cached_announcements[ann_id].get('title'):
                new_announcements.append(ann)
    
    return new_announcements

def update_cache_with_announcements(course_id: int, announcements: List[Dict], cache: Dict):
    """
    キャッシュに今回取得したお知らせ情報を更新する
    
    Args:
        course_id: コースID
        announcements: 今回取得したお知らせのリスト
        cache: キャッシュデータ（更新される）
    """
    course_key = str(course_id)
    
    if 'announcements' not in cache:
        cache['announcements'] = {}
    
    if course_key not in cache['announcements']:
        cache['announcements'][course_key] = {}
    
    # 今回取得したお知らせをキャッシュに追加/更新
    for ann in announcements:
        ann_id = str(ann.get('id'))
        cache['announcements'][course_key][ann_id] = {
            'title': ann.get('title'),
            'updated_at': ann.get('updated_at'),
            'cached_at': datetime.now().isoformat()
        }
    
    # 最終更新時刻を記録
    cache['last_updated'] = datetime.now().isoformat()

def print_cache_stats(cache: Dict):
    """
    キャッシュの統計情報を表示する
    """
    total_courses = len(cache.get('announcements', {}))
    total_announcements = sum(
        len(course_cache) 
        for course_cache in cache.get('announcements', {}).values()
    )
    
    logger.info("キャッシュ統計:")
    logger.info(f"  キャッシュされたコース数: {total_courses}")
    logger.info(f"  キャッシュされたお知らせ数: {total_announcements}")
    logger.info(f"  最終更新: {cache.get('last_updated', '未更新')}")

if __name__ == "__main__":
    # テスト用のコード
    logger.info("キャッシュマネージャーのテストを実行します...")
    
    # キャッシュを読み込み
    cache = load_cache()
    print_cache_stats(cache)
    
    # テストデータ
    test_announcements = [
        {'id': 1, 'title': 'テストお知らせ1', 'updated_at': '2023-06-01T10:00:00Z'},
        {'id': 2, 'title': 'テストお知らせ2', 'updated_at': '2023-06-01T11:00:00Z'}
    ]
    
    # 新しいお知らせをチェック
    new_announcements = get_new_announcements(12345, test_announcements, cache)
    logger.info(f"新しいお知らせ数: {len(new_announcements)}")
    
    # キャッシュを更新
    update_cache_with_announcements(12345, test_announcements, cache)
    save_cache(cache)
    
    logger.info("キャッシュマネージャーのテストを完了しました。")