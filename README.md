# Trip For U - 여행 플래너

맞춤형 여행 일정 생성 웹 애플리케이션

## 기능

- ✅ 취향 비중 기반 일정 자동 생성 (맛집, 관광, 쇼핑, 카페)
- ✅ 피로도 자동 계산 & 게이지
- ✅ 날씨 기반 대안 코스 제안
- ✅ 실시간 도착 확인 & 일정 추적
- ✅ PDF 다운로드
- ✅ 반응형 디자인 (데스크탑/태블릿/모바일)
- ✅ Flask REST API 백엔드
- ✅ SQLite 데이터베이스

## 기술 스택

### 프론트엔드
- HTML5 + CSS3
- Vanilla JavaScript
- html2pdf.js
- Google Fonts (Noto Sans KR)

### 백엔드
- Python 3.x
- Flask
- Flask-SQLAlchemy
- SQLite

## 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. Gemini API 키 설정 (선택사항, AI 기능 사용 시)

```bash
# .env.example을 복사하여 .env 파일 생성
cp .env.example .env

# .env 파일을 열어서 Gemini API 키 입력
# GEMINI_API_KEY=your_api_key_here
```

**Gemini API 키 발급 방법:**
1. https://aistudio.google.com/app/apikey 접속
2. Google 계정으로 로그인
3. "Create API Key" 클릭
4. 생성된 키를 `.env` 파일에 입력

**참고:** Gemini API 키가 없어도 기본 알고리즘으로 일정 생성이 가능합니다.

### 3. 데이터베이스 초기화 (샘플 데이터)

```bash
# 서버 실행 후 다음 명령 실행
curl -X POST http://localhost:5000/api/seed-data
```

**PowerShell에서:**
```powershell
Invoke-WebRequest -Uri http://localhost:5000/api/seed-data -Method POST
```

### 4. 서버 실행

```bash
python app.py
```

서버가 `http://localhost:5000`에서 실행됩니다.

### 5. 브라우저에서 접속

```
http://localhost:5000
```

## API 엔드포인트

### 활동 (Activities)

- `GET /api/activities` - 모든 활동 조회
- `GET /api/activities?category=food` - 카테고리별 조회
- `GET /api/activities?indoor=true` - 실내 활동만 조회
- `POST /api/activities` - 새 활동 생성

### 여행 (Trips)

- `GET /api/trips` - 모든 여행 조회
- `POST /api/trips` - 새 여행 생성
- `GET /api/trips/<id>` - 특정 여행 조회
- `PUT /api/trips/<id>` - 여행 수정
- `DELETE /api/trips/<id>` - 여행 삭제

### 일정 (Itinerary)

- `GET /api/trips/<id>/itinerary` - 특정 여행의 일정 조회
- `POST /api/trips/<id>/itinerary` - 일정에 활동 추가

### 일정 생성

- `POST /api/generate-itinerary` - 기본 알고리즘 기반 일정 생성
- `POST /api/generate-itinerary-ai` - Gemini AI 기반 일정 생성 (API 키 필요)

### 데이터

- `POST /api/seed-data` - 샘플 데이터 초기화

## 프로젝트 구조

```
tripforu/
├── app.py              # Flask 백엔드 서버
├── index.html          # 프론트엔드 대시보드
├── requirements.txt    # Python 의존성
├── tripforu.db        # SQLite 데이터베이스 (자동 생성)
└── README.md          # 프로젝트 문서
```

## 데이터베이스 스키마

### Activity (활동)
- id, title, category, duration
- description, tags, indoor
- cost, address, lat, lng

### Trip (여행)
- id, title, city
- start_date, end_date
- start_time, end_time
- transport, preferences, notes

### Itinerary (일정)
- id, trip_id, activity_id
- day_number, order_number
- start_time, end_time

## 개발

### 백엔드 개발 모드

```bash
export FLASK_ENV=development
python app.py
```

### API 테스트

```bash
# 활동 목록 조회
curl http://localhost:5000/api/activities

# 여행 생성
curl -X POST http://localhost:5000/api/trips \
  -H "Content-Type: application/json" \
  -d '{"title":"서울 2박3일","city":"서울","start_date":"2025-11-17","end_date":"2025-11-19"}'

# 일정 생성
curl -X POST http://localhost:5000/api/generate-itinerary \
  -H "Content-Type: application/json" \
  -d '{"preferences":{"food":40,"sight":30,"shopping":15,"cafe":15},"days":3}'
```

## 라이선스

MIT License

## 기여

Issue 또는 Pull Request를 환영합니다!