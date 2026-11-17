import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Campus Finder | 나의 학업 워크스페이스",
  description: "이수 과목을 정리하고 나만의 예시 시간표를 만들어 보세요.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="ko"><body>{children}</body></html>;
}
