# Stock Manager MVP

개인 투자 관리를 위한 반응형 웹 MVP입니다. 미국 주식은 Massive, 국내 주식은 한국투자증권 KIS의 최근 완료 거래일 EOD 시세를 사용하며, 포트폴리오는 아직 **Mock 데이터**입니다.

## 구조

- `frontend/`: Next.js + TypeScript 반응형 웹
- `backend/`: FastAPI + Python
- `database/`: PostgreSQL/Supabase-ready schema
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

## 시장 데이터 모드

Mock, Massive, KIS 또는 국내외 통합 모드를 선택할 수 있습니다.

```env
MARKET_PROVIDER=mock
```

미국 주식과 국내 주식을 함께 사용하려면 로컬 `backend/.env`에서 다음처럼 설정합니다.

```env
MARKET_PROVIDER=hybrid
MASSIVE_SYMBOLS=NVDA,AAPL,MSFT
MASSIVE_CACHE_SECONDS=900
MASSIVE_API_KEY=발급받은_키
KIS_SYMBOLS=005930
KIS_ENVIRONMENT=real
KIS_CACHE_SECONDS=900
KIS_APP_KEY=발급받은_App_Key
KIS_APP_SECRET=발급받은_App_Secret
```

영문 티커는 Massive, 6자리 국내 종목코드는 KIS로 자동 분기됩니다. 두 Provider 모두 최근 완료된 두 거래일의 종가로 변동률을 계산하고 `EOD`로 표시합니다. OAuth 토큰과 동일 종목 시세는 캐시하여 호출 제한을 줄이며, 외부 API 오류 시 Mock 값으로 자동 대체하지 않습니다.

KIS 모의투자용 키를 사용하는 경우 `KIS_ENVIRONMENT=demo`로 변경합니다.

## Frontend 실행

```bash
cd frontend
npm install
npm run dev
```

브라우저: `http://localhost:3000`

## 다음 구현 순서

1. SQLite 또는 Supabase/PostgreSQL 연결
2. Transaction 저장 및 Position 재계산
3. 종목 검색과 관심종목 저장
4. OpenDART 재무·공시 화면 연결
5. 뉴스/이벤트 + 분석 계층 확장
6. 배포 환경 구성

## 안전한 데이터 표시 원칙

- 실시간/지연/EOD/Mock 상태를 숨기지 않습니다.
- Mock 데이터로 투자 판단을 생성하지 않습니다.
- 외부 API 장애 시 마지막 정상 데이터의 기준시점을 표시합니다.
- 계산은 Python 계산 모듈에서 수행하고 AI는 결과 설명만 담당합니다.
