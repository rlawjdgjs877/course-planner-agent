# Plann 프론트엔드

경북대학교 컴퓨터학부 학생을 위한 Finder 스타일의 학업 관리 화면입니다.
Next.js App Router, TypeScript, Tailwind CSS로 구현했습니다.

## 실행하기

Node.js와 npm을 설치한 뒤, 저장소 루트에서 실행합니다.

```bash
cd frontend
npm ci
npm run dev
```

http://localhost:3000 에서 확인할 수 있습니다. 백엔드의 http://localhost:8000 시연 화면과 별개입니다.
Windows PowerShell에서 npm.ps1 실행 제한이 뜨면 `npm.cmd ci`, `npm.cmd run dev`를 사용하세요.

## 검사와 빌드

```bash
npm run lint
npm run build
npm run start
```

Vercel에서 배포할 때 Root Directory는 `frontend`로 지정합니다.

## 현재 기능

- Finder 스타일 화면, 학년 폴더, 문서 수록 과목 검색 및 이수 체크
- 학교 로그인 화면을 통한 이수 과목 불러오기, 수동 학생 정보 입력
- 심컴·인컴·첨컴·플솦·글솦별 졸업요건과 선후수 과목 안내
- 희망 학점·공강 요일 저장 및 미이수 과목 확인
- 선택 정보는 사용자 브라우저의 localStorage에 저장

학교 이수 과목 불러오기는 팀 백엔드에 연결했습니다. 시간표 자동 생성과 AI 채팅은 아직 연결하지 않았습니다.
학교 로그인 화면을 통한 과목 조회와 일반 URL 저장은 별개이며, 링크만 저장해서 학적 정보를 읽지는 않습니다.
PDF에 없는 과목별 학년·학점·강의 시간은 추측하지 않으며 졸업 충족 여부를 자동 판정하지 않습니다.

## 주요 파일

- `app/components/`: 화면 컴포넌트
- `app/lib/`: 과목, 졸업요건, 선후수 관계, 학생 구분 데이터
- `app/globals.css`: 화면 스타일
- `public/documents/`: 사용자가 제공한 학업 안내 PDF 원문

`node_modules`, `.next`, `.env` 및 개인의 학적·이수 기록은 저장소에 올리지 않습니다.

## 2026년 2학기 JSON 개설 데이터

제공받은 전공·교양 JSON 10개의 816개 조회 항목을 781개 분반, 254개 과목코드로 정리했습니다.
PDF의 기존 과목과 합친 이수 체크 목록은 288개이며 기존 66개 과목의 저장 ID를 유지합니다.
동일 분반의 전공별 학년·이수 구분은 자료별 기록으로 보존합니다.

- 원문: `data/course-sources/*.json` (10개 파일, 원본 그대로 보존)
- 화면용 데이터: `app/lib/data/offerings.json`, `sources.json`, `import-report.json`
- 다시 생성: `python scripts/import-course-data.py`
- 누락·중복 및 참조 검사: `python scripts/validate-course-data.py`

강좌 검색은 전공·교양 분류, 과목·교수·강좌번호, 학년, 요일 필터와 페이지 이동을 지원합니다.
조회 인원은 파일 생성 시점의 값이며 실시간 잔여석이 아닙니다.
수업 시간이 없는 2개 분반은 미기재로 유지합니다. 백엔드 API 연동과 시간표 자동 생성은 아직 구현하지 않았습니다.

## 도구 정의 v3.2 참고 반영

최소·목표·최대 학점, 필수/선호 공강·회피 시간, 포함/제외 과목, 선호 교수 조건을 저장하고 JSON으로 내려받을 수 있습니다.
개설 강좌를 직접 시간표에 담으면 시간 충돌·같은 과목 분반 중복·시간 미정을 검사합니다.
자동 생성 엔진, AI 설명, 2025 교육과정 학점 계산과 선수과목 적격 판정은 아직 연결하지 않았습니다.

반영 범위와 후속 연결 지점: `docs/agent-tools-v3.2-integration.md`.
충돌 검사 테스트: `node --experimental-strip-types scripts/validate-planning.mjs` (Node.js 22 이상).

## 학교 로그인으로 이수 과목 불러오기

첫 화면의 **학교 로그인으로 시작**에서 백엔드 `/import/knu/*`에 연결합니다.
학교 화면에 사용자가 직접 로그인한 뒤 조회 결과를 확인해 이수 체크에 반영합니다.
학년·전공 등 전체 학적 정보는 이 API 응답에 없으므로 별도 확인이 필요합니다.
아이디·비밀번호·연결 토큰·학교 화면은 브라우저 저장소에 저장하지 않습니다.

실행 설정과 저장 범위, 모의 UI 검사 방법은 `docs/school-import.md`를 확인하세요.
로컬 개발은 `localhost:3000` 프론트엔드와 `localhost:8000` 백엔드를 직접 연결하며 Next.js rewrites는 사용하지 않습니다.
이 기능을 사용하려면 백엔드의 선택 의존성 `requirements-import.txt`를 설치하고 로컬 `.env`의 `KNU_IMPORT_ENABLED=1` 설정 후 재시작해야 합니다.

학교 로그인은 첫 화면에서 연결 안내에 동의한 뒤 버튼을 누르면 Plann 안의 대화상자에 자동으로 표시됩니다.
별도의 '학교 화면 열기' 단계는 없으며 닫기 버튼으로 연결을 종료할 수 있습니다.
학교 자체 점검·장애 화면도 그대로 전달되므로 해당 경우에는 학교 서비스 복구가 필요합니다.
