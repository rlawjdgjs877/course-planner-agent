# Campus Finder 프론트엔드

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
- 학적·이수내역 링크 입력·저장, 접힌 수동 학생 정보 입력
- 심컴·인컴·첨컴·플솦·글솦별 졸업요건과 선후수 과목 안내
- 희망 학점·공강 요일 저장 및 미이수 과목 확인
- 선택 정보는 사용자 브라우저의 localStorage에 저장

현재는 독립 실행하는 프론트엔드이며 팀 저장소의 백엔드 API와 아직 연결하지 않았습니다.
링크를 저장해도 학적·이수 학점을 실제로 가져오지 않습니다.
PDF에 없는 과목별 학년·학점·강의 시간은 추측하지 않으며 졸업 충족 여부를 자동 판정하지 않습니다.

## 주요 파일

- `app/components/`: 화면 컴포넌트
- `app/lib/`: 과목, 졸업요건, 선후수 관계, 학생 구분 데이터
- `app/globals.css`: 화면 스타일
- `public/documents/`: 사용자가 제공한 학업 안내 PDF 원문

`node_modules`, `.next`, `.env` 및 개인의 학적·이수 기록은 저장소에 올리지 않습니다.
