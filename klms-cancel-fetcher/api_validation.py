"""
APIキー検証機能

セキュリティ強化のためのAPIキー検証とレート制限機能を提供
"""

import re
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from config import get_logger

logger = get_logger(__name__)

# レート制限用の簡易キャッシュ
_rate_limit_cache: Dict[str, Dict[str, Any]] = {}

def validate_canvas_token(token: Optional[str]) -> tuple[bool, Optional[str]]:
    """
    Canvas APIトークンの形式検証
    
    Args:
        token: 検証するAPIトークン
        
    Returns:
        tuple: (検証結果, エラーメッセージ)
    """
    if not token:
        return False, "APIトークンが提供されていません"
    
    # 基本的な形式チェック
    if not isinstance(token, str):
        return False, "APIトークンは文字列である必要があります"
    
    # 長さチェック（Canvas APIトークンは通常32文字以上）
    if len(token) < 32:
        return False, "APIトークンが短すぎます（最小32文字）"
    
    if len(token) > 256:
        return False, "APIトークンが長すぎます（最大256文字）"
    
    # 文字セットチェック（英数字とハイフン、アンダースコアのみ許可）
    if not re.match(r'^[a-zA-Z0-9_\-~]+$', token):
        return False, "APIトークンに無効な文字が含まれています"
    
    # 明らかに無効なパターンをチェック
    invalid_patterns = [
        r'^test',
        r'^dummy',
        r'^fake',
        r'^sample',
        r'^example',
        r'^123+',
        r'^aaa+',
    ]
    
    for pattern in invalid_patterns:
        if re.match(pattern, token, re.IGNORECASE):
            return False, f"無効なAPIトークンパターンです: {pattern}"
    
    logger.info("Canvas APIトークンの形式検証が完了しました")
    return True, None

def check_rate_limit(client_id: str, max_requests: int = 60, window_minutes: int = 1) -> tuple[bool, Optional[str]]:
    """
    レート制限チェック
    
    Args:
        client_id: クライアントID（IPアドレスやユーザーIDなど）
        max_requests: ウィンドウ内での最大リクエスト数
        window_minutes: 制限ウィンドウの長さ（分）
        
    Returns:
        tuple: (制限内かどうか, エラーメッセージ)
    """
    now = datetime.now()
    window_start = now - timedelta(minutes=window_minutes)
    
    if client_id not in _rate_limit_cache:
        _rate_limit_cache[client_id] = {
            'requests': [],
            'first_request': now
        }
    
    client_data = _rate_limit_cache[client_id]
    
    # ウィンドウ外の古いリクエストを削除
    client_data['requests'] = [
        req_time for req_time in client_data['requests']
        if req_time > window_start
    ]
    
    # 現在のリクエスト数をチェック
    if len(client_data['requests']) >= max_requests:
        remaining_time = (client_data['requests'][0] + timedelta(minutes=window_minutes) - now).total_seconds()
        return False, f"レート制限に達しました。{remaining_time:.0f}秒後に再試行してください"
    
    # 現在のリクエストを記録
    client_data['requests'].append(now)
    
    return True, None

def validate_request_parameters(params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    リクエストパラメータの検証
    
    Args:
        params: 検証するパラメータ辞書
        
    Returns:
        tuple: (検証結果, エラーメッセージ)
    """
    # force_refresh パラメータの検証
    if 'force_refresh' in params:
        force_refresh = params['force_refresh']
        if not isinstance(force_refresh, (bool, str)):
            return False, "force_refreshパラメータは真偽値または文字列である必要があります"
        
        if isinstance(force_refresh, str):
            if force_refresh.lower() not in ['true', 'false', '1', '0']:
                return False, "force_refreshパラメータの値が無効です"
    
    # canvas_token パラメータの検証
    if 'canvas_token' in params:
        is_valid, error_msg = validate_canvas_token(params['canvas_token'])
        if not is_valid:
            return False, f"canvas_token検証エラー: {error_msg}"
    
    return True, None

def sanitize_error_message(error_msg: str) -> str:
    """
    エラーメッセージから機密情報を除去
    
    Args:
        error_msg: 元のエラーメッセージ
        
    Returns:
        str: サニタイズされたエラーメッセージ
    """
    # APIトークンの一部が含まれている可能性のあるパターンをマスク
    patterns = [
        (r'[a-zA-Z0-9_\-~]{16,}', lambda m: m.group(0)[:4] + '***' + m.group(0)[-4:]),
        (r'Bearer\s+[a-zA-Z0-9_\-~]+', 'Bearer ***'),
        (r'token[\'\":\s=]+[a-zA-Z0-9_\-~]+', 'token: ***'),
        (r'authorization[\'\":\s=]+[a-zA-Z0-9_\-~]+', 'authorization: ***'),
    ]
    
    sanitized = error_msg
    for pattern, replacement in patterns:
        if callable(replacement):
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        else:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
    
    return sanitized

def log_security_event(event_type: str, details: Dict[str, Any], client_id: str = "unknown"):
    """
    セキュリティイベントのログ記録
    
    Args:
        event_type: イベントタイプ（例: "invalid_token", "rate_limit_exceeded"）
        details: イベントの詳細情報
        client_id: クライアントID
    """
    # 機密情報をサニタイズ
    safe_details = {}
    for key, value in details.items():
        if key in ['token', 'authorization', 'canvas_token']:
            safe_details[key] = '***masked***'
        else:
            safe_details[key] = str(value)[:100]  # 長い値は切り詰め
    
    logger.warning(f"セキュリティイベント: {event_type} - クライアント: {client_id} - 詳細: {safe_details}")

def clean_rate_limit_cache():
    """
    レート制限キャッシュのクリーンアップ（古いエントリを削除）
    定期的に呼び出すことを推奨
    """
    cutoff_time = datetime.now() - timedelta(hours=1)
    clients_to_remove = []
    
    for client_id, client_data in _rate_limit_cache.items():
        # 1時間以上前のデータは削除
        if client_data.get('first_request', datetime.now()) < cutoff_time:
            clients_to_remove.append(client_id)
    
    for client_id in clients_to_remove:
        del _rate_limit_cache[client_id]
    
    if clients_to_remove:
        logger.info(f"レート制限キャッシュから{len(clients_to_remove)}個の古いエントリを削除しました")