from datetime import datetime, timedelta

import requests
from config import Config, get_logger

logger = get_logger(__name__)

def get_courses(canvas_token=None):
    """
    Canvas LMSからユーザーが登録しているコース一覧を取得します。
    
    Args:
        canvas_token: Canvas APIトークン（Noneの場合は環境変数から取得）
    """
    token = canvas_token or Config.CANVAS_ACCESS_TOKEN
    headers = {
        "Authorization": f"Bearer {token}"
    }
    url = f"{Config.CANVAS_API_BASE_URL}courses"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # HTTPエラーがあれば例外を発生させる
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"コースの取得中にエラーが発生しました: {e}")
        return None

def get_announcements(course_id, canvas_token=None):
    """
    指定されたコースの最新のお知らせを取得します。
    
    Args:
        course_id: コースID
        canvas_token: Canvas APIトークン（Noneの場合は環境変数から取得）
    """
    token = canvas_token or Config.CANVAS_ACCESS_TOKEN
    headers = {
        "Authorization": f"Bearer {token}"
    }
    url = f"{Config.CANVAS_API_BASE_URL}announcements"
    
    # お知らせ取得期間を広げるため、開始日と終了日を設定
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=Config.CANVAS_ANNOUNCEMENT_PERIOD_DAYS)).strftime("%Y-%m-%d")

    params = {
        "context_codes[]": f"course_{course_id}", # コースIDをcontext_codesとして渡す
        "per_page": Config.CANVAS_MAX_ANNOUNCEMENTS_PER_COURSE, # 取得するお知らせの数
        "include[]": "body", # お知らせの本文も取得
        "start_date": start_date,
        "end_date": end_date
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"お知らせの取得中にエラーが発生しました（コースID: {course_id}）: {e}")
        return None

if __name__ == "__main__":
    logger.info("Canvas APIテストを開始します...")

    # コース一覧の取得テスト
    courses = get_courses()
    if courses:
        logger.info("コース一覧:")
        for course in courses:
            logger.info(f"ID: {course.get('id')}, 名前: {course.get('name')}")
        
        # 複数のコースに対してお知らせの取得をテスト
        num_courses_to_test = min(len(courses), 5) # 最初の5つのコース、または存在する全コース
        for i in range(num_courses_to_test):
            course_id = courses[i].get('id')
            course_name = courses[i].get('name')
            if course_id:
                logger.info(f"コース '{course_name}' (ID: {course_id}) のお知らせ:")
                announcements = get_announcements(course_id)
                if announcements:
                    for ann in announcements:
                        logger.info(f"ID: {ann.get('id')}, タイトル: {ann.get('title')}")
                else:
                    logger.warning("お知らせが見つからないか、取得できませんでした。")
            else:
                logger.error(f"コース {i+1} のIDが取得できませんでした。")
    else:
        logger.error("コース一覧が取得できませんでした。APIベースURLまたはアクセストークンを確認してください。")

    logger.info("Canvas APIテストを終了します。") 