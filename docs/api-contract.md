# 프론트엔드 ↔ 백엔드 API 약속

프론트엔드(Plann, `frontend/`)가 백엔드(`backend/`)를 부를 때의 요청과 응답 모양입니다.
바꿀 때는 이 문서를 먼저 고치고, 상대가 확인한 뒤 합칩니다.

- 백엔드 주소: 개발 중에는 `http://localhost:8000`. 프론트엔드는 `frontend/app/lib/api.ts`에서 `NEXT_PUBLIC_API_BASE`(없으면 `http://localhost:8000`)로 부릅니다. 바꾸려면 `frontend/.env.local`에 `NEXT_PUBLIC_API_BASE=...`를 적고 개발 서버를 다시 켜세요.
- 프론트엔드 개발 서버(`http://localhost:3000`)에서 오는 요청은 CORS로 허용되어 있습니다. 다른 주소(예: 3000번이 사용 중이라 3001번으로 뜬 경우)는 백엔드 환경변수 `FRONTEND_ORIGINS=http://localhost:3001`(쉼표로 여러 개)로 허용합니다.
- 모든 응답은 JSON입니다. 서버를 켜고 http://localhost:8000/docs 를 열면 아래 API를 직접 눌러 볼 수 있습니다.
- 오류는 `{"detail": "사람이 읽을 이유"}` 모양이고, 요청 형식이 틀리면 422입니다.

## 1. 개설 강좌: `GET /courses`

| 쿼리 | 뜻 |
|---|---|
| `q` | 과목명이나 과목코드 일부 |
| `category` | 이수구분 (`교양`, `전공필수` 등) |
| `department` | 개설학과 |

응답: `{"sample": false, "courses": [Course, ...]}`. `sample`이 `true`면 가짜 샘플 자료입니다.

`Course`(분반 하나):

| 필드 | 예 | 비고 |
|---|---|---|
| `course_id` | `"CAIB0211-001"` | 강좌번호 (학교의 `crseNo`) |
| `course_code` | `"CAIB0211"` | 과목코드 (`sbjetCd`) |
| `section` | `"001"` | 분반 |
| `name`, `credits`, `professor` | | |
| `category`, `grade` | `"공학전공"`, `"4"` | 기본값은 컴학 공통 자료 기준. 트랙별 값은 `listings` |
| `listings` | `[{"source": "ai", "category": "전공", "grade": "3", "department": "..."}]` | 같은 분반이 자료(트랙, 교양 영역)마다 다르게 올라 있는 값. `source`는 프론트엔드의 `sourceId`와 같음 |
| `meetings` | `[{"day": "화", "start": "09:00", "end": "10:30"}]` | 비어 있으면 시간 미정 |
| `time_raw` | `"화 09:00 ~ 10:30,목 10:30 ~ 12:00"` | 학교 원문 |
| `building`, `room` | | 학교의 `lctrmInfo`, `rmnmCd` |
| `capacity`, `enrolled` | `60`, `63` | 학교의 `attlcPrscpCnt`, `appcrCnt`를 정원과 신청 인원으로 **짐작한 것**. 확인 필요 |
| `area` | `"첨성인핵심 · 인문"` | 교양 영역. 시간표 후보 안에서만 채워짐 |

자료는 `frontend/data/course-sources/*.json`(학교 조회 응답 원본)에서 만듭니다. 원본이 바뀌면 백엔드에서 다시 넣습니다.

```bash
python -m scripts.import_data offerings ../frontend/data/course-sources
```

## 2. 시간표 만들기: `POST /tools/generate_timetable`

팀의 「에이전트 도구 정의 v3.2」를 따르며, **필드 이름은 `frontend/app/lib/planning.ts`의 `PlanningConstraints`와 같습니다.** 저장해 둔 조건을 그대로 보내고, 학생 정보만 덧붙이면 됩니다.

### 요청

```json
{
  "base_candidate_id": null,
  "min_credits": 15,
  "target_credits": 18,
  "max_credits": 19,
  "credits_strict": false,
  "free_days": ["금"],
  "blocked_times": [{"day": "월", "start": "09:00", "end": "12:00"}],
  "avoid_times": [{"day": "수", "start": "00:00", "end": "23:59"}],
  "must_include": ["COMP0204", "CAIB0211-001"],
  "exclude": ["CLTR0003"],
  "ge_areas": ["인문"],
  "prefer_professor": ["홍길동"],

  "track": "advanced",
  "grade": 2,
  "completed": ["COMP0101", "COMP0102"],
  "completed_names": ["기초프로그래밍", "자료구조"],
  "max_candidates": 3
}
```

| 필드 | 지키는 정도 | 뜻 |
|---|---|---|
| `min_credits` / `target_credits` / `max_credits` | | `min ≤ target ≤ max`. `max`가 19를 넘으면 19로 줄이고 `warnings`에 알림 (도구 정의서의 기본 상한, 학칙 검증 전) |
| `credits_strict` | | `true`면 최소 학점을 반드시 지킴. `false`면 못 채울 때 적은 학점으로라도 만들고 `partial` |
| `free_days` | 반드시 | 비울 요일 |
| `blocked_times` | 반드시 | 비울 시간 |
| `avoid_times` | 가능하면 | 겹치면 점수가 깎이고 후보 `warnings`에 표시 |
| `must_include` | 반드시 | 과목코드(`COMP0204`), 강좌번호(`CAIB0211-001`, 그 분반만), 과목명 중 하나 |
| `exclude` | 반드시 | 위와 같은 방식. 강좌번호면 그 분반만 뺌 |
| `ge_areas` | 가능하면 | 교양 영역 이름의 일부 (`인문`, `자연`, `첨성인기초`, `첨성인소양`) |
| `prefer_professor` | 가능하면 | 교수 이름 |
| `base_candidate_id` | 가능하면 | 이 후보의 과목을 최대한 유지하며 다시 만듦 (채팅 수정용) |
| `track` | v3.2 밖 확장 | `advanced` `ai` `research` `platform` `global`. 같은 분반의 이수구분을 이 트랙 기준으로 고름 |
| `grade` | v3.2 밖 확장 | 학생 학년. 그 학년 과목을 우선 (임시 기준) |
| `completed` | v3.2 밖 확장 | 이미 이수한 과목코드. 후보에서 뺌. 프론트엔드 내부 id(`knu-1` 등)가 아니라 **과목코드**로 보내 주세요 |
| `completed_names` | v3.2 밖 확장 | 이미 이수한 과목명. 선수과목(학과 권장 순서) 확인에 씀. 이번 학기에 열리지 않는 과목은 코드만으로 이름을 알 수 없어서 따로 받음 |
| `max_candidates` | | 1~5, 기본 3 |

자동 추천에서는 상주캠퍼스 강좌, 교직 과목, 시간 미정 강좌를 뺍니다. `must_include`로 직접 넣으면 넣습니다.

신청 인원·정원은 점수와 경고에 쓰지 않습니다. 점수에서 깎는 것 (넣을 수는 있지만 덜 고름): 토·일 수업, 학과 권장 순서상 먼저 들을 과목의 이수 기록이 없는 과목(이수 과목을 하나라도 보냈을 때만). 선수과목은 후보 `warnings`에 "먼저 들으면 좋은 …"으로 알립니다.

### 응답

```json
{
  "status": "partial",
  "optimal": false,
  "candidates": [
    {
      "id": "tt_001",
      "sections": [Course, ...],
      "total_credits": 9.0,
      "credits_by_category": {"교양": 3.0, "전공필수": 3.0, "전공선택": 3.0},
      "free_days": ["월", "수", "금"],
      "gap_minutes": 300,
      "score": 10.0,
      "warnings": ["알고리즘2: 먼저 들으면 좋은 알고리즘1의 이수 기록이 없습니다 (학과 권장 순서)."]
    }
  ],
  "applied": {"min_credits": 6, "target_credits": 9, "max_credits": 12, "credits_strict": false,
              "track": null, "grade": null, "base_candidate_id": null},
  "omitted_required": [
    {"item": "SAMP0101", "code": "SAMP0101", "name": "글쓰기(샘플)",
     "reason": "free_day_conflict", "detail": "모든 분반이 비워야 하는 요일에 있습니다 (수업 요일: 금)."}
  ],
  "warnings": [],
  "alternatives": [
    {"id": "tt_alt_001", "relaxed": ["금요일 공강"],
     "description": "금요일 공강을 풀면 8학점 (글쓰기(샘플) 포함)", "candidate": {"id": "tt_alt_001", "...": "후보와 같은 모양"}}
  ]
}
```

| 필드 | 뜻 |
|---|---|
| `status` | `success`: 반드시 조건과 최소 학점을 모두 지킴. `partial`: 후보는 있지만 빠진 필수 과목이 있거나 최소 학점 미달. `infeasible`: 후보 없음 |
| `optimal` | 최적임을 증명했는지. 지금은 항상 `false` (조합을 일부만 살펴볼 수 있음) |
| `candidates` | 점수가 높은 순. 최대 `max_candidates`개 |
| `omitted_required[].reason` | `not_offered` 이번 학기 미개설, `already_completed` 이미 이수, `excluded` 제외 목록에도 있음, `free_day_conflict` 모든 분반이 공강 요일, `blocked_time` 모든 분반이 비울 시간과 겹침, `time_conflict` 다른 필수 과목과 겹침 |
| `alternatives` | `success`가 아닐 때, 반드시 조건(공강 요일, 비울 시간)을 하나씩 풀어 보고 나아지는 안을 최대 2개 |
| `warnings` | 상한 19학점 적용, 최소 학점 미달, 조합을 일부만 살펴봄 등 |

후보 id(`tt_001`)는 서버 메모리에 잠시 보관되고 **서버를 다시 켜면 사라집니다.** 프론트엔드가 저장해 두었다가 다시 켠 서버에 보내면 `warnings`로 알리고 처음부터 만듭니다.

## 3. 만든 후보 다시 가져오기: `GET /tools/candidates/{id}`

`tt_001`, `tt_alt_001` 등. 대안을 고르면 새로 만들지 않고 이것으로 가져옵니다. 없으면 404.

## 4. 시간표 에이전트: `POST /agent/chat`

Plann의 '나의 시간표' 옆 채팅이 씁니다 (`frontend/app/lib/api.ts`의 `agentChat`). Claude가 도구(`search_courses`, `update_timetable`, `check_prerequisites`)를 골라 쓰고, 시간표는 항상 2장의 생성기가 다시 만듭니다.

요청:

```json
{
  "mode": "chat",
  "message": "금요일 비워주고 운영체제 넣어줘",
  "request": { "...": "2장 요청 본문 그대로 (지금 시간표를 만든 조건)" },
  "candidate_id": "tt_001",
  "history": [{ "role": "assistant", "content": "18학점 시간표예요…" }]
}
```

- `mode: "summary"`: 시간표를 만든 직후 부릅니다. `message`는 비워도 됩니다. 도구 없이 `candidate_id` 시간표를 요약합니다.
- `candidate_id`: 학생이 지금 보고 있는 안. 고칠 때 이 안의 과목을 가능하면 유지합니다.

응답:

```json
{
  "reply": "금요일을 비우고 운영체제 001분반을 넣었어요. …",
  "steps": [{ "tool": "search_courses", "label": "과목 검색: 운영체제 (1개)", "ok": true },
            { "tool": "update_timetable", "label": "시간표 다시 만들기: 넣기 COMP0312, 공강 금", "ok": true }],
  "applied": true,
  "request": { "...": "고친 조건 (2장 형식)" },
  "result": { "...": "2장 응답 형식의 새 시간표. applied 가 false 면 null" }
}
```

키(`ANTHROPIC_API_KEY`)가 없으면 503, Claude 호출이 실패하면 502와 `detail` 안내 문구를 돌려줍니다.

`POST /chat`은 백엔드 시연 화면(옛 `/timetables` 형식)용으로 남겨 두었습니다. Plann은 쓰지 않습니다.

## 5. 이수 과목 불러오기: `/import/knu/*` (실험 기능, 기본 켜짐)

서버가 띄운 브라우저로 학교 화면을 조작하는 실험 기능입니다. 사용법과 주의 사항은 루트 README의 "경북대 이수 과목 불러오기"를 보세요. 프론트엔드에 붙이려면 다음을 알아야 합니다.

- `X-Import-Session` 헤더로 연결을 구분합니다.
- 기본으로 **서버를 실행한 컴퓨터에서 온 요청만** 받습니다. Next.js가 요청을 대신 넘겨주는 방식(rewrites 프록시)을 쓰면 모든 학생이 "같은 컴퓨터"로 보이므로, 그런 배포에서는 이 기능을 켜지 마세요.

## 아직 없는 것

- `calc_credits`, `check_prereq`: 검증된 졸업 요건과 선수과목 자료가 필요합니다. 그 전까지 시간표는 "트랙 전공, 학생 학년 과목 우선"이라는 임시 기준으로 고릅니다.
- 같은 분반의 트랙별 이수구분: 지금은 `track`이 오면 그 트랙 값, 없으면 컴학 공통 값을 씁니다. 팀에서 다른 규칙을 정하면 백엔드의 `planner.for_track`만 바꾸면 됩니다.
