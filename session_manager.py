"""
Session Management Module
세션 관리 및 로그아웃 토큰 블랙리스트 처리
"""
import datetime
from typing import Set, Dict

# 간단한 메모리 기반 세션 저장소 (프로덕션에서는 Redis 등 사용 권장)
active_sessions: Dict[str, dict] = {}
blacklisted_tokens: Set[str] = set()


def create_session(token: str, user_id: int, username: str, expiration: datetime.datetime):
    """
    새로운 세션 생성
    
    Args:
        token: JWT 토큰
        user_id: 사용자 ID
        username: 사용자 이름
        expiration: 세션 만료 시간
    """
    active_sessions[token] = {
        'user_id': user_id,
        'username': username,
        'created_at': datetime.datetime.now(datetime.UTC),
        'expiration': expiration
    }


def get_session(token: str) -> dict:
    """
    세션 정보 조회
    
    Args:
        token: JWT 토큰
    
    Returns:
        세션 정보 딕셔너리 또는 None
    """
    return active_sessions.get(token)


def invalidate_session(token: str) -> bool:
    """
    세션 무효화 (로그아웃)
    
    Args:
        token: JWT 토큰
    
    Returns:
        성공 여부
    """
    if token in active_sessions:
        del active_sessions[token]
    
    # 토큰을 블랙리스트에 추가
    blacklisted_tokens.add(token)
    return True


def is_token_blacklisted(token: str) -> bool:
    """
    토큰이 블랙리스트에 있는지 확인
    
    Args:
        token: JWT 토큰
    
    Returns:
        블랙리스트 포함 여부
    """
    return token in blacklisted_tokens


def cleanup_expired_sessions():
    """
    만료된 세션 정리
    """
    now = datetime.datetime.now(datetime.UTC)
    expired_tokens = [
        token for token, session in active_sessions.items()
        if session['expiration'] < now
    ]
    
    for token in expired_tokens:
        del active_sessions[token]


def get_active_sessions_count() -> int:
    """
    활성 세션 수 반환
    
    Returns:
        활성 세션 개수
    """
    return len(active_sessions)


def get_user_sessions(user_id: int) -> list:
    """
    특정 사용자의 모든 활성 세션 조회
    
    Args:
        user_id: 사용자 ID
    
    Returns:
        세션 정보 리스트
    """
    return [
        {'token': token, **session}
        for token, session in active_sessions.items()
        if session['user_id'] == user_id
    ]
