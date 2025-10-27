"""
Authentication API Tests
JWT 인증 시스템 테스트
"""
import unittest
import json
import os
import sqlite3
from auth_api import app, init_db


class AuthAPITestCase(unittest.TestCase):
    """인증 API 테스트 케이스"""
    
    def setUp(self):
        """테스트 환경 설정"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # 환경 변수 설정
        os.environ['SECRET_KEY'] = 'test-secret-key'
        
        # 테스트 데이터베이스 초기화 (기존 데이터 삭제)
        if os.path.exists('auth.db'):
            os.remove('auth.db')
        init_db()
    
    def tearDown(self):
        """테스트 정리"""
        # 세션 상태 초기화
        from session_manager import active_sessions, blacklisted_tokens
        active_sessions.clear()
        blacklisted_tokens.clear()
    
    def test_health_check(self):
        """헬스 체크 테스트"""
        response = self.client.get('/api/health')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'healthy')
    
    def test_register_success(self):
        """회원가입 성공 테스트"""
        response = self.client.post(
            '/api/auth/register',
            data=json.dumps({
                'username': 'testuser',
                'password': 'testpass123'
            }),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 201)
        self.assertIn('message', data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['username'], 'testuser')
    
    def test_register_missing_fields(self):
        """회원가입 필드 누락 테스트"""
        response = self.client.post(
            '/api/auth/register',
            data=json.dumps({'username': 'testuser'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_register_duplicate_username(self):
        """중복 사용자명 회원가입 테스트"""
        # 첫 번째 사용자 등록
        self.client.post(
            '/api/auth/register',
            data=json.dumps({
                'username': 'duplicate',
                'password': 'pass123'
            }),
            content_type='application/json'
        )
        
        # 같은 사용자명으로 다시 등록 시도
        response = self.client.post(
            '/api/auth/register',
            data=json.dumps({
                'username': 'duplicate',
                'password': 'pass456'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 409)
    
    def test_login_success(self):
        """로그인 성공 테스트"""
        # 먼저 사용자 등록
        self.client.post(
            '/api/auth/register',
            data=json.dumps({
                'username': 'loginuser',
                'password': 'loginpass'
            }),
            content_type='application/json'
        )
        
        # 로그인 시도
        response = self.client.post(
            '/api/auth/login',
            data=json.dumps({
                'username': 'loginuser',
                'password': 'loginpass'
            }),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['username'], 'loginuser')
    
    def test_login_wrong_password(self):
        """잘못된 비밀번호로 로그인 테스트"""
        # 사용자 등록
        self.client.post(
            '/api/auth/register',
            data=json.dumps({
                'username': 'user1',
                'password': 'correctpass'
            }),
            content_type='application/json'
        )
        
        # 잘못된 비밀번호로 로그인
        response = self.client.post(
            '/api/auth/login',
            data=json.dumps({
                'username': 'user1',
                'password': 'wrongpass'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
    
    def test_login_nonexistent_user(self):
        """존재하지 않는 사용자 로그인 테스트"""
        response = self.client.post(
            '/api/auth/login',
            data=json.dumps({
                'username': 'nonexistent',
                'password': 'somepass'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
    
    def test_verify_token(self):
        """토큰 검증 테스트"""
        # 사용자 등록 및 로그인
        self.client.post(
            '/api/auth/register',
            data=json.dumps({
                'username': 'verifyuser',
                'password': 'verifypass'
            }),
            content_type='application/json'
        )
        
        login_response = self.client.post(
            '/api/auth/login',
            data=json.dumps({
                'username': 'verifyuser',
                'password': 'verifypass'
            }),
            content_type='application/json'
        )
        token = json.loads(login_response.data)['token']
        
        # 토큰 검증
        response = self.client.get(
            '/api/auth/verify',
            headers={'Authorization': f'Bearer {token}'}
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['user']['username'], 'verifyuser')
    
    def test_verify_token_without_token(self):
        """토큰 없이 검증 요청 테스트"""
        response = self.client.get('/api/auth/verify')
        
        self.assertEqual(response.status_code, 401)
    
    def test_get_current_user(self):
        """현재 사용자 정보 조회 테스트"""
        # 사용자 등록 및 로그인
        self.client.post(
            '/api/auth/register',
            data=json.dumps({
                'username': 'currentuser',
                'password': 'currentpass'
            }),
            content_type='application/json'
        )
        
        login_response = self.client.post(
            '/api/auth/login',
            data=json.dumps({
                'username': 'currentuser',
                'password': 'currentpass'
            }),
            content_type='application/json'
        )
        token = json.loads(login_response.data)['token']
        
        # 현재 사용자 정보 조회
        response = self.client.get(
            '/api/auth/me',
            headers={'Authorization': f'Bearer {token}'}
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['user']['username'], 'currentuser')
    
    def test_logout(self):
        """로그아웃 테스트"""
        # 사용자 등록 및 로그인
        self.client.post(
            '/api/auth/register',
            data=json.dumps({
                'username': 'logoutuser',
                'password': 'logoutpass'
            }),
            content_type='application/json'
        )
        
        login_response = self.client.post(
            '/api/auth/login',
            data=json.dumps({
                'username': 'logoutuser',
                'password': 'logoutpass'
            }),
            content_type='application/json'
        )
        token = json.loads(login_response.data)['token']
        
        # 로그아웃
        response = self.client.post(
            '/api/auth/logout',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        
        # 로그아웃 후 토큰 사용 시도 (블랙리스트 확인)
        verify_response = self.client.get(
            '/api/auth/verify',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(verify_response.status_code, 401)


if __name__ == '__main__':
    unittest.main()
