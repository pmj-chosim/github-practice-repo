# JWT 인증 API 문서

## 개요

이 프로젝트는 JWT(JSON Web Token) 기반의 사용자 인증 및 세션 관리 시스템을 구현합니다.

## 주요 기능

- 사용자 회원가입 및 로그인
- JWT 토큰 기반 인증
- 세션 관리 및 로그아웃
- 토큰 검증 및 블랙리스트 처리
- 비밀번호 해싱 (bcrypt)

## 설치 및 실행

### 의존성 설치

```bash
pip install -r requirements.txt
```

### 환경 변수 설정

`.env.example` 파일을 `.env`로 복사하고 필요한 값을 설정합니다:

```bash
cp .env.example .env
```

`.env` 파일 내용:
```
SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

### 서버 실행

```bash
python auth_api.py
```

서버는 `http://localhost:5000`에서 실행됩니다.

## API 엔드포인트

### 1. 헬스 체크

**Endpoint:** `GET /api/health`

**설명:** 서버 상태를 확인합니다.

**응답:**
```json
{
  "status": "healthy"
}
```

### 2. 회원가입

**Endpoint:** `POST /api/auth/register`

**설명:** 새로운 사용자를 등록합니다.

**Request Body:**
```json
{
  "username": "myusername",
  "password": "mypassword"
}
```

**응답 (201 Created):**
```json
{
  "message": "회원가입이 완료되었습니다",
  "user": {
    "id": 1,
    "username": "myusername"
  }
}
```

**에러 응답:**
- `400`: 사용자 이름과 비밀번호가 필요합니다
- `409`: 이미 존재하는 사용자 이름입니다

### 3. 로그인

**Endpoint:** `POST /api/auth/login`

**설명:** 사용자 로그인 및 JWT 토큰 발급

**Request Body:**
```json
{
  "username": "myusername",
  "password": "mypassword"
}
```

**응답 (200 OK):**
```json
{
  "message": "로그인 성공",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "myusername"
  }
}
```

**에러 응답:**
- `400`: 사용자 이름과 비밀번호가 필요합니다
- `401`: 사용자 이름 또는 비밀번호가 올바르지 않습니다

### 4. 토큰 검증

**Endpoint:** `GET /api/auth/verify`

**설명:** JWT 토큰의 유효성을 검증합니다.

**Headers:**
```
Authorization: Bearer <token>
```

**응답 (200 OK):**
```json
{
  "message": "유효한 토큰입니다",
  "user": {
    "id": 1,
    "username": "myusername"
  }
}
```

**에러 응답:**
- `401`: 토큰이 없습니다
- `401`: 유효하지 않거나 만료된 토큰입니다
- `401`: 무효화된 토큰입니다

### 5. 현재 사용자 정보

**Endpoint:** `GET /api/auth/me`

**설명:** 현재 로그인한 사용자의 정보를 조회합니다.

**Headers:**
```
Authorization: Bearer <token>
```

**응답 (200 OK):**
```json
{
  "user": {
    "id": 1,
    "username": "myusername"
  }
}
```

### 6. 로그아웃

**Endpoint:** `POST /api/auth/logout`

**설명:** 사용자를 로그아웃하고 토큰을 무효화합니다.

**Headers:**
```
Authorization: Bearer <token>
```

**응답 (200 OK):**
```json
{
  "message": "로그아웃되었습니다"
}
```

### 7. 활성 세션 조회

**Endpoint:** `GET /api/auth/sessions`

**설명:** 현재 사용자의 활성 세션 목록을 조회합니다.

**Headers:**
```
Authorization: Bearer <token>
```

**응답 (200 OK):**
```json
{
  "sessions": [
    {
      "created_at": "2024-01-01T12:00:00",
      "expiration": "2024-01-02T12:00:00"
    }
  ],
  "count": 1
}
```

## 사용 예시

### cURL 예시

#### 회원가입
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'
```

#### 로그인
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'
```

#### 토큰 검증
```bash
curl -X GET http://localhost:5000/api/auth/verify \
  -H "Authorization: Bearer <your-token-here>"
```

#### 로그아웃
```bash
curl -X POST http://localhost:5000/api/auth/logout \
  -H "Authorization: Bearer <your-token-here>"
```

## 테스트

테스트를 실행하려면:

```bash
python -m pytest test_auth_api.py -v
```

또는

```bash
python test_auth_api.py
```

## 보안 고려사항

1. **SECRET_KEY**: 프로덕션 환경에서는 반드시 강력한 시크릿 키를 사용하세요.
2. **HTTPS**: 프로덕션 환경에서는 HTTPS를 사용하여 토큰이 암호화된 채널로 전송되도록 하세요.
3. **비밀번호**: bcrypt를 사용하여 안전하게 해싱됩니다.
4. **토큰 만료**: 기본 24시간 후 토큰이 만료됩니다.
5. **세션 관리**: 현재 메모리 기반 세션 저장소를 사용하지만, 프로덕션에서는 Redis 등의 영구 저장소 사용을 권장합니다.

## 아키텍처

### 주요 모듈

- **auth_api.py**: Flask API 엔드포인트
- **auth_jwt.py**: JWT 토큰 생성 및 검증 유틸리티
- **session_manager.py**: 세션 관리 및 토큰 블랙리스트 처리
- **test_auth_api.py**: 단위 테스트

### 데이터베이스 스키마

**users 테이블:**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 라이선스

MIT License
