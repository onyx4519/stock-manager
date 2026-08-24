# Stock Manager MVP

개인 투자 관리를 위한 반응형 웹 MVP입니다. 미국 주식은 Massive, 국내 주식은 한국투자증권 KIS의 최근 완료 거래일 EOD 시세를 사용합니다. KIS KOSPI·KOSDAQ 마스터와 Massive 전체 종목 디렉터리를 검색하고, 매수·매도 거래와 관심종목은 로그인 계정별로 SQLite에 분리 저장합니다.

## 구조

- `frontend/`: Next.js + TypeScript 반응형 웹
- `backend/`: FastAPI + Python
- `database/`: 로컬 SQLite 및 PostgreSQL/Supabase-ready schema
- `docs/`: API 및 설계 기록

## Backend 실행

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

확인:
- API docs: `http://localhost:8000/docs`
- health: `http://localhost:8000/health`

테스트:

```bash
cd backend
pytest -q
```

관리자 계정은 일반 회원가입에서 만들 수 없습니다. 백엔드 터미널에서 다음
명령을 실행하고, 화면에 노출되지 않는 입력창에 12자 이상의 비밀번호를
입력합니다.

```bash
cd backend
python scripts/create_admin.py --email admin@example.com --display-name "관리자"
```

관리자 이메일과 비밀번호를 소스 코드나 `.env`에 저장하지 마세요.

## 시장 데이터 모드

Mock, Massive, KIS 또는 국내외 통합 모드를 선택할 수 있습니다.

```env
MARKET_PROVIDER=mock
```

미국 주식과 국내 주식을 함께 사용하려면 로컬 `backend/.env`에서 다음처럼 설정합니다.

```env
MARKET_PROVIDER=hybrid
MASSIVE_SYMBOLS=NVDA,AAPL,MSFT,AMZN,JPM
MASSIVE_CACHE_SECONDS=900
MASSIVE_NEWS_CACHE_SECONDS=900
MASSIVE_API_KEY=발급받은_키
KIS_SYMBOLS=005930,000660,005380,035420,105560
KIS_ENVIRONMENT=real
KIS_CACHE_SECONDS=900
DART_CACHE_SECONDS=900
KIS_APP_KEY=발급받은_App_Key
KIS_APP_SECRET=발급받은_App_Secret
```

`MASSIVE_SYMBOLS`와 `KIS_SYMBOLS`는 홈·검색 첫 화면에 보여 줄 주요 종목입니다. 기본 구성은 국내 5개와 미국 5개이며, 시장 탐색을 위한 목록으로 투자 추천을 의미하지 않습니다. 검색 가능한 전체 종목 수를 제한하는 설정도 아닙니다. 국내 종목은 KIS가 공식 배포하는 최신 KOSPI·KOSDAQ 마스터와 OpenDART의 공식 영문 기업명, 미국 활성 주식은 Massive 종목 디렉터리에서 검색합니다. 미국 종목의 한글명은 `backend/app/services/stock_aliases.py`의 검증된 별칭을 Massive 티커로 변환하며, 선택한 종목의 시세만 조회합니다. KIS 마스터를 일시적으로 불러오지 못한 경우에는 OpenDART 상장회사 목록을 대체 검색원으로 사용합니다.

영문 티커는 Massive, 6자리 국내 종목코드는 KIS로 자동 분기됩니다. 두 Provider 모두 최근 완료된 두 거래일의 종가로 변동률을 계산하고 `EOD`로 표시합니다. OAuth 토큰과 동일 종목 시세는 캐시하여 호출 제한을 줄이며, 외부 API 오류 시 Mock 값으로 자동 대체하지 않습니다.

KIS 모의투자용 키를 사용하는 경우 `KIS_ENVIRONMENT=demo`로 변경합니다.

로컬 거래 데이터 파일 위치는 필요할 때 다음 환경 변수로 변경할 수 있습니다. 상대 경로는 `backend/`를 기준으로 해석됩니다.

```env
DATABASE_PATH=data/stock_manager.db
```

주요 거래·포트폴리오 API:

- `GET /api/v1/transactions`: 전체 거래 조회
- `POST /api/v1/transactions`: 거래 등록
- `PATCH /api/v1/transactions/{id}`: 거래 수정
- `DELETE /api/v1/transactions/{id}`: 거래 삭제
- `GET /api/v1/portfolio/positions`: 실제 보유 포지션 조회
- `GET /api/v1/portfolio/summary`: 통화별 포트폴리오 요약
- `GET /api/v1/stocks?q={검색어}&limit=20`: KOSPI·KOSDAQ·미국 활성 주식 통합 검색
- `POST /api/v1/auth/register`: 계정 생성 및 세션 발급
- `POST /api/v1/auth/login`: 로그인 및 세션 발급
- `GET /api/v1/auth/me`: 현재 로그인 계정 확인
- `POST /api/v1/auth/logout`: 세션 종료
- `GET /api/v1/watchlist`: 관심종목 조회
- `POST /api/v1/watchlist`: 관심종목 추가
- `DELETE /api/v1/watchlist/{symbol}`: 관심종목 삭제
- `GET /api/v1/dart/companies/{stock_code}/disclosures`: 국내 종목 최근 공시
- `GET /api/v1/dart/companies/{stock_code}/financials`: 국내 종목 주요 재무계정
- `GET /api/v1/news?symbol={ticker}`: Massive 미국 종목 최신 뉴스
- `GET /api/v1/analysis/companies/{stock_code}/financial-health`: OpenDART 공식 재무지표와 일반 재무 위험 신호

원화와 달러 자산은 환율을 임의 적용하지 않고 KRW·USD별로 분리하여 표시합니다. 보유 수량을 초과하는 매도 거래는 저장하지 않습니다.

## Frontend 실행

```bash
cd frontend
npm install
npm run dev
```

브라우저: `http://localhost:3000`

## 다음 구현 순서

1. Supabase/PostgreSQL 전환 및 배포 환경 구성
2. 이메일 인증·비밀번호 재설정 등 운영용 인증 강화

## 안전한 데이터 표시 원칙

- 실시간/지연/EOD/Mock 상태를 숨기지 않습니다.
- Mock 데이터로 투자 판단을 생성하지 않습니다.
- 외부 API 장애 시 마지막 정상 데이터의 기준시점을 표시합니다.
- 계산은 Python 계산 모듈에서 수행하고 AI는 결과 설명만 담당합니다.
