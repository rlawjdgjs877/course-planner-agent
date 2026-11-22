> 11/16 기획 시점 문서, 이후 변경: 학교 로그인 불러오기를 아이디·비밀번호 방식(Playwright)으로 구현, LLM은 Claude 대신 OpenAI(tool calling), 시간표 엔진은 OR-Tools CP-SAT 대신 비트마스크·백트래킹 조합 탐색(backend/app/services/timetable.py)으로 구현. 현재 동작은 저장소 README 기준.

# 수강 설계 에이전트 도구 정의 v3.2

- 스택: Claude Opus 5.5(`claude-opus-5-5`) · Anthropic Python SDK · FastAPI · OR-Tools CP-SAT
- 범위: **2026학년도 2학기** 시간표 추천만 (졸업사정·다학기 로드맵 제외). 문서의 "이번 학기"는 모두 2026-2
- 원칙: Claude는 요청 해석·설명, Python은 검색·계산·검증·조합 탐색. Claude는 백엔드가 주지 않은 시간·학점·충돌 여부를 지어내지 않는다.

## 1. 공통 규칙

| 항목 | 결정 |
|---|---|
| 학생 정보 | 도구 입력에 넣지 않음. 이수 과목은 북마클릿/체크박스로, 트랙과 학년은 화면에서 선택받아 백엔드 세션에 저장하고 도구가 꺼내 씀 |
| 성적 | 저장하지 않음. 북마클릿이 브라우저 안에서 F/NP 과목과 성적 필드를 지우고 넘김. 넘어온 과목은 모두 이수 완료로 처리. F 과목은 미이수라 다시 추천 대상이 됨 (재수강 규칙은 범위 밖) |
| 교육과정 연도 | 2025 교육과정 하나로 고정 (데이터가 그것뿐). 화면과 Claude 설명에 "2025 교육과정 기준 참고용, 공식 졸업사정 아님"을 표시 |
| 식별자 | 과목 `sbjetCd`(COMP0312), 분반 `sbjetCd-분반`(COMP0312-001). 학기는 백엔드가 고정 |
| 설계 대상 학기 | 2026-2 고정. 개설강좌는 2026-2 데이터만 사용. 이수내역에 2026-2 행이 있으면(이미 수강 중인 학생) 무시하고 "2026-2 수강신청 전" 상황으로 계산. 그래서 '수강 중' 상태는 따로 두지 않음 |
| 시간 | 출력은 원본 `"월 1A,1B,2A"` 유지, 내부에서 (요일, 슬롯) 집합으로 변환. **Claude가 넣는 시간 조건은 교시가 아니라 시각**(`{day, start: "15:00", end: "18:00"}`)으로 받고 백엔드가 슬롯으로 바꿈. Claude가 교시표를 외울 필요가 없음 |
| 시간 미정 강좌 | 충돌 없음으로 치지 않고 `unresolved`로 따로 표시 |
| 스키마 | 전 도구 `strict: true`, `additionalProperties: false`, 모든 필드 required. 안 쓰는 조건은 `null` 또는 `[]` |
| 수강 학점 상한 | 백엔드 상수(기본 19, 학칙 확인 필요) |
| 시간표 결과 저장 | generate_timetable 결과 후보를 세션에 `tt_001` 같은 id로 저장. id는 세션 안에서 계속 증가하고 재사용하지 않음. 수정 요청은 이 id로 참조하고, 백엔드가 그 학생 세션의 결과인지 확인 |

공통 오류 형식: `{"error": {"code": "...", "message": "...", "details": {}}}`

| 코드 | 의미 |
|---|---|
| `SESSION_NOT_READY` | 이수 과목이 아직 입력되지 않음 |
| `NOT_FOUND` | 과목코드·분반이 이번 학기에 없음 (details에 어떤 id인지) |
| `INVALID_CONSTRAINT` | 조건끼리 모순 (예: min > max) |
| `DATA_INCOMPLETE` | 규칙·시간 데이터가 없어 판정 불가 |

## 2. 도구 5개

### 2.1 search_courses: 개설강좌 조회

```json
{
  "name": "search_courses",
  "description": "이번 학기 개설강좌를 분반 단위로 검색한다. 과목명·과목코드 일부, 이수구분, 교양 영역, 대상 학년, 수업 요일로 거를 수 있고 최대 30개를 반환한다. 결과가 30개를 넘으면 조건을 좁혀 다시 검색한다. 특정 과목의 개설 여부·분반·시간·교수를 묻거나 시간표 후보를 찾을 때 사용한다.",
  "strict": true,
  "input_schema": {
    "type": "object",
    "properties": {
      "keyword":  { "type": ["string", "null"], "description": "과목명 또는 과목코드 일부. 없으면 null" },
      "category": { "type": "string", "enum": ["전공", "교양", "전체"], "description": "전공은 공학전공·전공기반·기본소양 포함" },
      "ge_area":  { "type": ["string", "null"], "description": "교양 영역명. 없으면 null" },
      "grade":    { "type": ["integer", "null"], "description": "개설 대상 학년. 없으면 null" },
      "days":     { "type": "array", "items": { "type": "string", "enum": ["월","화","수","목","금","토"] }, "description": "이 요일에만 수업이 있는 분반. 빈 배열이면 제한 없음" }
    },
    "required": ["keyword", "category", "ge_area", "grade", "days"],
    "additionalProperties": false
  }
}
```

출력: `{ total_count, has_more, sections: [{ id, code, name, category, credit, time, professor, capacity, applicants, english, note }] }`
`capacity`·`applicants`는 데이터 수집 시점 값이라 참고용으로만 안내한다.

### 2.2 calc_credits: 학점 현황

```json
{
  "name": "calc_credits",
  "description": "세션의 이수 과목을 학생 트랙의 2025 교육과정 요건과 비교해 이수구분별 이수·부족 학점, 미이수 전공필수, 부족 교양 영역을 반환한다. candidate_id나 planned_sections를 주면 그 분반을 이번 학기에 듣는다고 가정한 결과도 계산한다. 졸업 가능 여부를 최종 판정하지는 않는다.",
  "strict": true,
  "input_schema": {
    "type": "object",
    "properties": {
      "candidate_id":     { "type": ["string", "null"], "description": "시간표 후보 id(예: 'tt_001'). 그 후보를 듣는다고 가정해 계산. 없으면 null" },
      "planned_sections": { "type": "array", "items": { "type": "string" }, "description": "후보 id 없이 직접 지정할 수강 예정 분반 id. 없으면 빈 배열" }
    },
    "required": ["candidate_id", "planned_sections"],
    "additionalProperties": false
  }
}
```

출력:
```json
{ "track": "심화컴퓨팅",
  "total": { "earned": 23, "planned": 18, "required": 140 },
  "by_category": [ { "category": "전공필수", "earned": 12, "planned": 6, "required": 30, "remaining_after_plan": 12 } ],
  "missing_required_courses": [ { "code": "COMP0204", "name": "자료구조", "recommended_term": "2-1", "offered_this_term": true } ],
  "missing_ge_areas": ["인문", "사회"] }
```

### 2.3 check_prereq: 선수과목 확인

```json
{
  "name": "check_prereq",
  "description": "지정한 과목들을 이번 학기에 들을 수 있는지 선수과목 규칙과 세션의 이수 과목으로 판정한다. 결과는 eligible, ineligible, unknown 중 하나이며, 규칙 데이터가 없으면 unknown이다. 이번 학기에 같이 들을 과목은 선수과목 이수로 치지 않는다.",
  "strict": true,
  "input_schema": {
    "type": "object",
    "properties": {
      "course_codes": { "type": "array", "items": { "type": "string" }, "description": "과목코드 목록" }
    },
    "required": ["course_codes"],
    "additionalProperties": false
  }
}
```

출력: `{ results: [{ code, name, status, missing_required: [{ code, name }], missing_recommended: [], chain: ["시스템프로그래밍", "운영체제", "클라우드컴퓨팅"] }] }`

선수과목 데이터 형식 (조사 안 한 과목과 선수과목 없는 과목을 구분):
```json
{ "COMP0312": { "verified": true, "required": ["COMP0311"], "recommended": [] },
  "COMP0204": { "verified": true, "required": [], "recommended": [] } }
```

| 데이터 | status |
|---|---|
| verified, 필수 선수과목 충족 (권장만 미이수면 경고 포함) | `eligible` |
| 필수 선수과목 미이수 | `ineligible` |
| 키가 없거나 verified false | `unknown` |

### 2.4 check_conflict: 시간 충돌 확인

```json
{
  "name": "check_conflict",
  "description": "분반 목록의 시간 충돌, 같은 과목 분반 중복 선택, 시간 미정 강좌를 검사한다. 시간 정보가 불완전한 분반이 있으면 ok를 true로 주지 않는다.",
  "strict": true,
  "input_schema": {
    "type": "object",
    "properties": {
      "section_ids": { "type": "array", "items": { "type": "string" }, "description": "분반 id 목록" }
    },
    "required": ["section_ids"],
    "additionalProperties": false
  }
}
```

출력: `{ ok, conflicts: [{ a, b, overlap: "화 3B,4A" }], duplicate_courses: [], unresolved: [], not_found: [] }`
`ok: true`는 모든 분반을 확인했고 충돌·중복·시간 미정이 하나도 없을 때만.

### 2.5 generate_timetable: 시간표 생성

```json
{
  "name": "generate_timetable",
  "description": "이번 학기 시간표 후보를 최대 3개 만든다. 선수과목, 시간 충돌, 분반 중복, 학점 상한, 학생이 반드시 지키라고 한 조건(must_include, exclude, free_days, blocked_times)은 절대 어기지 않는다. 학점은 max_credits와 학칙 상한만 강제하고, min_credits는 credits_strict가 true일 때만 강제한다. 그 안에서 1) 권장 학기가 됐거나 지난 미이수 전공필수 과목 수, 2) 그중 권장 학기가 지난 과목, 3) 목표 학점 근접, 4) 전공선택·부족 교양 영역, 5) avoid_times·선호 교수 순서로 최적화한다. 조건을 모두 지킬 수 없으면 어기지 않고, 어떤 조건을 풀면 되는지 alternatives로 돌려준다. '무조건', '반드시', '절대' 같은 표현의 조건만 free_days·blocked_times에 넣고, '가능하면', '웬만하면' 같은 조건은 avoid_times에 넣는다. 이전 후보를 일부만 바꿔 달라는 요청이면 base_candidate_id에 그 후보 id를 넣고, 바꿀 과목·분반만 must_include·exclude에 넣는다. 처음부터 새로 짜 달라는 요청이면 base_candidate_id는 null이다.",
  "strict": true,
  "input_schema": {
    "type": "object",
    "properties": {
      "base_candidate_id": { "type": ["string", "null"], "description": "수정할 이전 후보 id(예: 'tt_001'). 새로 짤 때는 null. 지정하면 이 후보에서 exclude된 것 외의 분반은 유지. 학생이 '1번'이라고 하면 가장 최근 결과에서 rank 1인 후보의 id" },
      "min_credits":      { "type": "integer", "description": "최소 학점. 말하지 않으면 15" },
      "target_credits":   { "type": "integer", "description": "목표 학점. 말하지 않으면 18" },
      "max_credits":      { "type": "integer", "description": "최대 학점. 말하지 않으면 19" },
      "credits_strict":   { "type": "boolean", "description": "'무조건 18학점'처럼 학점 범위를 반드시 지켜야 하면 true. '정확히 18학점'이면 min·target·max 모두 18에 true. 그 외에는 false" },
      "free_days":        { "type": "array", "items": { "type": "string", "enum": ["월","화","수","목","금","토"] }, "description": "반드시 비울 요일" },
      "blocked_times":    { "type": "array", "items": { "type": "object", "properties": { "day": { "type": "string", "enum": ["월","화","수","목","금","토"] }, "start": { "type": "string", "description": "HH:MM" }, "end": { "type": "string", "description": "HH:MM" } }, "required": ["day", "start", "end"], "additionalProperties": false }, "description": "반드시 비울 시간대. 예: 금요일 15시 이후면 {day:'금', start:'15:00', end:'23:59'}" },
      "avoid_times":      { "type": "array", "items": { "type": "object", "properties": { "day": { "type": "string", "enum": ["월","화","수","목","금","토"] }, "start": { "type": "string", "description": "HH:MM" }, "end": { "type": "string", "description": "HH:MM" } }, "required": ["day", "start", "end"], "additionalProperties": false }, "description": "가능하면 피할 시간대. '오전 수업 싫어'면 요일마다 09:00~12:00. '월요일 공강이면 좋겠어'처럼 강제가 아닌 공강 희망도 그 요일 전체를 여기에 넣음" },
      "must_include":     { "type": "array", "items": { "type": "string" }, "description": "꼭 넣을 과목코드(분반은 자동 선택) 또는 분반 id" },
      "exclude":          { "type": "array", "items": { "type": "string" }, "description": "뺄 과목코드 또는 분반 id" },
      "ge_areas":         { "type": "array", "items": { "type": "string" }, "description": "우선 채울 교양 영역. 빈 배열이면 부족 영역 자동" },
      "prefer_professor": { "type": "array", "items": { "type": "string" }, "description": "선호 교수명" }
    },
    "required": ["base_candidate_id", "min_credits", "target_credits", "max_credits", "credits_strict", "free_days", "blocked_times", "avoid_times", "must_include", "exclude", "ge_areas", "prefer_professor"],
    "additionalProperties": false
  }
}
```

출력:
```json
{ "status": "partial",
  "optimal": true,
  "candidates": [
    { "id": "tt_001", "rank": 1, "total_credits": 12,
      "sections": [ { "id": "COMP0204-002", "name": "자료구조", "credit": 3, "time": "월 2A,2B,3A 수 2A,2B,3A", "reason_tags": ["전공필수", "권장학기 2-1"] } ],
      "fills": { "전공필수": 6, "교양-인문": 3 },
      "omitted_required": [ { "code": "COMP0312", "name": "운영체제", "reason": "free_day_conflict", "detail": "금요일 공강 조건과 겹침" } ],
      "warnings": ["COMP0204-002 신청인원이 정원 초과(72/60)", "COMP0410 선수과목 확인 필요"] } ],
  "alternatives": [ { "id": "tt_alt_001", "relaxed": [ { "constraint": "free_days", "value": "금" } ], "description": "금요일 공강을 풀면 18학점 가능", "total_credits": 18 } ],
  "unsatisfied": ["월·금 공강을 지키면 최대 12학점 (최소 희망 15학점 미달)"] }
```

| status | 의미 |
|---|---|
| `success` | 강제 조건 충족, min~max 학점 안 |
| `partial` | 강제 조건은 지켰지만 min 학점 미달 등 목표 일부 미달 |
| `infeasible` | 강제 조건을 모두 지키는 시간표가 없다고 **증명됨** (alternatives만 반환) |
| `timeout` | 제한 시간 안에 해를 못 찾음. 불가능하다고 말하면 안 됨 |

- 조건을 푼 시간표는 `candidates`에 섞지 않고 `alternatives`에만 둔다.
- `optimal: false`면 Claude는 "조건에 맞는 시간표지만 최선인지는 확인되지 않았다"고 안내한다.
- 선수과목 `unknown` 과목은 넣을 수 있되 `warnings`에 "선수과목 확인 필요"를 붙인다.
- `omitted_required.reason`: `not_offered`(2026-2 미개설), `prereq`, `time_conflict`, `free_day_conflict`, `credit_limit`, `excluded` 중 하나.

## 3. 시간표 엔진 (CP-SAT)

### 3.1 풀기 전 검사

must_include가 2026-2 미개설이거나, 선수과목 ineligible이거나, exclude와 겹치거나, `min > max`이면 solver를 돌리지 않고 `INVALID_CONSTRAINT`와 사유를 반환한다. 조건 완화로 풀 수 있는 문제가 아니기 때문이다.

### 3.2 후보 풀 (자동으로 넣을 수 있는 분반)

| 구분 | 규칙 |
|---|---|
| 항상 제외 | 이수 완료 과목, 선수과목 ineligible 과목, 상주캠퍼스 분반(`rmrk`), 교직, exclude |
| 전공 | 학생이 입력한 학년에 맞춰, 권장 학년이 그 학년 이하인 과목만 자동 추천. 예외로 학생이 "3학년 과목인 ○○도 미리 듣고 싶어"처럼 직접 요청한 과목(must_include)은 선수과목만 충족하면 넣음 |
| 교양 | 부족 영역 과목과 ge_areas로 지정한 영역. 부족 영역이 없으면 전체 교양(점수 0, 학점 맞추기용) |
| 시간 미정 분반 | 자동으로는 안 넣음. must_include면 넣고 경고 |

must_include는 풀 규칙보다 우선한다 (3.1 검사를 통과한 경우).

### 3.3 모델

- 변수: 분반마다 `x_s ∈ {0,1}`, 과목마다 `y_c = Σ x_s` (과목 단위 집계용)
- 강제 제약: 과목당 분반 ≤ 1, 시간 슬롯당 ≤ 1, `Σ학점 ≤ min(max, 상한)`, must_include = 1, free_days·blocked_times에 걸리는 분반 = 0, `credits_strict`면 `Σ학점 ≥ min`
- `base_candidate_id`가 있으면 그 후보의 분반 중 exclude되지 않은 것을 = 1로 고정
- 단계별 최적화 (각 단계가 **OPTIMAL일 때만** 그 값을 제약으로 고정하고 다음 단계로):

| 단계 | 목표 |
|---|---|
| 1 | 권장 학기가 됐거나 지난 미이수 전공필수 **과목 수** 최대 |
| 2 | 1의 과목 수를 유지하면서, 권장 학기가 지난 과목 수 최대 |
| 3 | 목표 학점과의 차이 최소 |
| 4 | 아래 점수 합 최대 |
| 5 | avoid_times와 겹치는 슬롯 수 최소. 동점이면 선호 교수 분반 수 최대 |

4단계 점수 (초기값, 테스트하며 조정):

| 항목 | 점수 |
|---|---|
| 전공필수가 아닌 전공 과목 | 과목당 2 |
| 부족 교양 영역을 새로 채움 | 영역당 2 (같은 영역 두 번째 과목부터 0) |
| ge_areas로 지정한 영역을 채움 | 추가 1 |
| 그 외 교양 | 0 |

- 단계 하나가 FEASIBLE(최적 미증명)로 끝나면 거기서 멈추고 그 해를 `optimal: false`로 반환. 제한 시간은 단계당 2초 정도로 시작해서 측정 후 조정
- 후보 3개: 1·2단계 최적값을 유지한 채 "앞선 후보들과 과목 구성이 1개 이상 다름" 제약을 넣고 3·4·5단계를 다시 풀기. 과목 구성이 다른 해가 없으면 "분반이 하나 이상 다름"으로 한 번 더. 그래도 없으면 3개를 억지로 채우지 않음

### 3.4 대안(alternatives) 만들기

| 언제 | 방법 |
|---|---|
| `infeasible` | 완화 가능한 강제 조건마다 `relax_k ∈ {0,1}`를 두고 비용 합을 최소화. 조건 여러 개를 같이 풀어야 하는 경우도 한 번에 찾아짐 |
| `partial` (min 학점 미달) | 위와 같은 문제에 `Σ학점 ≥ min`을 강제로 추가해서, 무엇을 풀면 학점이 채워지는지 찾음 |

- 완화 조합이 정해지면 그 조건만 푼 상태로 3.3의 1~5단계를 다시 돌려 시간표를 만든다.
- 앞에서 찾은 완화 조합을 금지하고 다시 풀어 최대 3개.

| 완화 대상 | 비용 |
|---|---|
| blocked_times 시간대 하나 | 1 |
| free_days 하루 | 2 |
| credits_strict 범위 | 2 |
| must_include 과목 하나 | 5 |

## 4. 역할 분리

| 기능 | Claude | Python |
|---|---|---|
| 자연어 조건 해석, 강제/선호 구분 | O | 입력 검증 |
| 도구 선택 | O | 실행 |
| 검색·학점·선수과목·충돌·조합 | 요청만 | O |
| 추천 이유·대안 설명 | O (reason_tags, warnings, alternatives 기반) | 근거 제공 |

## 5. 팀이 정할 것

- 졸업 요건 JSON (트랙별 이수구분 학점, 전공필수 목록과 권장 학기, 교양 영역 요건): 조가연·김재영
- 선수과목 JSON (2.3의 verified 형식, 선수과목 없는 전공 과목도 빠짐없이 `required: []`로 등록)
- 교양 영역 매핑 (교양 703분반에 영역 붙이기)
- 수강 학점 상한 학칙 확인
- 이수내역 성적 코드 종류 확인 (F, NP 외에 W, U 등 미이수로 봐야 할 코드가 있는지)
- 교시와 시각 대응표 (1A가 몇 시인지, `lssnsRealTimeInfo`로 확인)
- 분반 번호 형식 (`sbjetDvnno`가 '001'인지 '1'인지), 토요일 수업 분반 유무
