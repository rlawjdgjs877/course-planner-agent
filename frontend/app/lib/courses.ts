export type Course = { id: string; name: string; year: number; years?: number[]; allGrades?: boolean; category: string; credits: number | null; creditOptions?: number[]; semester: string; sourceIds?: string[]; code?: string };
export const courses: Course[] = [
  {
    "id": "knu-1",
    "name": "기초프로그래밍",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-2",
    "name": "프로그래밍기초",
    "year": 1,
    "category": "전공",
    "credits": 6.0,
    "semester": "2026년 2학기",
    "years": [
      1
    ],
    "sourceIds": [
      "ai"
    ],
    "creditOptions": [
      6.0
    ],
    "code": "COMP0204",
    "allGrades": false
  },
  {
    "id": "knu-3",
    "name": "자료구조",
    "year": 0,
    "category": "공학전공 / 전공필수",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      1,
      2
    ],
    "sourceIds": [
      "advanced",
      "computing",
      "research"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "COME0331",
    "allGrades": false
  },
  {
    "id": "knu-4",
    "name": "알고리즘1",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-5",
    "name": "알고리즘2",
    "year": 3,
    "category": "공학전공",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      3
    ],
    "sourceIds": [
      "computing"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "COMP0320",
    "allGrades": false
  },
  {
    "id": "knu-6",
    "name": "객체지향프로그래밍기초",
    "year": 1,
    "category": "전공",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      1
    ],
    "sourceIds": [
      "research"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "COMP0336",
    "allGrades": false
  },
  {
    "id": "knu-7",
    "name": "소프트웨어설계",
    "year": 2,
    "category": "공학전공 / 전공",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      2
    ],
    "sourceIds": [
      "ai",
      "computing",
      "global"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "COMP0224",
    "allGrades": false
  },
  {
    "id": "knu-8",
    "name": "소프트웨어공학",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-9",
    "name": "종합설계프로젝트1",
    "year": 3,
    "category": "공학전공 / 전공필수",
    "credits": 4.0,
    "semester": "2026년 2학기",
    "years": [
      3
    ],
    "sourceIds": [
      "ai",
      "computing"
    ],
    "creditOptions": [
      4.0
    ],
    "code": "ITEC0401",
    "allGrades": false
  },
  {
    "id": "knu-10",
    "name": "종합설계프로젝트2",
    "year": 4,
    "category": "공학전공",
    "credits": 4.0,
    "semester": "2026년 2학기",
    "years": [
      4
    ],
    "sourceIds": [
      "computing",
      "platform"
    ],
    "creditOptions": [
      4.0
    ],
    "code": "ITEC0402",
    "allGrades": false
  },
  {
    "id": "knu-11",
    "name": "시스템프로그래밍",
    "year": 2,
    "category": "공학전공 / 전공",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      2
    ],
    "sourceIds": [
      "ai",
      "computing"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "ELEC0462",
    "allGrades": false
  },
  {
    "id": "knu-12",
    "name": "운영체제",
    "year": 2,
    "category": "전공 / 전공필수",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      2
    ],
    "sourceIds": [
      "ai",
      "global"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "COMP0312",
    "allGrades": false
  },
  {
    "id": "knu-13",
    "name": "클라우드컴퓨팅",
    "year": 4,
    "category": "공학전공 / 전공",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      4
    ],
    "sourceIds": [
      "ai",
      "computing",
      "global",
      "platform"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "GLSO0227",
    "allGrades": false
  },
  {
    "id": "knu-14",
    "name": "데이타통신",
    "year": 2,
    "category": "전공",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      2
    ],
    "sourceIds": [
      "global"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "COMP0323",
    "allGrades": false
  },
  {
    "id": "knu-15",
    "name": "컴퓨터망",
    "year": 3,
    "category": "전공",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      3
    ],
    "sourceIds": [
      "global"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "COMP0414",
    "allGrades": false
  },
  {
    "id": "knu-16",
    "name": "웹보안",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-17",
    "name": "이산수학",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-18",
    "name": "오토마타및형식언어",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-19",
    "name": "컴파일러",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-20",
    "name": "인공지능수학기초",
    "year": 1,
    "category": "전공필수",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      1
    ],
    "sourceIds": [
      "ai"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "COMP0454",
    "allGrades": false
  },
  {
    "id": "knu-21",
    "name": "선형대수",
    "year": 1,
    "category": "전공",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      1
    ],
    "sourceIds": [
      "advanced",
      "research"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "MTED0231",
    "allGrades": false
  },
  {
    "id": "knu-22",
    "name": "확률및통계",
    "year": 2,
    "category": "전공 / 전공기반",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      2
    ],
    "sourceIds": [
      "ai",
      "computing"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "COME0311",
    "allGrades": false
  },
  {
    "id": "knu-23",
    "name": "인공지능수학심화",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-24",
    "name": "정보보호론",
    "year": 4,
    "category": "공학전공 / 전공",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      4
    ],
    "sourceIds": [
      "ai",
      "computing",
      "global",
      "platform"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "COME0368",
    "allGrades": false
  },
  {
    "id": "knu-25",
    "name": "데이터베이스",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-26",
    "name": "문제해결기반공학연수실습",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-27",
    "name": "증강현실",
    "year": 4,
    "category": "공학전공 / 전공",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      4
    ],
    "sourceIds": [
      "ai",
      "computing",
      "global",
      "platform"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "COMP0436",
    "allGrades": false
  },
  {
    "id": "knu-28",
    "name": "자바프로그래밍",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-29",
    "name": "오픈소스프로그래밍",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-30",
    "name": "모바일앱프로그래밍1",
    "year": 0,
    "category": "공학전공 / 전공",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      3,
      4
    ],
    "sourceIds": [
      "ai",
      "computing",
      "global"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "COMP0328",
    "allGrades": false
  },
  {
    "id": "knu-31",
    "name": "컴퓨팅사고와SW코딩",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-32",
    "name": "고급문제해결",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-33",
    "name": "대규모병렬컴퓨팅",
    "year": 4,
    "category": "공학전공 / 전공",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      4
    ],
    "sourceIds": [
      "ai",
      "computing",
      "global",
      "platform"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "ITEC0418",
    "allGrades": false
  },
  {
    "id": "knu-34",
    "name": "자료구조응용",
    "year": 2,
    "category": "공학전공",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      2
    ],
    "sourceIds": [
      "computing"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "COMP0216",
    "allGrades": false
  },
  {
    "id": "knu-35",
    "name": "데이터통신",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-36",
    "name": "데이터마이닝이론및응용",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-37",
    "name": "기초창의공학설계",
    "year": 1,
    "category": "전공",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      1
    ],
    "sourceIds": [
      "ai"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "COMP0205",
    "allGrades": false
  },
  {
    "id": "knu-38",
    "name": "컴퓨터구조",
    "year": 2,
    "category": "공학전공",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      2
    ],
    "sourceIds": [
      "computing"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "COMP0411",
    "allGrades": false
  },
  {
    "id": "knu-39",
    "name": "인공지능과컴퓨팅",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-40",
    "name": "인공지능",
    "year": 2,
    "category": "전공 / 전공필수",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      2
    ],
    "sourceIds": [
      "ai",
      "global"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "COMP0324",
    "allGrades": false
  },
  {
    "id": "knu-41",
    "name": "기계학습개론",
    "year": 3,
    "category": "공학전공 / 전공",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      3
    ],
    "sourceIds": [
      "computing",
      "global"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "ITEC0417",
    "allGrades": false
  },
  {
    "id": "knu-42",
    "name": "딥러닝",
    "year": 3,
    "category": "전공",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      3
    ],
    "sourceIds": [
      "ai"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "MOBI0224",
    "allGrades": false
  },
  {
    "id": "knu-43",
    "name": "인공지능시스템",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-44",
    "name": "정보이론기초",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-45",
    "name": "데이터과학기초",
    "year": 2,
    "category": "전공 / 전공기반",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      2
    ],
    "sourceIds": [
      "ai",
      "computing"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "ITEC0419",
    "allGrades": false
  },
  {
    "id": "knu-46",
    "name": "강화학습개론",
    "year": 3,
    "category": "전공",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      3
    ],
    "sourceIds": [
      "ai"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "CAIB0216",
    "allGrades": false
  },
  {
    "id": "knu-47",
    "name": "신경망개론",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-48",
    "name": "뇌인지공학개론",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-49",
    "name": "영상이해",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-50",
    "name": "컴퓨터비전",
    "year": 0,
    "category": "공학전공 / 전공",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      3,
      4
    ],
    "sourceIds": [
      "ai",
      "computing",
      "global"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "ITEC0424",
    "allGrades": false
  },
  {
    "id": "knu-51",
    "name": "음성인식",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-52",
    "name": "지능HCI",
    "year": 4,
    "category": "공학전공 / 전공",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      4
    ],
    "sourceIds": [
      "ai",
      "computing"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "COMP0455",
    "allGrades": false
  },
  {
    "id": "knu-53",
    "name": "자연어처리개론",
    "year": 0,
    "category": "공학전공 / 전공",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      3,
      4
    ],
    "sourceIds": [
      "ai",
      "computing",
      "global",
      "platform"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "CAIB0211",
    "allGrades": false
  },
  {
    "id": "knu-54",
    "name": "정보검색",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-55",
    "name": "의료인공지능",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-56",
    "name": "생물정보학개론",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-57",
    "name": "AI심화글쓰기",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-58",
    "name": "첨단컴퓨팅특강",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-59",
    "name": "기업가정신과벤처창업",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-60",
    "name": "창업과경영",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-61",
    "name": "회계와사회생활",
    "year": 0,
    "category": "교양",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      1,
      3
    ],
    "sourceIds": [
      "core-humanities",
      "global"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "CLTR0089",
    "allGrades": false
  },
  {
    "id": "knu-62",
    "name": "나의첫사업제안서",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-63",
    "name": "알기쉬운창업마케팅과스피치",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-64",
    "name": "스타트업설계",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-65",
    "name": "IT지식재산권",
    "year": 0,
    "category": "문서 수록 과목",
    "credits": null,
    "semester": "개설 정보 미확인",
    "years": [],
    "sourceIds": [],
    "creditOptions": []
  },
  {
    "id": "knu-66",
    "name": "SW창업프로젝트",
    "year": 4,
    "category": "전공",
    "credits": 3.0,
    "semester": "2026년 2학기",
    "years": [
      4
    ],
    "sourceIds": [
      "global"
    ],
    "creditOptions": [
      3.0
    ],
    "code": "GLSO0229",
    "allGrades": false
  },
  {
    "id": "course-CLTR0003",
    "name": "실용화법",
    "code": "CLTR0003",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "advanced",
      "ai",
      "literacy",
      "research"
    ]
  },
  {
    "id": "course-CLTR0011",
    "name": "중국어1",
    "code": "CLTR0011",
    "year": 0,
    "years": [
      1,
      2
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0012",
    "name": "중국어2",
    "code": "CLTR0012",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0016",
    "name": "교양한문",
    "code": "CLTR0016",
    "year": 0,
    "years": [
      1,
      2
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0017",
    "name": "실용한자",
    "code": "CLTR0017",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0022",
    "name": "프랑스어1",
    "code": "CLTR0022",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0023",
    "name": "프랑스어2",
    "code": "CLTR0023",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0024",
    "name": "독일어1",
    "code": "CLTR0024",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0025",
    "name": "독일어2",
    "code": "CLTR0025",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0032",
    "name": "일어 I",
    "code": "CLTR0032",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0033",
    "name": "일어 II",
    "code": "CLTR0033",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0034",
    "name": "영어 I",
    "code": "CLTR0034",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0035",
    "name": "영어 II",
    "code": "CLTR0035",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0036",
    "name": "러시아어 I",
    "code": "CLTR0036",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0037",
    "name": "러시아어 II",
    "code": "CLTR0037",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0038",
    "name": "스페인어",
    "code": "CLTR0038",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0040",
    "name": "스페인어 2",
    "code": "CLTR0040",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0041",
    "name": "한국사",
    "code": "CLTR0041",
    "year": 0,
    "years": [
      1,
      2,
      4
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양 / 기본소양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0042",
    "name": "동양의역사와문화",
    "code": "CLTR0042",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0043",
    "name": "서양의 역사와 문화",
    "code": "CLTR0043",
    "year": 0,
    "years": [
      1,
      2,
      4
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양 / 기본소양",
    "sourceIds": [
      "computing",
      "core-humanities",
      "global"
    ]
  },
  {
    "id": "course-CLTR0044",
    "name": "철학의이해",
    "code": "CLTR0044",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0045",
    "name": "논리와 비판적 사고",
    "code": "CLTR0045",
    "year": 0,
    "years": [
      1,
      2
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0048",
    "name": "철학사상사",
    "code": "CLTR0048",
    "year": 0,
    "years": [
      1,
      3
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0058",
    "name": "자원봉사활동",
    "code": "CLTR0058",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0061",
    "name": "정치학의 이해",
    "code": "CLTR0061",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0069",
    "name": "인간과성",
    "code": "CLTR0069",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0073",
    "name": "현대사회와 윤리",
    "code": "CLTR0073",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0078",
    "name": "심리학의이해",
    "code": "CLTR0078",
    "year": 0,
    "years": [
      1,
      2
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0082",
    "name": "매스컴과 사회",
    "code": "CLTR0082",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0083",
    "name": "경제의이해",
    "code": "CLTR0083",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0085",
    "name": "경영의이해",
    "code": "CLTR0085",
    "year": 0,
    "years": [
      1,
      3,
      4
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양 / 기본소양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0090",
    "name": "현대사회와법",
    "code": "CLTR0090",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0091",
    "name": "현대사회와행정",
    "code": "CLTR0091",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0094",
    "name": "문화인류학의이해",
    "code": "CLTR0094",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0095",
    "name": "프랑스문화의이해",
    "code": "CLTR0095",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0096",
    "name": "영상으로보는독일문화",
    "code": "CLTR0096",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0101",
    "name": "인간과자연",
    "code": "CLTR0101",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0102",
    "name": "자연과학의이해",
    "code": "CLTR0102",
    "year": 0,
    "years": [
      1,
      2
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0103",
    "name": "과학사의이해",
    "code": "CLTR0103",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0106",
    "name": "화학의신비",
    "code": "CLTR0106",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0107",
    "name": "자연과환경",
    "code": "CLTR0107",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0108",
    "name": "생명의신비",
    "code": "CLTR0108",
    "year": 0,
    "years": [
      1,
      2
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0112",
    "name": "생활속의통계",
    "code": "CLTR0112",
    "year": 0,
    "years": [
      1,
      2,
      3
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0118",
    "name": "생활과원예",
    "code": "CLTR0118",
    "year": 0,
    "years": [
      2
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0120",
    "name": "아름다운 지구",
    "code": "CLTR0120",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0130",
    "name": "프랑스문학의 이해",
    "code": "CLTR0130",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0133",
    "name": "국악의 이해",
    "code": "CLTR0133",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0156",
    "name": "지구과학",
    "code": "CLTR0156",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양 / 전공기반",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0174",
    "name": "현대사회와 스포츠",
    "code": "CLTR0174",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0180",
    "name": "골프",
    "code": "CLTR0180",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 1.0,
    "creditOptions": [
      1.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0181",
    "name": "호신술",
    "code": "CLTR0181",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 1.0,
    "creditOptions": [
      1.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0195",
    "name": "C/C++프로그래밍기초",
    "code": "CLTR0195",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양 / 전공기반",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0205",
    "name": "대학글쓰기",
    "code": "CLTR0205",
    "year": 0,
    "years": [
      1,
      3
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양 / 기본소양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0208",
    "name": "심화글쓰기",
    "code": "CLTR0208",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양 / 기본소양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0210",
    "name": "명저읽기와 토론",
    "code": "CLTR0210",
    "year": 0,
    "years": [
      1,
      2
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0211",
    "name": "수학 I",
    "code": "CLTR0211",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "advanced",
      "ai",
      "core-natural",
      "research"
    ]
  },
  {
    "id": "course-CLTR0212",
    "name": "수학 II",
    "code": "CLTR0212",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양 / 전공기반",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0213",
    "name": "물리학 I",
    "code": "CLTR0213",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0214",
    "name": "물리학 II",
    "code": "CLTR0214",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양 / 전공기반",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0215",
    "name": "화학 I",
    "code": "CLTR0215",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0216",
    "name": "화학 II",
    "code": "CLTR0216",
    "year": 0,
    "years": [
      1,
      2
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양 / 전공기반",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0221",
    "name": "통계학",
    "code": "CLTR0221",
    "year": 0,
    "years": [
      1,
      4
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0224",
    "name": "물리학실험 II",
    "code": "CLTR0224",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 1.0,
    "creditOptions": [
      1.0
    ],
    "semester": "2026년 2학기",
    "category": "교양 / 전공기반",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0226",
    "name": "화학실험 I",
    "code": "CLTR0226",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 1.0,
    "creditOptions": [
      1.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0227",
    "name": "화학실험 II",
    "code": "CLTR0227",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 1.0,
    "creditOptions": [
      1.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0233",
    "name": "생물학실험 I",
    "code": "CLTR0233",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 1.0,
    "creditOptions": [
      1.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0234",
    "name": "생물학실험 II",
    "code": "CLTR0234",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 1.0,
    "creditOptions": [
      1.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0242",
    "name": "인문사회수학",
    "code": "CLTR0242",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0246",
    "name": "일반생명과학Ⅰ",
    "code": "CLTR0246",
    "year": 0,
    "years": [
      1,
      2
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양 / 전공기반",
    "sourceIds": [
      "computing",
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0247",
    "name": "일반생명과학Ⅱ",
    "code": "CLTR0247",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0248",
    "name": "한국사상과 윤리",
    "code": "CLTR0248",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0251",
    "name": "한국문학의 이해",
    "code": "CLTR0251",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0253",
    "name": "대중음악을 통한 미국문화와 영어표현법",
    "code": "CLTR0253",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0267",
    "name": "웹 프로그래밍 기초",
    "code": "CLTR0267",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0268",
    "name": "파이선 프로그래밍",
    "code": "CLTR0268",
    "year": 0,
    "years": [
      1,
      2
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0271",
    "name": "독서로 세상보기",
    "code": "CLTR0271",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0301",
    "name": "Korean Language I",
    "code": "CLTR0301",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0302",
    "name": "Korean Language II",
    "code": "CLTR0302",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0313",
    "name": "Modern Korean Society",
    "code": "CLTR0313",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0327",
    "name": "Korean Language III",
    "code": "CLTR0327",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0342",
    "name": "Korean Language Ⅳ",
    "code": "CLTR0342",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0343",
    "name": "Korean Language Ⅴ",
    "code": "CLTR0343",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0344",
    "name": "Korean Language Ⅵ",
    "code": "CLTR0344",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0348",
    "name": "Cultural Life in Korea",
    "code": "CLTR0348",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0351",
    "name": "Academic Writing & Study Skills",
    "code": "CLTR0351",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0352",
    "name": "Business Communication & Writing Skills",
    "code": "CLTR0352",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0353",
    "name": "Practical Korean Writing",
    "code": "CLTR0353",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0359",
    "name": "Korea in Motion: Korean Film and the Korean Wave",
    "code": "CLTR0359",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0366",
    "name": "Academic Korean Speaking",
    "code": "CLTR0366",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0367",
    "name": "Academic Korean Reading",
    "code": "CLTR0367",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0372",
    "name": "인공지능의 이해",
    "code": "CLTR0372",
    "year": 0,
    "years": [
      1,
      2
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양 / 기본소양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0373",
    "name": "빅데이터 기초 실습",
    "code": "CLTR0373",
    "year": 0,
    "years": [
      1,
      2
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0374",
    "name": "생활 안전을 위한 공간적 사고",
    "code": "CLTR0374",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0401",
    "name": "체력 컨디셔닝",
    "code": "CLTR0401",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 2.0,
    "creditOptions": [
      2.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0404",
    "name": "20세기 중국의 이해",
    "code": "CLTR0404",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0411",
    "name": "실용영어1",
    "code": "CLTR0411",
    "year": 0,
    "years": [
      2
    ],
    "allGrades": true,
    "credits": 2.0,
    "creditOptions": [
      2.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0412",
    "name": "실용영어2",
    "code": "CLTR0412",
    "year": 0,
    "years": [
      1,
      3
    ],
    "allGrades": true,
    "credits": 2.0,
    "creditOptions": [
      2.0
    ],
    "semester": "2026년 2학기",
    "category": "교양 / 기본소양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0413",
    "name": "비즈니스영어",
    "code": "CLTR0413",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 2.0,
    "creditOptions": [
      2.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0455",
    "name": "외국인을 위한 한국어 문법",
    "code": "CLTR0455",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0458",
    "name": "러시아 문화 읽기",
    "code": "CLTR0458",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0467",
    "name": "전통문화체험",
    "code": "CLTR0467",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0469",
    "name": "대구지리기행",
    "code": "CLTR0469",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0473",
    "name": "인도를 읽는 열두개의 시선",
    "code": "CLTR0473",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0492",
    "name": "르네상스 문학과 미술",
    "code": "CLTR0492",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0499",
    "name": "Discussions in English",
    "code": "CLTR0499",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 2.0,
    "creditOptions": [
      2.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0501",
    "name": "한국의 언어와 문학",
    "code": "CLTR0501",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0504",
    "name": "동화의 세계",
    "code": "CLTR0504",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0508",
    "name": "인간과 언어",
    "code": "CLTR0508",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0511",
    "name": "내면의 수사학",
    "code": "CLTR0511",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0515",
    "name": "과학기술과 윤리",
    "code": "CLTR0515",
    "year": 0,
    "years": [
      1,
      2,
      4
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0518",
    "name": "아름다움이란 무엇인가",
    "code": "CLTR0518",
    "year": 0,
    "years": [
      2
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0520",
    "name": "문화로 읽는 대중가요의 흐름",
    "code": "CLTR0520",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0521",
    "name": "기독교와 인류문명",
    "code": "CLTR0521",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0523",
    "name": "영상으로보는중국문화",
    "code": "CLTR0523",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0524",
    "name": "러시아, 러시아인",
    "code": "CLTR0524",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0531",
    "name": "현대지리학의 이해",
    "code": "CLTR0531",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0533",
    "name": "인간의 삶과 사회복지",
    "code": "CLTR0533",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0535",
    "name": "패션과 사회",
    "code": "CLTR0535",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0538",
    "name": "시사생명과학",
    "code": "CLTR0538",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0539",
    "name": "생물다양성",
    "code": "CLTR0539",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0542",
    "name": "축산식품과 건강",
    "code": "CLTR0542",
    "year": 2,
    "years": [
      2
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0546",
    "name": "우주의 이해",
    "code": "CLTR0546",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0553",
    "name": "비즈니스 독일어",
    "code": "CLTR0553",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0555",
    "name": "비즈니스 일본어",
    "code": "CLTR0555",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0570",
    "name": "문학과 영화, 그리고 나",
    "code": "CLTR0570",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0591",
    "name": "국제시사해설",
    "code": "CLTR0591",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0601",
    "name": "인문과 예술로 만나는 삶과 인성",
    "code": "CLTR0601",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0611",
    "name": "예비부모교육",
    "code": "CLTR0611",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0612",
    "name": "인간관계 성공 레슨",
    "code": "CLTR0612",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0614",
    "name": "독도의 자연알기",
    "code": "CLTR0614",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0617",
    "name": "성의진화",
    "code": "CLTR0617",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0618",
    "name": "이미지 메이킹 & 패션 코디네이션",
    "code": "CLTR0618",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0620",
    "name": "통일과 남북한 관계의 이해",
    "code": "CLTR0620",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0625",
    "name": "식생활과 사회 Issue",
    "code": "CLTR0625",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0639",
    "name": "디자인과 현대문화",
    "code": "CLTR0639",
    "year": 0,
    "years": [
      2
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0646",
    "name": "한국어로 보는 한국문화",
    "code": "CLTR0646",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0652",
    "name": "생활테니스",
    "code": "CLTR0652",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 1.0,
    "creditOptions": [
      1.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0654",
    "name": "댄스스포츠",
    "code": "CLTR0654",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 1.0,
    "creditOptions": [
      1.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0657",
    "name": "생활배드민턴",
    "code": "CLTR0657",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 1.0,
    "creditOptions": [
      1.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0658",
    "name": "생활수영",
    "code": "CLTR0658",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 1.0,
    "creditOptions": [
      1.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0659",
    "name": "생활스키",
    "code": "CLTR0659",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 1.0,
    "creditOptions": [
      1.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0665",
    "name": "한국의 선비문화와 고전",
    "code": "CLTR0665",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0667",
    "name": "세계문화의 이해",
    "code": "CLTR0667",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0668",
    "name": "인물따라 떠나는 한국사 기행",
    "code": "CLTR0668",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0672",
    "name": "영화로 철학하기",
    "code": "CLTR0672",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0674",
    "name": "문화 속의 상상력과 창의력",
    "code": "CLTR0674",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0678",
    "name": "영상으로 보는 일본문학",
    "code": "CLTR0678",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0679",
    "name": "데이터로 이해하는 일본인,일본어",
    "code": "CLTR0679",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0680",
    "name": "영화로 만나는 러시아와 동유럽 문화",
    "code": "CLTR0680",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0685",
    "name": "세계화시대의 여가에 대한 이해",
    "code": "CLTR0685",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0687",
    "name": "유비쿼터스 정보와 미래사회",
    "code": "CLTR0687",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0694",
    "name": "형태구성 및 조형심리",
    "code": "CLTR0694",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0703",
    "name": "행복한 삶과 가족",
    "code": "CLTR0703",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0709",
    "name": "웰빙, 웰에이징 그리고 웰다잉",
    "code": "CLTR0709",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0710",
    "name": "정보학의 이해",
    "code": "CLTR0710",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0730",
    "name": "국제개발협력의 이해",
    "code": "CLTR0730",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0742",
    "name": "옛이야기의 전통과 아름다움",
    "code": "CLTR0742",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0750",
    "name": "미래사회와 교육",
    "code": "CLTR0750",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0754",
    "name": "정보사회와 지식재산",
    "code": "CLTR0754",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0755",
    "name": "식품위생의 이해",
    "code": "CLTR0755",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0769",
    "name": "글로벌· 다문화 인재 리더십",
    "code": "CLTR0769",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0781",
    "name": "4차 산업혁명과 에너지 정책",
    "code": "CLTR0781",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0785",
    "name": "감염 미생물의 세계",
    "code": "CLTR0785",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0794",
    "name": "오픈소스 소프트웨어 기초",
    "code": "CLTR0794",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0797",
    "name": "한중 문화 콘텐츠 개발과 교류",
    "code": "CLTR0797",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0798",
    "name": "식품의 예술",
    "code": "CLTR0798",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0800",
    "name": "일상 속의 물리",
    "code": "CLTR0800",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0801",
    "name": "컴퓨터제작",
    "code": "CLTR0801",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0807",
    "name": "신소재의 미래활용: 플라스틱",
    "code": "CLTR0807",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0808",
    "name": "상대성이론과 양자역학 입문",
    "code": "CLTR0808",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0809",
    "name": "반려동물의 해부생리학적 이해",
    "code": "CLTR0809",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0811",
    "name": "인문사회 코딩기초",
    "code": "CLTR0811",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0812",
    "name": "자연과학 코딩기초",
    "code": "CLTR0812",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0813",
    "name": "빅데이터와 R프로그래밍",
    "code": "CLTR0813",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0814",
    "name": "인문사회 기초수학",
    "code": "CLTR0814",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0815",
    "name": "인문사회 기초통계",
    "code": "CLTR0815",
    "year": 0,
    "years": [
      1,
      2
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0816",
    "name": "인문사회 기초생명과학",
    "code": "CLTR0816",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0818",
    "name": "인문사회 기초지구과학",
    "code": "CLTR0818",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0819",
    "name": "기초수학2",
    "code": "CLTR0819",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0820",
    "name": "기초수학1",
    "code": "CLTR0820",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0821",
    "name": "물리학입문",
    "code": "CLTR0821",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0823",
    "name": "생명과학입문",
    "code": "CLTR0823",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0827",
    "name": "인공지능의 책임성과 윤리",
    "code": "CLTR0827",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0837",
    "name": "환경교육특강",
    "code": "CLTR0837",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0838",
    "name": "해양생태학으로의 산책",
    "code": "CLTR0838",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0840",
    "name": "사회학적 상상력과 현대사회",
    "code": "CLTR0840",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-humanities"
    ]
  },
  {
    "id": "course-CLTR0841",
    "name": "인류사와 인류세",
    "code": "CLTR0841",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0849",
    "name": "날씨와 생활",
    "code": "CLTR0849",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0850",
    "name": "인공지능 활용",
    "code": "CLTR0850",
    "year": 0,
    "years": [
      1
    ],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "foundation"
    ]
  },
  {
    "id": "course-CLTR0852",
    "name": "고전 속 사랑앓이",
    "code": "CLTR0852",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0854",
    "name": "인공지능을 위한 선형대수",
    "code": "CLTR0854",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0855",
    "name": "한국사 속의 가족과 여성",
    "code": "CLTR0855",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0856",
    "name": "지속가능한 의생활 문화",
    "code": "CLTR0856",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0859",
    "name": "글로벌 이슈와 정의로운 국제관계: 전쟁, 난민, 빈곤, 기후 위기",
    "code": "CLTR0859",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0862",
    "name": "인간과 지구시스템과학 2",
    "code": "CLTR0862",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "core-natural"
    ]
  },
  {
    "id": "course-CLTR0864",
    "name": "AI·디지털 이야기 창작과 공유 및 활용",
    "code": "CLTR0864",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0867",
    "name": "열린 대구, 글로벌 공생",
    "code": "CLTR0867",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0868",
    "name": "한국문화와 대구지역 이해",
    "code": "CLTR0868",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0869",
    "name": "Academic Korean Listening",
    "code": "CLTR0869",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0878",
    "name": "하늘을 재고 땅을 나누다: 조선의 과학, 일상을 바꾸다",
    "code": "CLTR0878",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0879",
    "name": "글로벌 문화컨텐츠",
    "code": "CLTR0879",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0881",
    "name": "Snap to Cut: AI 영상제작",
    "code": "CLTR0881",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0884",
    "name": "항공우주와 드론의 이해",
    "code": "CLTR0884",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0885",
    "name": "미래사회와 나의 삶에 대한 디자인",
    "code": "CLTR0885",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-CLTR0886",
    "name": "국제사회와 법",
    "code": "CLTR0886",
    "year": 0,
    "years": [],
    "allGrades": true,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교양",
    "sourceIds": [
      "literacy"
    ]
  },
  {
    "id": "course-COMP0225",
    "name": "디지털설계및실험",
    "code": "COMP0225",
    "year": 2,
    "years": [
      2
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "공학전공",
    "sourceIds": [
      "computing"
    ]
  },
  {
    "id": "course-COMP0322",
    "name": "데이타베이스",
    "code": "COMP0322",
    "year": 3,
    "years": [
      3
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "공학전공 / 전공",
    "sourceIds": [
      "ai",
      "computing",
      "global"
    ]
  },
  {
    "id": "course-COMP0333",
    "name": "데이터분석을 위한 파이썬프로그래밍",
    "code": "COMP0333",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "전공",
    "sourceIds": [
      "advanced"
    ]
  },
  {
    "id": "course-COMP0334",
    "name": "프로그래밍연습2",
    "code": "COMP0334",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 1.0,
    "creditOptions": [
      1.0
    ],
    "semester": "2026년 2학기",
    "category": "전공",
    "sourceIds": [
      "advanced"
    ]
  },
  {
    "id": "course-COMP0335",
    "name": "자료구조실습",
    "code": "COMP0335",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "전공",
    "sourceIds": [
      "advanced"
    ]
  },
  {
    "id": "course-COMP0423",
    "name": "프로그래밍언어론",
    "code": "COMP0423",
    "year": 0,
    "years": [
      3,
      4
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "공학전공 / 전공",
    "sourceIds": [
      "computing",
      "global"
    ]
  },
  {
    "id": "course-COMP0428",
    "name": "IT기술경영개론",
    "code": "COMP0428",
    "year": 4,
    "years": [
      4
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "기본소양 / 전공",
    "sourceIds": [
      "computing",
      "global",
      "platform"
    ]
  },
  {
    "id": "course-COMP0432",
    "name": "소프트웨어 특강",
    "code": "COMP0432",
    "year": 2,
    "years": [
      2
    ],
    "allGrades": false,
    "credits": 2.0,
    "creditOptions": [
      2.0
    ],
    "semester": "2026년 2학기",
    "category": "공학전공",
    "sourceIds": [
      "computing"
    ]
  },
  {
    "id": "course-COMP0458",
    "name": "모바일네트워크",
    "code": "COMP0458",
    "year": 4,
    "years": [
      4
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "공학전공",
    "sourceIds": [
      "computing",
      "platform"
    ]
  },
  {
    "id": "course-COMP0460",
    "name": "문제해결기반 공학연수실습(컴퓨터학)",
    "code": "COMP0460",
    "year": 3,
    "years": [
      3
    ],
    "allGrades": false,
    "credits": 2.0,
    "creditOptions": [
      2.0
    ],
    "semester": "2026년 2학기",
    "category": "전공",
    "sourceIds": [
      "global"
    ]
  },
  {
    "id": "course-COMP0461",
    "name": "문제해결기반 공학연수실습(심화컴퓨터학)",
    "code": "COMP0461",
    "year": 4,
    "years": [
      4
    ],
    "allGrades": false,
    "credits": 2.0,
    "creditOptions": [
      2.0
    ],
    "semester": "2026년 2학기",
    "category": "공학전공",
    "sourceIds": [
      "platform"
    ]
  },
  {
    "id": "course-EECS0312",
    "name": "네트워크프로그래밍",
    "code": "EECS0312",
    "year": 3,
    "years": [
      3
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "공학전공",
    "sourceIds": [
      "computing"
    ]
  },
  {
    "id": "course-ELEC0247",
    "name": "논리회로",
    "code": "ELEC0247",
    "year": 1,
    "years": [
      1
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "전공",
    "sourceIds": [
      "research"
    ]
  },
  {
    "id": "course-GLSO0212",
    "name": "소프트웨어수학",
    "code": "GLSO0212",
    "year": 2,
    "years": [
      2
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "전공",
    "sourceIds": [
      "global"
    ]
  },
  {
    "id": "course-STAT0452",
    "name": "수치해석",
    "code": "STAT0452",
    "year": 3,
    "years": [
      3
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "전공기반",
    "sourceIds": [
      "computing"
    ]
  },
  {
    "id": "course-TCHR0593",
    "name": "컴퓨터교육론",
    "code": "TCHR0593",
    "year": 3,
    "years": [
      3
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교직",
    "sourceIds": [
      "computing"
    ]
  },
  {
    "id": "course-TCHR0594",
    "name": "컴퓨터교재연구및지도법",
    "code": "TCHR0594",
    "year": 3,
    "years": [
      3
    ],
    "allGrades": false,
    "credits": 3.0,
    "creditOptions": [
      3.0
    ],
    "semester": "2026년 2학기",
    "category": "교직",
    "sourceIds": [
      "computing"
    ]
  }
];
