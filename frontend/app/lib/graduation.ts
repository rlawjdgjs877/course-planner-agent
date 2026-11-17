export type Requirement = { label: string; value: string };
export type GraduationProfile = { id: string; name: string; basis: string; total: number; required: string[]; rows: Requirement[]; notes: string[]; sourcePage: number; sourceUrl: string };
const common = { label: "공통 인정요건", value: "전공 졸업요건과 경북대학교 졸업자격인정제 모두 충족" };
export const graduationProfiles: GraduationProfile[] = [
 { id: "advanced", name: "심화컴퓨팅전공", basis: "2026학년도 기준", total: 130, required: ["기초프로그래밍", "자료구조", "알고리즘1", "종합설계프로젝트1"], sourcePage: 1, sourceUrl: "https://aicollege.knu.ac.kr/sub3_2_a.php", rows: [
 { label: "학점 구성", value: "총 130학점: 전공 72 · 교양 30 · 그 외 28학점" },
 { label: "교양필수", value: "첨성인기초 / 첨성인핵심 / SDG교양" },
 { label: "공인 영어성적", value: "TOEIC 700점 이상 또는 이에 상응하는 공인 영어성적" },
 { label: "연구활동", value: "3학점 이상 또는 현장실습 대체 인정" },
 { label: "졸업심사", value: "전공 학업역량평가 응시" }, common],
 notes: ["연구활동·현장실습 대체와 영어 대체 인정은 학부 심화컴퓨팅 공지를 확인하세요.", "교양 이수 세부기준은 해당 학년도 학사안내를 따릅니다."] },
 { id: "research", name: "첨단컴퓨팅연구전공", basis: "2026학년도 기준", total: 130, required: ["기초프로그래밍", "자료구조", "첨단컴퓨팅특강", "알고리즘1"], sourcePage: 2, sourceUrl: "https://aicollege.knu.ac.kr/sub3_3_a.php", rows: [
 { label: "학점 구성", value: "총 130학점: 전공 72 · 교양 30 · 대학원 교과목 9 · 그 외 19학점" },
 { label: "교양필수", value: "첨성인기초 / 첨성인핵심 / SDG교양" },
 { label: "공인 영어성적", value: "TOEIC 700점 이상 또는 이에 상응하는 공인 영어성적" },
 { label: "연구실 활동", value: "3개 학기 이상 연구활동 수행" },
 { label: "연구행사", value: "공식 연구행사 3회 이상 참석 및 증빙자료 제출" },
 { label: "졸업심사", value: "졸업학기 논문 형식 연구보고서 제출 및 연구결과 발표 1회 이상" }, common],
 notes: ["연구활동 3개 학기는 연속이 아니어도 되며, 학기별 확인서를 제출하고 S/U로 평가합니다.", "연구행사는 BK·학부 세미나, 학술대회 등 지도교수가 인정하는 행사여야 합니다.", "발표는 구두·포스터 발표가 가능하며 공인 학회 발표로 대체할 수 있습니다.", "대학원 교과목 9학점은 학·석사 연계 또는 관련 규정에 따라 이수할 수 있습니다."] },
 { id: "ai", name: "인공지능컴퓨팅전공", basis: "2026학년도 기준", total: 130, required: ["컴퓨팅사고와SW코딩", "인공지능수학기초", "자료구조", "알고리즘1", "인공지능", "기계학습개론", "종합설계프로젝트1"], sourcePage: 3, sourceUrl: "https://aicollege.knu.ac.kr/sub3_4_a.php", rows: [
 { label: "학점 구성", value: "총 130학점 · 전공 72학점" },
 { label: "현장실습", value: "3학점 이상" },
 { label: "실용영어", value: "졸업자격인정제의 실용영어 영역 충족 (문서에 TOEIC 700점 별도 요건 없음)" },
 { label: "교양 이수", value: "전공 및 교양과목 이수 세부기준은 해당 학년도 학칙 적용" }, common],
 notes: ["이 전공에는 TOEIC 700점을 별도 독립 요건으로 적용하지 않았습니다.", "학년도별 기준이 다르므로 본인의 해당 학년도 졸업기준을 확인하세요."] },
 { id: "platform", name: "플랫폼SW·데이터과학전공", basis: "홈페이지 표시: 2025학년도까지 · ABEEK 기준", total: 140, required: [], sourcePage: 4, sourceUrl: "https://aicollege.knu.ac.kr/sub3_5_a.php", rows: [
 { label: "영어성적", value: "문서의 각 학번 구간 모두 TOEIC 700점 이상" },
 { label: "설계 학점", value: "공학전공 학점 안에 설계 14학점 포함 (별도 가산하지 않음)" },
 { label: "졸업포트폴리오", value: "비교과 활동 3건 이상 증빙 및 KEESS 등록 등 · 종합설계프로젝트 1·2 설계포트폴리오 포함" },
 { label: "공통 인정요건", value: "ABEEK 프로그램 요건 및 경북대학교 졸업자격인정제 모두 충족" }],
 notes: ["원문 표의 ‘2012학번~’와 ‘2021학번~’ 중복 구간은 후속 기준인 2021학번 이후로 구분한 자료입니다.", "영어 성적은 KEESS 비교과영역에 스캔파일 등록 및 안내된 담당자 이메일로 제출하도록 안내되어 있습니다.", "설계포트폴리오에는 강의계획서, 수행 자료, 발표·보고서, 작품 결과 화면(필수) 등이 포함됩니다.", "선후수 이수체계와 편입·전과생 별도 절차를 확인하세요. 이 PDF에는 전공필수 전체 목록이 없습니다."] },
 { id: "global", name: "글로벌SW융합전공", basis: "홈페이지 표시: 2025학년도까지 · 세 트랙 중 하나 충족", total: 130, required: [], sourcePage: 5, sourceUrl: "https://aicollege.knu.ac.kr/sub3_6_a.php", rows: [
 { label: "총 졸업학점", value: "130학점 이상" },
 { label: "SW전공역량", value: "해당 전공 교육과정 내 전공학점 51학점 이상 · 다중전공·해외대학·대학원·타 전공학점 제외" }, common],
 notes: ["현장실습·해외어학연수·해외 인턴십 학점은 총 졸업학점에 포함되지만, 최소 교양학점 또는 SW전공역량 학점에는 포함되지 않습니다.", "졸업포트폴리오에 이수학점·영어성적·해외프로그램·창업·현장실습 증빙을 수록하도록 안내합니다.", "스타트업 창업은 직접 창업 외 대체 유형이 있으므로 원문 세부기준을 확인하세요. 이 PDF에는 전공필수 전체 목록이 없습니다."] },
];
export const platformCohorts = [
 { id: "2010", name: "2010~2011학번", total: 140, value: "총 140 · 기본소양 15(외국어 제외) · 전공기반 21 · 공학전공 60(설계 14 포함) · ABEEK 96학점", practice: "현장실습: 문서 표에 별도 요건 없음" },
 { id: "2012", name: "2012~2020학번", total: 150, value: "총 150 · 기본소양 15(외국어 제외) · 전공기반 21 · 공학전공 75(설계 14 포함) · ABEEK 111학점", practice: "현장실습 3학점 이상" },
 { id: "2021", name: "2021학번 이후", total: 140, value: "총 140 · 기본소양 15(외국어 제외) · 전공기반 18 · 공학전공 60(설계 14 포함) · ABEEK 93학점", practice: "현장실습 3학점 이상" },
];
export const globalCohorts = [
 { id: "2017", name: "2017학년도", value: "교양 30학점" },
 { id: "2018", name: "2018~2022학년도", value: "교양 24~42학점 · 해당 학년도 세부기준 확인" },
 { id: "2023", name: "2023학년도 이후", value: "교양 30학점" },
];
export const globalTracks = [
 { id: "multi", name: "다중전공 트랙", value: "TOEIC 700점 이상 · 해외대학 인정학점 9학점 이상 · 현장실습 3학점 이상 · 창업교과목 9학점 이상 · 스타트업 창업 · 다중전공 필수 · 종합설계교과목 3학점 이상(2022학번부터)" },
 { id: "overseas", name: "해외복수학위 트랙", value: "TOEIC 800점 이상 · 해외복수학위과정 이수 또는 교환학생 1년 이상 · 창업교과목 3학점 이상 · 다중전공 선택" },
 { id: "master", name: "학·석사연계 트랙", value: "TOEIC 700점 이상 · 해외대학 인정학점 6학점 이상 · 현장실습 3학점 이상 · 다중전공 선택" },
];
