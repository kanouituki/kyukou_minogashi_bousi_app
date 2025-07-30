"""
型安全なデータモデル定義
pydanticを使用してAPIのリクエスト/レスポンスモデルを定義
"""
from datetime import datetime
from typing import Optional, List, Literal, Union
from enum import Enum
from pydantic import BaseModel, Field, validator, HttpUrl


class AnalysisSource(str, Enum):
    """分析データのソース"""
    KLMS = "KLMS"
    MANUAL = "MANUAL"
    CACHE = "CACHE"


class CancellationStatus(str, Enum):
    """休講ステータス"""
    CANCELED = "canceled"
    POSTPONED = "postponed"
    NORMAL = "normal"
    UNKNOWN = "unknown"


class Period(str, Enum):
    """時限の定義"""
    FIRST = "1限"
    SECOND = "2限"
    THIRD = "3限"
    FOURTH = "4限"
    FIFTH = "5限"
    SIXTH = "6限"
    SEVENTH = "7限"
    UNKNOWN = "不明"


class CancellationDetails(BaseModel):
    """休講情報の詳細"""
    course: str = Field(..., description="授業名")
    date: Optional[str] = Field(None, description="日付 (YYYY-MM-DD形式)")
    period: Optional[Period] = Field(None, description="時限")
    canceled: bool = Field(..., description="休講かどうか")
    source: AnalysisSource = Field(AnalysisSource.KLMS, description="情報源")
    message: Optional[str] = Field(None, description="休講メッセージ")
    reason: Optional[str] = Field(None, description="休講理由")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="信頼度 (0.0-1.0)")
    
    @validator('date')
    def validate_date_format(cls, v):
        """日付形式の検証"""
        if v is not None:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('日付はYYYY-MM-DD形式で入力してください')
        return v


class AnnouncementDetails(BaseModel):
    """お知らせの詳細情報"""
    course_id: int = Field(..., description="コースID")
    course_name: str = Field(..., description="コース名")
    announcement_id: int = Field(..., description="お知らせID")
    announcement_title: str = Field(..., description="お知らせタイトル")
    analyzed_at: datetime = Field(..., description="分析実行日時")


class CancellationInfo(CancellationDetails, AnnouncementDetails):
    """完全な休講情報（詳細情報 + お知らせ情報）"""
    pass


class ApiSummary(BaseModel):
    """API実行結果のサマリー"""
    total_courses: int = Field(..., ge=0, description="取得したコース数")
    total_cancellations: int = Field(..., ge=0, description="検出した休講数")
    analyzed_at: datetime = Field(..., description="分析実行日時")
    api_version: str = Field(..., description="APIバージョン")
    source: Optional[str] = Field(None, description="データソース")
    source_file: Optional[str] = Field(None, description="ソースファイル名")


class KyukouApiResponse(BaseModel):
    """休講情報APIのレスポンス"""
    summary: ApiSummary = Field(..., description="実行結果サマリー")
    cancellations: List[CancellationInfo] = Field(default_factory=list, description="休講情報リスト")


class ApiError(BaseModel):
    """APIエラーレスポンス"""
    error: str = Field(..., description="エラーメッセージ")
    error_code: Optional[str] = Field(None, description="エラーコード")
    details: Optional[dict] = Field(None, description="エラー詳細情報")
    timestamp: datetime = Field(default_factory=datetime.now, description="エラー発生時刻")


class CanvasTokenRequest(BaseModel):
    """Canvas APIトークンリクエスト"""
    canvas_token: str = Field(..., min_length=32, max_length=256, description="Canvas APIトークン")
    force_refresh: bool = Field(False, description="キャッシュを無視して強制更新")
    
    @validator('canvas_token')
    def validate_token_format(cls, v):
        """トークン形式の検証"""
        if not v.replace('-', '').replace('_', '').replace('~', '').isalnum():
            raise ValueError('APIトークンに無効な文字が含まれています')
        return v


class RateLimitInfo(BaseModel):
    """レート制限情報"""
    remaining_requests: int = Field(..., ge=0, description="残りリクエスト数")
    reset_time: datetime = Field(..., description="制限リセット時刻")
    limit_per_window: int = Field(..., gt=0, description="ウィンドウあたりの制限数")
    window_minutes: int = Field(..., gt=0, description="制限ウィンドウ（分）")


class HealthCheckResponse(BaseModel):
    """ヘルスチェックレスポンス"""
    status: Literal["healthy", "unhealthy"] = Field(..., description="サービス状態")
    timestamp: datetime = Field(default_factory=datetime.now, description="チェック時刻")
    version: str = Field("1.0.0", description="APIバージョン")
    dependencies: Optional[dict] = Field(None, description="依存サービスの状態")


class ConfigValidation(BaseModel):
    """設定検証結果"""
    is_valid: bool = Field(..., description="設定が有効かどうか")
    missing_vars: List[str] = Field(default_factory=list, description="不足している環境変数")
    invalid_vars: List[str] = Field(default_factory=list, description="無効な環境変数")
    warnings: List[str] = Field(default_factory=list, description="警告メッセージ")


# エクスポート用のモデル一覧
__all__ = [
    'AnalysisSource',
    'CancellationStatus', 
    'Period',
    'CancellationDetails',
    'AnnouncementDetails',
    'CancellationInfo',
    'ApiSummary',
    'KyukouApiResponse',
    'ApiError',
    'CanvasTokenRequest',
    'RateLimitInfo',
    'HealthCheckResponse',
    'ConfigValidation'
]