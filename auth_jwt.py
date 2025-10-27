"""
JWT Authentication Module
JWT 토큰 생성, 검증, 디코딩을 위한 유틸리티 함수들
"""
import jwt
import datetime
import os
from functools import wraps
from flask import request, jsonify

# 환경 변수에서 설정 가져오기
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))


def generate_token(user_id, username):
    """
    JWT 토큰 생성
    
    Args:
        user_id: 사용자 ID
        username: 사용자 이름
    
    Returns:
        JWT 토큰 문자열
    """
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.datetime.now(datetime.UTC)
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def decode_token(token):
    """
    JWT 토큰 디코딩 및 검증
    
    Args:
        token: JWT 토큰 문자열
    
    Returns:
        디코딩된 페이로드 또는 None (유효하지 않은 경우)
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def token_required(f):
    """
    JWT 토큰 인증이 필요한 엔드포인트를 위한 데코레이터
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Authorization 헤더에서 토큰 추출
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # "Bearer <token>" 형식
            except IndexError:
                return jsonify({'message': '토큰 형식이 올바르지 않습니다'}), 401
        
        if not token:
            return jsonify({'message': '토큰이 없습니다'}), 401
        
        # 토큰 검증
        payload = decode_token(token)
        if not payload:
            return jsonify({'message': '유효하지 않거나 만료된 토큰입니다'}), 401
        
        # 검증된 사용자 정보를 함수에 전달
        return f(payload, *args, **kwargs)
    
    return decorated
