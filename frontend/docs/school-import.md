# Plann 학교 이수 과목 불러오기

## 실제로 지원하는 정보

기존 백엔드 `/import/knu/*` API를 직접 호출합니다. Next.js rewrites나 서버 프록시는 추가하지 않았습니다.
Plann 안에 백엔드가 제공하는 학교 화면을 표시하고, 사용자가 그 화면에 직접 로그인합니다.
학번·비밀번호 전용 Plann 로그인 API를 새로 만들거나 학교 로그인 절차를 우회하지 않습니다.

응답에 포함되는 것은 `code`, `name`, `credits`, `category`뿐입니다.
학년·전공·입학년도·학적 상태는 이 API가 반환하지 않으므로 직접 확인합니다.
백엔드는 F·NP를 제외하지만 다른 미이수·취소·재이수와 학기별 제외 여부는 실제 응답 검증이 필요합니다.
2026-2 수강 중인 과목을 사전 이수 과목으로 잘못 반영하지 않았는지 사용자에게 확인을 안내합니다.

## 로컬 실행

백엔드 폴더에서 기존 가상환경으로 실행합니다.

```bash
pip install -r requirements-import.txt
```

Chrome이 없으면 Playwright의 Chromium을 설치합니다.

```bash
python -m playwright install chromium
```

`backend/.env`에 다음 로컬 전용 값을 설정하고 백엔드를 재시작합니다.

```dotenv
KNU_IMPORT_ENABLED=1
KNU_IMPORT_ALLOW_REMOTE=0
```

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

프론트엔드는 `http://localhost:3000`에서 실행하세요. 백엔드의 기본 CORS 허용 주소입니다.
다른 개발 주소를 쓰면 백엔드의 허용 Origin도 실제 주소와 맞춰야 합니다.
`NEXT_PUBLIC_API_BASE`가 없으면 localhost에서만 `http://localhost:8000`으로 연결합니다.
배포 환경에는 HTTPS 백엔드 주소를 명시해야 하며, 지정하지 않으면 직접 입력으로 안내합니다.
공개 배포에서 원격 사용자 허용은 기존 백엔드 문서의 검토 범위이며 이 변경으로 자동 활성화하지 않습니다.
학교 불러오기를 Next.js rewrites로 프록시하지 마세요. 모든 사용자가 루프백으로 보이는 문제가 있습니다.

## 세션과 저장

- 첫 화면의 개인정보 제공 동의 영역에서 수집·이용 및 학교 연결 서버 처리에 각각 동의한 뒤 버튼을 누릅니다.
- 수집 항목, 이용 목적, 처리 경로, 보관·삭제, 동의 거부 안내를 펼쳐 볼 수 있습니다. 필수 항목 하나라도 미동의면 로그인 창이 열리지 않습니다.
- 동의 선택은 현재 페이지 메모리에만 유지하며 브라우저 재방문 시 다시 확인합니다. 직접 입력은 해당 동의 없이 이용할 수 있습니다.
- 버튼을 누르면 Plann 위에 학교 로그인 대화상자가 바로 열리고 연결을 자동 시작합니다. 추가로 화면 열기 버튼을 누를 필요가 없습니다.
- 닫기·Escape는 연결을 정리합니다. 학교 원격 화면에 초점을 둔 상태의 Escape·Tab은 학교 화면으로 전달합니다.
- 조회 결과를 확인해 반영하면 대화상자를 닫고 이수 내역 화면으로 이동합니다.
- 연결 토큰은 React ref 메모리에만 보관하고 URL·localStorage·sessionStorage에 넣지 않습니다.
- 학교 화면은 표시용 메모리에만 두며, 조회 완료·연결 종료·화면 이동 시 지웁니다.
- 화면 이동·페이지 종료 시 `/stop`을 요청합니다. 네트워크 실패 시 서버의 만료 처리가 최종 정리합니다.
- 한글·붙여넣기 보조 입력칸은 가림 처리하고, 전송 시 DOM 값부터 즉시 지웁니다.
- 확인 후 반영 버튼을 눌러야 과목이 저장됩니다. 성적·비밀번호·쿠키·연결 토큰·이미지는 저장하지 않습니다.
- 개설 목록 매칭은 과목코드가 정확히 같은 경우에만 수행합니다. 이름 유사도나 순서로 추측하지 않습니다.
- 개설 목록에 없는 과거 과목도 별도 이수 내역에 보존하며, 제거하면 연결된 체크도 해제합니다.
- 실제 학교 로그인 성공, 학교 화면 변경 대응, 재이수 규칙은 실제 계정으로 사용자가 확인해야 합니다.

## 수정할 파일

- `app/lib/knu-import.ts`: API 주소·요청·응답·세션 종료
- `app/components/school-import-panel.tsx`: 원격 화면, 자동 연결, 입력 전달, 결과 확인
- `app/components/school-import-dialog.tsx`: Plann 안의 로그인 창과 닫기·초점 이동
- `app/lib/imported-courses.ts`: 저장 필드 정리, 중복 병합, 과목코드 매칭
- `app/components/imported-course-summary.tsx`: 과거 과목을 포함한 이수 내역
- `app/components/academic-input-choice.tsx`: 첫 화면 학교 로그인 버튼
- `app/components/school-privacy-consent.tsx`: 개인정보 안내·필수 동의 UI
- `app/lib/school-privacy.ts`: 필수 동의 충족 여부 검사

## 검증

```bash
node --experimental-strip-types scripts/validate-imported-courses.mjs
```

백엔드의 Playwright 설치 환경과 실행 중인 프론트엔드가 있으면 다음 모의 UI 검사를 실행할 수 있습니다.

```bash
python scripts/test-school-import-ui.py http://localhost:3105
```

이 검사는 모든 `/import/knu/*` 요청을 모의 응답으로 대체하며 실제 학교 계정을 사용하지 않습니다.
동의, 입력 전달·즉시 지우기, 토큰 비저장, 과목 반영·제거, 화면 이동 시 종료와 사용 불가 상태를 검사합니다.
