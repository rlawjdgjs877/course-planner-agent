export type CourseOffering = {
  crseNo: string; sbjetCd: string; sbjetNm: string; sbjetDvnno: string;
  estblYear: string; estblSmstrSctnm: string; estblGrade: string;
  estblUnivNm: string; estblDprtnNm: string; sbjetSctnm: string;
  crdit: string; thryTime: string; prctsTime: string; totalPrfssNm: string;
  lssnsTimeInfo: string; lssnsRealTimeInfo: string; lctrmInfo: string; rmnmCd: string;
  rmrk: string; appcrCnt: number; attlcPrscpCnt: number; pckgeRqstCnt: number;
};
// User-provided excerpt: only the fully present record is included.
// No fetch timestamp or live availability was supplied.
export const platformOfferings: CourseOffering[] = [{
  crseNo: "ITEC0418-001", sbjetCd: "ITEC0418", sbjetNm: "대규모병렬컴퓨팅", sbjetDvnno: "001",
  estblYear: "2026", estblSmstrSctnm: "2학기", estblGrade: "4",
  estblUnivNm: "IT대학", estblDprtnNm: "컴퓨터학부 플랫폼소프트웨어전공", sbjetSctnm: "공학전공",
  crdit: "3", thryTime: "3", prctsTime: "0", totalPrfssNm: "백낙훈",
  lssnsTimeInfo: "토 1A,1B,2A,토 2B,3A,3B", lssnsRealTimeInfo: "토 09:00 ~ 10:30,토 10:30 ~ 12:00",
  lctrmInfo: "산격동 캠퍼스 IT대학5호관(IT융복합관)", rmnmCd: "B102", rmrk: "원격강좌",
  appcrCnt: 109, attlcPrscpCnt: 110, pckgeRqstCnt: 145,
}];
export function getCourseOffering(name: string) {
  return platformOfferings.find(offering => offering.sbjetNm === name);
}
