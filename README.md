# github-practice-repo  

이것은 저의 첫 번째 변경 사항입니다.

## JWT 인증 시스템

이 프로젝트에는 JWT 기반 사용자 인증 및 세션 관리 시스템이 구현되어 있습니다.

### 주요 기능
- 사용자 회원가입 및 로그인
- JWT 토큰 기반 인증
- 세션 관리 및 로그아웃
- 토큰 검증 및 블랙리스트 처리

### 시작하기
```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env

# 서버 실행
python auth_api.py

# 테스트 실행
python test_auth_api.py
```

### 문서
- [API 문서](API_DOCUMENTATION.md) - 전체 API 레퍼런스
- [구현 요약](IMPLEMENTATION_SUMMARY.md) - 구현 개요 및 보안 기능

