# Stock Manager MVP

개인 투자 관리를 위한 반응형 웹 MVP 골격입니다. 현재 모든 시세/포트폴리오 예시는 **Mock 데이터**이며 실제 투자 데이터가 아닙니다.

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

## Frontend 실행

```bash
cd frontend
npm install
npm run dev
```

브라우저: `http://localhost:3000`

## 다음 구현 순서

1. Frontend가 FastAPI Mock endpoint를 실제 호출하도록 연결
2. Supabase/PostgreSQL 연결
3. Transaction 저장 및 Position 재계산
4. 실제 Market Provider Adapter 연결
5. OpenDART/SEC 연결
6. 뉴스/이벤트 + 분석 계층 확장

## 안전한 데이터 표시 원칙

- 실시간/지연/EOD/Mock 상태를 숨기지 않습니다.
- Mock 데이터로 투자 판단을 생성하지 않습니다.
- 외부 API 장애 시 마지막 정상 데이터의 기준시점을 표시합니다.
- 계산은 Python 계산 모듈에서 수행하고 AI는 결과 설명만 담당합니다.
