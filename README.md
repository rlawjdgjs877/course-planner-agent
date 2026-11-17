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
    db.py          # 데이터베이스 테이블과 읽기·쓰기
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

`.env.example`을 복사해 `.env`를 만들고 `OPENAI_API_KEY=` 뒤에 키를, `OPENAI_MODEL=` 뒤에 사용할 모델 이름을 넣습니다. 채팅 기능에만 필요하고, 없어도 시간표 만들기는 동작합니다.

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

- 시간표 화면: http://localhost:8000
- API 문서: http://localhost:8000/docs
- 상태 확인: http://localhost:8000/health → `{"status": "ok"}`

서버를 끄려면 터미널에서 `Ctrl + C`를 누릅니다.

## API

| 주소 | 설명 |
|---|---|
| `GET /` | 시연용 화면 (`backend/app/static/index.html`). 조건을 고르면 시간표 화면으로 넘어가고, 그 아래 채팅으로 고칠 수 있음 |
| `POST /chat` | 말로 시간표 고치기. 예: "세계의 문화 추가해줘", "운영체제 빼줘". OpenAI 키 필요 |
| `GET /health` | 서버 상태 확인 |
| `GET /courses` | 이번 학기 개설 강좌 전체. `sample`이 `true`이면 가짜 샘플 데이터 |
| `POST /timetables` | 조건에 맞고 시간이 겹치지 않는 시간표를 점수순으로 반환 |

### POST /timetables

AI를 쓰지 않는 계산이라, 돌려주는 시간표는 항상 시간 충돌이 없고 학점 조건을 지킵니다. http://localhost:8000/docs 에서 바로 실행해 볼 수 있습니다.

요청 예시:

```json
{
  "min_credits": 12,
  "max_credits": 15,
  "must_include": ["SAMP0201"],
  "completed": [],
  "exclude": [],
  "blocked_times": [{ "start": "09:00", "end": "10:00" }, { "day": "수", "start": "13:00", "end": "18:00" }],
  "required_credits": { "전공필수": 3 },
  "preferred_free_days": ["금"],
  "max_results": 3
}
```

| 항목 | 의미 |
|---|---|
| `min_credits`, `max_credits` | 이번 학기 학점 범위 (필수) |
| `must_include` | 꼭 넣을 과목. 교과목코드 또는 교과목명 |
| `completed`, `exclude` | 이미 이수한 과목, 넣지 않을 과목 |
| `blocked_times` | 수업을 넣으면 안 되는 시간. `day`를 비우면 모든 요일 |
| `required_credits` | 교과구분별로 이번 학기에 채울 최소 학점 |
| `exclude_full` | 정원이 찬 강좌 제외 여부 |
| `preferred_free_days` | 공강이면 좋은 요일. 반드시 지켜지지는 않고 점수에 반영 |

응답의 `timetables`는 점수가 높은 순입니다. 조건을 만족하는 시간표가 없으면 `timetables`가 비고 `message`에 이유가 담깁니다. `truncated`가 `true`이면 경우의 수가 많아 전부 따져 보지는 못했다는 뜻입니다 (결과는 여전히 모두 유효합니다).

`app/data/courses.json`이 없으면 가짜 샘플 데이터(`courses.sample.json`)로 동작합니다.

### POST /chat

AI는 사용자의 말을 이해해 **조건만** 고치고, 시간표는 `POST /timetables`와 같은 코드가 다시 만듭니다. 그래서 채팅으로 바꿔도 시간이 겹치거나 개설되지 않은 과목이 들어가지 않습니다.

1. 화면이 지금 조건(`request`), 보고 있는 시간표의 강좌번호(`current_course_ids`), 사용자의 말(`message`)을 보냅니다.
2. AI가 고친 조건을 돌려줍니다. 개설 강좌에 없는 과목이나 형식이 틀린 시간은 버립니다.
3. 고친 조건으로 시간표를 다시 만듭니다. 지금 시간표의 과목은 가능하면 유지합니다.
4. 조건에 맞는 시간표가 없으면 적용하지 않고 이유를 답합니다.

`backend/.env`에 `OPENAI_API_KEY`와 `OPENAI_MODEL`이 둘 다 있어야 동작합니다. 없으면 503과 함께 안내 문구를 돌려줍니다. 관련 코드는 `backend/app/agent/chat.py`에 있습니다.

## 데이터베이스

개설 강좌와 졸업 요건은 SQLite 데이터베이스(`backend/app/data/planner.db`)에 들어 있습니다. SQLite는 파일 하나가 곧 데이터베이스라서 따로 설치하거나 켤 것이 없습니다.

| 테이블 | 내용 |
|---|---|
| `courses` | 개설 강좌 (분반 단위): 강좌번호, 과목명, 교과구분, 학점, 교수, 강의실, 정원 등 |
| `meetings` | 강좌별 수업 시간: 요일, 시작, 종료. 주 2회 수업이면 두 줄 |
| `programs` | 학과·입학연도별 졸업 총 학점 |
| `credit_requirements` | 영역(교과구분)별 최소 학점 |
| `required_courses` | 꼭 들어야 하는 과목 |

테이블 정의와 읽고 쓰는 코드는 `backend/app/db.py`에 있습니다.

**DB 파일은 git에 올리지 않습니다.** 서버가 처음 DB에 연결할 때 테이블을 만들고, 비어 있으면 `app/data`의 원본 파일로 채웁니다.

- `courses.json`, `requirements.json`이 있으면 그것으로 채웁니다.
- 없으면 가짜 샘플(`courses.sample.json`, `requirements.sample.json`)로 채웁니다.

그래서 팀원은 `git pull`만 하고 서버를 켜면 같은 DB가 만들어집니다. DB를 처음부터 다시 만들고 싶으면 `planner.db` 파일을 지우고 서버를 다시 켭니다.

### 자료 넣기

`backend` 폴더에서 가상환경을 켠 상태로 실행합니다.

```bash
python -m scripts.import_data courses 저장한파일.xlsx
```

```bash
python -m scripts.import_data requirements 졸업요건.json
```

```bash
python -m scripts.import_data status
```

- `courses`: 엑셀, CSV, JSON을 읽어 강좌를 넣습니다. 같은 연도·학기의 기존 강좌는 새 것으로 바뀌고, 가짜 샘플이 들어 있었다면 지워집니다.
- `requirements`: 졸업 요건을 넣습니다. 형식은 `app/data/requirements.sample.json`을 따릅니다.
- `status`: 지금 들어 있는 자료의 개수를 보여 줍니다.

넣은 자료는 `app/data/courses.json`, `requirements.json`으로도 저장됩니다. **이 JSON 파일을 커밋해서 올려야** 팀원에게 같은 자료가 전달됩니다.

### 조회 API

| 주소 | 설명 |
|---|---|
| `GET /courses?q=자료&category=교양&department=컴퓨터학부` | 강좌 검색. 조건은 모두 선택 사항 |
| `GET /requirements?department=컴퓨터학부&admission_year=2024` | 졸업 요건 |

## 과목 데이터 만들기 (데이터 담당)

데이터 형식은 `backend/app/schemas.py`의 `Course`입니다.

학교 시간표 사이트는 `robots.txt`로 자동 수집을 금지하고 있습니다. **프로그램으로 긁어 오지 말고**, 사람이 직접 조회한 결과를 옮기거나 학교에서 제공받은 파일을 사용합니다.

### 1. 표를 파일로 옮기기

1. 학교 '수업시간표 및 강의계획서 조회' 화면에서 필요한 학과·교양을 조회합니다.
2. 결과 표를 열 제목까지 포함해 엑셀에 붙여넣고 `.xlsx` 또는 `.csv`로 저장합니다.
3. 여러 번 조회했다면 한 시트에 이어 붙입니다. 같은 강좌번호는 한 번만 남습니다.

최소한 `강좌번호`, `교과목명`, `학점` 열이 있어야 하고, 시간 충돌 검사를 하려면 `강의시간` 또는 `강의시간(실제시간)` 열이 필요합니다. 열 순서는 상관없습니다.

### 2. 데이터베이스에 넣기

`backend` 폴더에서 가상환경을 켠 상태로 실행합니다.

```bash
python -m scripts.import_data courses 저장한파일.xlsx
```

데이터베이스에 들어가고 `app/data/courses.json`도 함께 만들어집니다. 해석하지 못한 줄이 있으면 경고로 알려 줍니다. `courses.json`을 커밋해서 올리면 팀원도 같은 과목을 쓰게 됩니다.

### 샘플 데이터

`app/data/courses.sample.csv`와 `courses.sample.json`은 형식을 보여 주는 **가짜 데이터**입니다. 실제 데이터가 준비되기 전까지 개발과 테스트에 씁니다.

### 테스트

```bash
python -m pytest
```

## 협업 규칙

- `main`에 직접 push하지 말고, 브랜치를 만들어 Pull Request로 올립니다.
- 작업 시작 전에 `git pull`로 최신 코드를 받습니다.
