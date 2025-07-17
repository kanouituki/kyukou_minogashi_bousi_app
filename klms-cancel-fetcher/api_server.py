#!/usr/bin/env python3
"""
KLMS休講情報API サーバー

既存のバッチ処理ロジックをWebAPIとして提供
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from canvas_api import get_courses, get_announcements
from gpt_analyzer import analyze_announcement
from cache_manager import load_cache, save_cache, get_new_announcements, update_cache_with_announcements
from config import Config, get_logger

logger = get_logger(__name__)

# FastAPIアプリケーション作成
app = FastAPI(
    title="KLMS休講情報API",
    description="KLMS Canvas APIとGPTを使用して休講情報を取得するAPI",
    version="1.0.0"
)

# CORS設定（Unity等からのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切なオリジンを指定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """APIのルートエンドポイント"""
    return {
        "message": "KLMS休講情報API",
        "version": "1.0.0",
        "endpoints": {
            "kyukou": "/api/kyukou - 休講情報を取得",
            "health": "/health - ヘルスチェック"
        }
    }

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/kyukou")
async def get_kyukou_info(
    canvas_token: Optional[str] = Query(None, description="Canvas APIトークン"),
    force_refresh: bool = Query(False, description="キャッシュを無視して強制的に最新情報を取得")
):
    """
    休講情報を取得するAPIエンドポイント
    
    Args:
        canvas_token: Canvas APIトークン（ユーザー提供）
        force_refresh: キャッシュを無視するかどうか
    
    Returns:
        Dict: 休講情報のJSON
    """
    try:
        logger.info(f"休講情報取得API呼び出し - canvas_token: {'あり' if canvas_token else 'なし'}, force_refresh: {force_refresh}")
        
        # 結果を保存するディレクトリを作成
        os.makedirs(Config.RESULTS_DIR, exist_ok=True)
        
        # キャッシュを読み込み
        cache = load_cache()
        if force_refresh:
            logger.info("強制更新: キャッシュをクリア")
            cache = {}
        
        # 現在の日時を取得
        current_time = datetime.now()
        
        # 全体の結果を格納するリスト
        all_results = []
        
        # 1. コース一覧を取得
        logger.info("コース一覧を取得中...")
        courses = get_courses(canvas_token)
        if not courses:
            raise HTTPException(status_code=500, detail="コースの取得に失敗しました")
        
        logger.info(f"取得したコース数: {len(courses)}")
        
        # 2. 各コースのお知らせを取得・分析
        for i, course in enumerate(courses, 1):
            course_id = course.get('id')
            course_name = course.get('name', 'Unknown')
            
            logger.debug(f"[{i}/{len(courses)}] コース: {course_name} (ID: {course_id})")
            
            if not course_id:
                logger.warning("コースIDが取得できませんでした。スキップします。")
                continue
            
            # お知らせを取得
            announcements = get_announcements(course_id, canvas_token)
            if not announcements:
                logger.debug("お知らせが見つかりませんでした。")
                continue
            
            # 新しいお知らせのみを抽出
            new_announcements = get_new_announcements(course_id, announcements, cache)
            if not new_announcements:
                logger.debug("新しいお知らせはありません。")
                # キャッシュは更新しておく
                update_cache_with_announcements(course_id, announcements, cache)
                continue
            
            logger.debug(f"新しいお知らせ数: {len(new_announcements)}")
            
            # 新しいお知らせのみを分析
            for ann in new_announcements:
                ann_title = ann.get('title', '')
                ann_body = ann.get('message', '')
                ann_id = ann.get('id')
                
                logger.debug(f"分析中: {ann_title}")
                
                # GPTで休講判定
                analysis_result = analyze_announcement(ann_title, ann_body)
                
                # エラーチェック
                if 'error' in analysis_result:
                    logger.error(f"分析エラー: {analysis_result['error']}")
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
                    logger.info(f"休講情報を検出: {analysis_result.get('date')} {analysis_result.get('period')}")
            
            # キャッシュを更新
            update_cache_with_announcements(course_id, announcements, cache)
        
        # キャッシュを保存
        save_cache(cache)
        
        # 3. レスポンスの作成
        response_data = {
            'summary': {
                'total_courses': len(courses),
                'total_cancellations': len(all_results),
                'analyzed_at': current_time.isoformat(),
                'api_version': '1.0.0'
            },
            'cancellations': all_results
        }
        
        logger.info(f"API応答: {len(all_results)}件の休講情報を検出")
        return response_data
        
    except Exception as e:
        logger.error(f"API実行中にエラーが発生: {e}")
        raise HTTPException(status_code=500, detail=f"内部サーバーエラー: {str(e)}")

@app.get("/api/kyukou/latest")
async def get_latest_result(
    canvas_token: Optional[str] = Query(None, description="Canvas APIトークン（現在未使用）")
):
    """
    最新の結果ファイルから休講情報を取得（高速版）
    """
    try:
        results_dir = Config.RESULTS_DIR
        if not os.path.exists(results_dir):
            return {
                'summary': {
                    'total_courses': 0,
                    'total_cancellations': 0,
                    'analyzed_at': None,
                    'source': 'no_data'
                },
                'cancellations': []
            }
        
        # 最新のJSONファイルを取得
        json_files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
        if not json_files:
            return {
                'summary': {
                    'total_courses': 0,
                    'total_cancellations': 0,
                    'analyzed_at': None,
                    'source': 'no_results'
                },
                'cancellations': []
            }
        
        # ファイル名でソート（日時順）
        json_files.sort(reverse=True)
        latest_file = os.path.join(results_dir, json_files[0])
        
        # JSONファイルを読み込み
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # source情報を追加
        if 'summary' in data:
            data['summary']['source'] = 'cached_file'
            data['summary']['source_file'] = json_files[0]
        
        logger.info(f"キャッシュファイルから応答: {latest_file}")
        return data
        
    except Exception as e:
        logger.error(f"キャッシュファイル読み込みエラー: {e}")
        raise HTTPException(status_code=500, detail=f"キャッシュ読み込みエラー: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    # 設定の初期化
    logger.info("FastAPIサーバーを起動しています...")
    
    # サーバー起動
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )