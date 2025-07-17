#!/usr/bin/env python3
import os
import json
from datetime import datetime
from canvas_api import get_courses, get_announcements
from gpt_analyzer import analyze_announcement
from cache_manager import load_cache, save_cache, get_new_announcements, update_cache_with_announcements, print_cache_stats
from config import Config, get_logger

logger = get_logger(__name__)

def main(canvas_token=None):
    """
    KLMS休講情報取得メインスクリプト
    1. Canvas APIでコース一覧を取得
    2. 各コースのお知らせを取得
    3. GPTで休講判定を実行
    4. 結果をJSONファイルに保存
    
    Args:
        canvas_token: Canvas APIトークン（Noneの場合は環境変数から取得）
    """
    logger.info("KLMS休講情報取得を開始します...")
    
    # 結果を保存するディレクトリを作成
    os.makedirs(Config.RESULTS_DIR, exist_ok=True)
    
    # キャッシュを読み込み
    logger.info("前回のキャッシュを読み込み中...")
    cache = load_cache()
    print_cache_stats(cache)
    
    # 現在の日時を取得（ファイル名用）
    current_time = datetime.now()
    timestamp = current_time.strftime("%Y-%m-%d_%H-%M-%S")
    output_file = f"{Config.RESULTS_DIR}/klms_results_{timestamp}.json"
    
    # 全体の結果を格納するリスト
    all_results = []
    
    try:
        # 1. コース一覧を取得
        logger.info("コース一覧を取得中...")
        courses = get_courses(canvas_token)
        if not courses:
            logger.error("コースの取得に失敗しました。")
            return
        
        logger.info(f"取得したコース数: {len(courses)}")
        
        # 2. 各コースのお知らせを取得・分析
        for i, course in enumerate(courses, 1):
            course_id = course.get('id')
            course_name = course.get('name', 'Unknown')
            
            logger.info(f"[{i}/{len(courses)}] コース: {course_name} (ID: {course_id})")
            
            if not course_id:
                logger.warning("  コースIDが取得できませんでした。スキップします。")
                continue
            
            # お知らせを取得
            announcements = get_announcements(course_id, canvas_token)
            if not announcements:
                logger.debug("  お知らせが見つかりませんでした。")
                continue
            
            logger.debug(f"  お知らせ数: {len(announcements)}")
            
            # 新しいお知らせのみを抽出
            new_announcements = get_new_announcements(course_id, announcements, cache)
            if not new_announcements:
                logger.debug("  新しいお知らせはありません。")
                # キャッシュは更新しておく
                update_cache_with_announcements(course_id, announcements, cache)
                continue
            
            logger.info(f"  新しいお知らせ数: {len(new_announcements)}")
            
            # 新しいお知らせのみを分析
            for ann in new_announcements:
                ann_title = ann.get('title', '')
                ann_body = ann.get('message', '')
                ann_id = ann.get('id')
                
                logger.debug(f"    分析中: {ann_title}")
                
                # GPTで休講判定
                analysis_result = analyze_announcement(ann_title, ann_body)
                
                # エラーチェック
                if 'error' in analysis_result:
                    logger.error(f"    エラー: {analysis_result['error']}")
                    continue
                
                # 結果に追加情報を付与
                analysis_result['course_id'] = course_id
                analysis_result['course_name'] = course_name
                analysis_result['announcement_id'] = ann_id
                analysis_result['announcement_title'] = ann_title
                analysis_result['analyzed_at'] = current_time.isoformat()
                
                # 休講の場合のみ結果に追加
                if analysis_result.get('canceled', False):
                    all_results.append(analysis_result)
                    logger.info(f"    ✓ 休講情報を検出: {analysis_result.get('date')} {analysis_result.get('period')}")
                else:
                    logger.debug("    - 休講ではありません")
            
            # キャッシュを更新
            update_cache_with_announcements(course_id, announcements, cache)
        
        # 3. 結果をJSONファイルに保存
        logger.info(f"結果を保存中: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total_courses': len(courses),
                    'total_cancellations': len(all_results),
                    'analyzed_at': current_time.isoformat()
                },
                'cancellations': all_results
            }, f, ensure_ascii=False, indent=2)
        
        # 4. 結果サマリーを表示
        logger.info("=== 実行結果 ===")
        logger.info(f"分析対象コース数: {len(courses)}")
        logger.info(f"検出した休講情報: {len(all_results)}件")
        logger.info(f"結果ファイル: {output_file}")
        
        if all_results:
            logger.info("検出した休講情報:")
            for result in all_results:
                logger.info(f"  - {result.get('course', 'Unknown')}: {result.get('date')} {result.get('period')}")
        
    except Exception as e:
        logger.error(f"実行中にエラーが発生しました: {e}")
        return
    finally:
        # キャッシュを保存
        logger.info("キャッシュを保存中...")
        save_cache(cache)
    
    logger.info("KLMS休講情報取得を完了しました。")

if __name__ == "__main__":
    main()