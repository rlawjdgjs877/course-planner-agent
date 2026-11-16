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
    schemas.py     # 과목 데이터 형식
  scripts/         # 데이터 변환 스크립트
  tests/           # 테스트
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

## 과목 데이터 만들기 (데이터 담당)

에이전트는 `backend/app/data/courses.json`에서 개설 강좌를 찾습니다. 데이터 형식은 `backend/app/schemas.py`의 `Course`입니다.

학교 시간표 사이트는 `robots.txt`로 자동 수집을 금지하고 있습니다. **프로그램으로 긁어 오지 말고**, 사람이 직접 조회한 결과를 옮기거나 학교에서 제공받은 파일을 사용합니다.

### 1. 표를 파일로 옮기기

1. 학교 '수업시간표 및 강의계획서 조회' 화면에서 필요한 학과·교양을 조회합니다.
2. 결과 표를 열 제목까지 포함해 엑셀에 붙여넣고 `.xlsx` 또는 `.csv`로 저장합니다.
3. 여러 번 조회했다면 한 시트에 이어 붙입니다. 같은 강좌번호는 한 번만 남습니다.

최소한 `강좌번호`, `교과목명`, `학점` 열이 있어야 하고, 시간 충돌 검사를 하려면 `강의시간` 또는 `강의시간(실제시간)` 열이 필요합니다. 열 순서는 상관없습니다.

### 2. JSON으로 변환

`backend` 폴더에서 가상환경을 켠 상태로 실행합니다.

```bash
python -m scripts.convert_courses 저장한파일.xlsx
```

`app/data/courses.json`이 만들어지고, 해석하지 못한 줄이 있으면 경고로 알려 줍니다.

### 샘플 데이터

`app/data/courses.sample.csv`와 `courses.sample.json`은 형식을 보여 주는 **가짜 데이터**입니다. 실제 데이터가 준비되기 전까지 개발과 테스트에 씁니다.

### 테스트

```bash
python -m pytest
```

## 협업 규칙

- `main`에 직접 push하지 말고, 브랜치를 만들어 Pull Request로 올립니다.
- 작업 시작 전에 `git pull`로 최신 코드를 받습니다.
