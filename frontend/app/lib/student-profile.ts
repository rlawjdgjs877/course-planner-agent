export const computingMajors = [
  { id: "advanced", short: "심컴", name: "심화컴퓨팅전공" },
  { id: "ai", short: "인컴", name: "인공지능컴퓨팅전공" },
  { id: "research", short: "첨컴", name: "첨단컴퓨팅연구전공" },
  { id: "platform", short: "플솦", name: "플랫폼SW·데이터과학전공" },
  { id: "global", short: "글솦", name: "글로벌SW융합전공" },
];
export const affiliations = [
  { id: "primary", name: "컴퓨터학부 주전공", description: "컴학을 주전공으로 재학 중이에요." },
  { id: "double", name: "컴학 복수전공", description: "다른 학과 소속으로 컴학을 복수전공해요." },
  { id: "minor", name: "컴학 부전공", description: "다른 학과 소속으로 컴학을 부전공해요." },
  { id: "incoming", name: "방문 교환학생", description: "타 대학에서 컴학 수업을 들으러 왔어요." },
];
export const entryPaths = [
  { id: "regular", name: "신입학 · 컴학 직접 입학" },
  { id: "undeclared", name: "자율전공에서 컴학 진입" },
  { id: "transfer", name: "편입학" },
  { id: "department", name: "타 학과에서 전과" },
  { id: "other", name: "기타 · 확인 중" },
];
export const otherMajorOptions = [
  { id: "none", name: "다른 전공 이수 없음" },
  { id: "double", name: "다른 학과 복수전공" },
  { id: "minor", name: "다른 학과 부전공" },
  { id: "both", name: "다른 학과 복수·부전공" },
];
export const exchangeOptions = [
  { id: "none", name: "교환·학점교류 이력 없음" },
  { id: "outgoing", name: "해외 교환학생으로 타 대학 이수" },
  { id: "domestic", name: "국내 타 대학 학점교류" },
  { id: "both", name: "해외 교환 + 국내 학점교류" },
];
export const recognitionOptions = [
  { id: "pending", name: "학점 인정 확인 전 · 심사 중" },
  { id: "partial", name: "일부 학점 인정 완료" },
  { id: "approved", name: "학점 인정 완료" },
];
export type StudentProfile = {
  affiliation: string; majorId: string; currentGrade: string; entryPath: string; admissionYear: string; curriculumYear: string;
  homeDepartment: string; otherMajor: string; otherDepartment: string;
  exchange: string; recognition: string; hostUniversity: string; incomingOrigin: string;
};
export const emptyStudentProfile: StudentProfile = {
  affiliation: "", majorId: "", currentGrade: "", entryPath: "", admissionYear: "", curriculumYear: "", homeDepartment: "",
  otherMajor: "none", otherDepartment: "", exchange: "none", recognition: "pending", hostUniversity: "", incomingOrigin: "",
};
export function restoreStudentProfile(input: unknown): StudentProfile {
  if (!input || typeof input !== "object") return { ...emptyStudentProfile };
  const data = input as Record<string, unknown>;
  const result = { ...emptyStudentProfile };
  const choices: Partial<Record<keyof StudentProfile, string[]>> = {
    currentGrade: ["1", "2", "3", "4"], affiliation: affiliations.map(x => x.id), majorId: computingMajors.map(x => x.id), entryPath: entryPaths.map(x => x.id),
    otherMajor: otherMajorOptions.map(x => x.id), exchange: exchangeOptions.map(x => x.id), recognition: recognitionOptions.map(x => x.id), incomingOrigin: ["domestic", "overseas"],
  };
  for (const key of Object.keys(result) as (keyof StudentProfile)[]) {
    const value = data[key];
    if (typeof value !== "string") continue;
    if (choices[key] && !choices[key]!.includes(value)) continue;
    if ((key === "admissionYear" || key === "curriculumYear") && !/^(19|20)\d{2}$/.test(value)) continue;
    result[key] = value.slice(0, 100);
  }
  return result;
}
export function changeAffiliation(profile: StudentProfile, affiliation: string): StudentProfile {
  return { ...profile, affiliation, entryPath: "", homeDepartment: "", otherMajor: "none", otherDepartment: "", incomingOrigin: "", exchange: "none", recognition: "pending", hostUniversity: "" };
}
export function getStudentGuidance(profile: StudentProfile): string[] {
  const notes: string[] = [];
  if (!profile.affiliation) return ["학생 구분을 선택하면 본인에게 필요한 확인 항목을 안내합니다."];
  if (profile.affiliation === "double" || profile.affiliation === "minor") notes.push(`컴학 ${profile.affiliation === "double" ? "복수전공" : "부전공"}의 별도 이수학점·필수과목 기준은 첨부 PDF에 없습니다. 아래 주전공 졸업요건은 참고자료이며 본인 요건으로 적용하지 않습니다.`);
  if (profile.affiliation === "incoming") notes.push("방문 교환학생은 컴학 학위 졸업요건 적용 대상으로 판단하지 않습니다. 소속 대학의 학점 인정, 교환 협정, 수강 가능 과목과 수업 언어를 별도로 확인해 주세요.");
  if (profile.affiliation === "primary") {
    if (profile.entryPath === "undeclared") notes.push("자율전공에서 컴학으로 진입한 경우 적용 교육과정 연도와 진입 전 이수 과목의 전공·교양 인정 내역을 확인해 주세요. 입학 연도만으로 기준을 자동 결정하지 않습니다.");
    if (profile.entryPath === "transfer") notes.push("편입학자는 전적 대학 인정학점, 잔여 필수과목, 적용 교육과정과 별도 이수 지도를 확인해 주세요. PDF만으로 편입생의 졸업 잔여학점을 계산하지 않습니다.");
    if (profile.entryPath === "department") notes.push("전과 이전 이수 과목의 인정 구분과 적용 교육과정 연도를 확인해 주세요. 전과생 별도 기준은 이 PDF에 없습니다.");
    if (profile.otherMajor !== "none") notes.push("타 학과 복수·부전공 이수에 따른 컴학 이수요건 변경 및 학점 중복 인정 여부는 별도 확인이 필요합니다. 두 전공의 요건을 임의로 합산하거나 감면하지 않습니다.");
    if (!profile.entryPath) notes.push("입학·진입 경로를 선택해 주세요. 자율전공 진입·편입·전과는 추가 인정 내역 확인이 필요합니다.");
  }
  if (profile.affiliation !== "incoming" && profile.exchange !== "none") notes.push("타 대학 이수 과목은 학점 인정 결과와 전공·교양 분류를 확인한 뒤 반영해야 합니다. ‘인정 완료’ 선택만으로 학점을 더하거나 컴학 과목을 이수 처리하지 않습니다.");
  if (!profile.curriculumYear && profile.affiliation !== "incoming") notes.push("적용 교육과정 연도가 아직 입력되지 않았습니다. PDF의 기준 연도와 본인의 적용 연도는 다를 수 있습니다.");
  notes.push("학생 구분은 사용자 입력 정보입니다. 첨부 PDF의 전공별 안내 외에 대상별 상세 기준은 추가 자료로 확인해야 하며, 현재 졸업 충족 여부를 자동 판정하지 않습니다.");
  return notes;
}
