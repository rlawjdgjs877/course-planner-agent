// 선후수 흐름 원본은 data/prerequisites.json 하나다. 백엔드(backend/app/data/prerequisites.json)도 같은 내용을 쓴다.
import chains from "./data/prerequisites.json";

export type PrerequisiteChain = { category: string; stages: string[]; page: number };
export const prerequisiteChains: PrerequisiteChain[] = chains;
export const startupCourses = ["기업가정신과벤처창업", "창업과경영", "회계와사회생활", "나의첫사업제안서", "알기쉬운창업마케팅과스피치", "스타트업설계", "IT지식재산권", "SW창업프로젝트"];
