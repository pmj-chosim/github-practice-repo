"""
Authentication API
JWT 기반 사용자 인증 API 엔드포인트
"""
from flask import Flask, request, jsonify
import bcrypt
import sqlite3
import datetime
import os
from dotenv import load_dotenv

from auth_jwt import generate_token, decode_token, token_required
from session_manager import (
    create_session, invalidate_session, is_token_blacklisted,
    cleanup_expired_sessions, get_user_sessions
)

# 환경 변수 로드
load_dotenv()

app = Flask(__name__)

# 헬퍼 함수
def extract_token_from_header():
    """Authorization 헤더에서 토큰 추출"""
    if 'Authorization' not in request.headers:
        return None
    
    auth_header = request.headers['Authorization']
    try:
        return auth_header.split(' ')[1]  # "Bearer <token>" 형식
    except IndexError:
        return None


# 데이터베이스 초기화
def init_db():
    """사용자 테이블 초기화"""
    conn = sqlite3.connect('auth.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


@app.route('/api/auth/register', methods=['POST'])
def register():
    """
    사용자 회원가입 엔드포인트
    
    Request Body:
        - username: 사용자 이름
        - password: 비밀번호
    
    Returns:
        성공 메시지 및 사용자 정보
    """
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': '사용자 이름과 비밀번호가 필요합니다'}), 400
    
    username = data['username']
    password = data['password']
    
    # 비밀번호 해시 생성
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    try:
        conn = sqlite3.connect('auth.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'message': '회원가입이 완료되었습니다',
            'user': {
                'id': user_id,
                'username': username
            }
        }), 201
    
    except sqlite3.IntegrityError:
        return jsonify({'message': '이미 존재하는 사용자 이름입니다'}), 409
    except Exception as e:
        return jsonify({'message': f'오류가 발생했습니다: {str(e)}'}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    사용자 로그인 엔드포인트
    
    Request Body:
        - username: 사용자 이름
        - password: 비밀번호
    
    Returns:
        JWT 토큰 및 사용자 정보
    """
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': '사용자 이름과 비밀번호가 필요합니다'}), 400
    
    username = data['username']
    password = data['password']
    
    try:
        conn = sqlite3.connect('auth.db')
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, username, password_hash FROM users WHERE username = ?',
            (username,)
        )
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'message': '사용자 이름 또는 비밀번호가 올바르지 않습니다'}), 401
        
        user_id, username, password_hash = user
        
        # 비밀번호 검증
        if not bcrypt.checkpw(password.encode('utf-8'), password_hash):
            return jsonify({'message': '사용자 이름 또는 비밀번호가 올바르지 않습니다'}), 401
        
        # JWT 토큰 생성
        token = generate_token(user_id, username)
        
        # 세션 생성
        expiration = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            hours=int(os.getenv('JWT_EXPIRATION_HOURS', '24'))
        )
        create_session(token, user_id, username, expiration)
        
        return jsonify({
            'message': '로그인 성공',
            'token': token,
            'user': {
                'id': user_id,
                'username': username
            }
        }), 200
    
    except Exception as e:
        return jsonify({'message': f'오류가 발생했습니다: {str(e)}'}), 500


@app.route('/api/auth/logout', methods=['POST'])
@token_required
def logout(current_user):
    """
    사용자 로그아웃 엔드포인트
    
    Headers:
        - Authorization: Bearer <token>
    
    Returns:
        로그아웃 성공 메시지
    """
    try:
        token = extract_token_from_header()
        
        if not token:
            return jsonify({'message': '토큰을 찾을 수 없습니다'}), 401
        
        # 세션 무효화
        invalidate_session(token)
        
        return jsonify({'message': '로그아웃되었습니다'}), 200
    
    except Exception as e:
        return jsonify({'message': f'오류가 발생했습니다: {str(e)}'}), 500


@app.route('/api/auth/verify', methods=['GET'])
@token_required
def verify_token(current_user):
    """
    토큰 검증 엔드포인트
    
    Headers:
        - Authorization: Bearer <token>
    
    Returns:
        토큰 유효성 및 사용자 정보
    """
    try:
        token = extract_token_from_header()
        
        if not token:
            return jsonify({'message': '토큰을 찾을 수 없습니다'}), 401
        
        # 블랙리스트 확인
        if is_token_blacklisted(token):
            return jsonify({'message': '무효화된 토큰입니다'}), 401
        
        return jsonify({
            'message': '유효한 토큰입니다',
            'user': {
                'id': current_user['user_id'],
                'username': current_user['username']
            }
        }), 200
    
    except Exception as e:
        return jsonify({'message': f'오류가 발생했습니다: {str(e)}'}), 500


@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """
    현재 로그인된 사용자 정보 조회
    
    Headers:
        - Authorization: Bearer <token>
    
    Returns:
        사용자 정보
    """
    return jsonify({
        'user': {
            'id': current_user['user_id'],
            'username': current_user['username']
        }
    }), 200


@app.route('/api/auth/sessions', methods=['GET'])
@token_required
def get_sessions(current_user):
    """
    현재 사용자의 활성 세션 목록 조회
    
    Headers:
        - Authorization: Bearer <token>
    
    Returns:
        활성 세션 목록
    """
    sessions = get_user_sessions(current_user['user_id'])
    
    # 토큰은 마스킹 처리하고 타임스탬프를 안전하게 처리
    masked_sessions = []
    for session in sessions:
        session_info = {}
        if hasattr(session.get('created_at'), 'isoformat'):
            session_info['created_at'] = session['created_at'].isoformat()
        else:
            session_info['created_at'] = str(session.get('created_at', 'N/A'))
        
        if hasattr(session.get('expiration'), 'isoformat'):
            session_info['expiration'] = session['expiration'].isoformat()
        else:
            session_info['expiration'] = str(session.get('expiration', 'N/A'))
        
        masked_sessions.append(session_info)
    
    return jsonify({
        'sessions': masked_sessions,
        'count': len(masked_sessions)
    }), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
