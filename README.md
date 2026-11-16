# course-planner-agent

수강 설계 에이전트. 성적표와 졸업 요건을 읽고, 시간표 데이터를 조회해 남은 학점을 채우는 시간표 초안을 짜 주는 AI 에이전트입니다.

## 폴더 구조

```
backend/
  app/
    main.py        # FastAPI 서버 시작점
    routers/       # API 엔드포인트
    agent/         # 에이전트 로직 (LLM 호출, 도구 사용)
    services/      # 성적표 파싱, 졸업 요건 계산, 시간표 조회
    data/          # 시간표, 졸업 요건 데이터
  requirements.txt
  .env.example
frontend/          # Next.js (프론트 담당이 생성 예정)
```

## 백엔드 실행 방법

Python 3.10 이상과 git이 필요합니다.

### 1. 코드 받기

```bash
git clone https://github.com/rlawjdgjs877/course-planner-agent.git
cd course-planner-agent/backend
```

### 2. 가상환경 만들고 켜기

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

켜지면 터미널 줄 앞에 `(.venv)`가 붙습니다.

> Windows에서 "스크립트를 실행할 수 없습니다" 오류가 나면
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` 를 한 번 실행한 뒤 다시 시도하세요.

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경변수 파일 만들기

`.env.example`을 복사해 `.env`를 만들고 `OPENAI_API_KEY=` 뒤에 키를 넣습니다.

Windows (PowerShell):

```powershell
Copy-Item .env.example .env
```

macOS / Linux:

```bash
cp .env.example .env
```

**`.env`는 절대 커밋하지 마세요.** `.gitignore`에 들어 있어 기본적으로 올라가지 않습니다.

### 5. 서버 실행

```bash
uvicorn app.main:app --reload
```

### 6. 확인

- API 문서: http://localhost:8000/docs
- 상태 확인: http://localhost:8000/health → `{"status": "ok"}`

서버를 끄려면 터미널에서 `Ctrl + C`를 누릅니다.

## 협업 규칙

- `main`에 직접 push하지 말고, 브랜치를 만들어 Pull Request로 올립니다.
- 작업 시작 전에 `git pull`로 최신 코드를 받습니다.
