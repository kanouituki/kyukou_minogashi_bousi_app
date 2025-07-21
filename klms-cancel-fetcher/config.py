"""
KLMS休講情報取得モジュール設定管理

このファイルでは、システム全体で使用される設定値を一元管理します。
"""

import os
import logging
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

class Config:
    """設定値を管理するクラス"""
    
    # API設定
    CANVAS_API_BASE_URL = "https://lms.keio.jp/api/v1/"
    CANVAS_ACCESS_TOKEN = os.getenv("CANVAS_ACCESS_TOKEN")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Canvas API設定
    CANVAS_MAX_ANNOUNCEMENTS_PER_COURSE = 10
    CANVAS_ANNOUNCEMENT_PERIOD_DAYS = 365
    
    # OpenAI設定
    OPENAI_MODEL = "gpt-4o"
    OPENAI_TEMPERATURE = 0.1
    OPENAI_MAX_TOKENS = 500
    
    # ファイル・ディレクトリ設定
    DATA_DIR = "data"
    CACHE_FILE = "data/cache.json"
    RESULTS_DIR = "results"
    
    # ログ設定
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = "logs/klms.log"
    
    @classmethod
    def validate_required_env_vars(cls):
        """必須の環境変数が設定されているかチェック"""
        missing_vars = []
        
        if not cls.CANVAS_ACCESS_TOKEN:
            missing_vars.append("CANVAS_ACCESS_TOKEN")
        if not cls.OPENAI_API_KEY:
            missing_vars.append("OPENAI_API_KEY")
        
        if missing_vars:
            raise ValueError(
                f"以下の環境変数が.envファイルに設定されていません: {', '.join(missing_vars)}"
            )
    
    @classmethod
    def ensure_directories(cls):
        """必要なディレクトリが存在しない場合は作成"""
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        os.makedirs(cls.RESULTS_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(cls.LOG_FILE), exist_ok=True)
    
    @classmethod
    def setup_logging(cls):
        """ログシステムを設定"""
        # ログレベルを設定
        log_level = getattr(logging, cls.LOG_LEVEL.upper(), logging.INFO)
        
        # ルートロガーを設定
        logging.basicConfig(
            level=log_level,
            format=cls.LOG_FORMAT,
            handlers=[
                logging.FileHandler(cls.LOG_FILE, encoding='utf-8'),
                logging.StreamHandler()  # コンソール出力も維持
            ]
        )

def get_logger(name: str):
    """モジュール名を指定してロガーを取得"""
    return logging.getLogger(name)

# 設定の検証と初期化
Config.validate_required_env_vars()
Config.ensure_directories()
Config.setup_logging()