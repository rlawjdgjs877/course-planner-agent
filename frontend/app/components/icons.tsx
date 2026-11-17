export function Icon({ name, size = 20 }: { name: string; size?: number }) {
  const paths: Record<string, React.ReactNode> = {
    check: <path d="m5 12 4 4L19 6" />,
    grid: <><rect x="4" y="4" width="6" height="6" rx="1" /><rect x="14" y="4" width="6" height="6" rx="1" /><rect x="4" y="14" width="6" height="6" rx="1" /><rect x="14" y="14" width="6" height="6" rx="1" /></>,
    list: <path d="M9 6h12M9 12h12M9 18h12M3 6h1M3 12h1M3 18h1" />,
    search: <><circle cx="10.5" cy="10.5" r="6.5" /><path d="m16 16 4 4" /></>,
    calendar: <><rect x="3" y="5" width="18" height="16" rx="3" /><path d="M7 3v4m10-4v4M3 11h18M8 15h2m4 0h2" /></>,
    sliders: <><path d="M4 7h16M4 17h16" /><circle cx="9" cy="7" r="3" /><circle cx="15" cy="17" r="3" /></>,
    book: <><path d="M12 5v15M12 5C8 2 3 4 3 4v15s5-2 9 1c4-3 9-1 9-1V4s-5-2-9 1Z" /></>,
    arrow: <path d="m9 5 7 7-7 7" />,
    info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v6m0-10v1" /></>,
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name] || paths.book}</svg>;
}
export function Folder() {
  return <svg className="folder" viewBox="0 0 104 82" fill="none" aria-hidden="true"><path d="M5 14a6 6 0 0 1 6-6h28l10 9h44a6 6 0 0 1 6 6v48H5Z" fill="#47a8e8" /><path d="M5 30a6 6 0 0 1 6-6h82a6 6 0 0 1 6 6v40a6 6 0 0 1-6 6H11a6 6 0 0 1-6-6Z" fill="url(#folderFill)" /><path d="M11 25h82" stroke="#b7eaff" strokeWidth="2" /><defs><linearGradient id="folderFill" x1="52" y1="24" x2="52" y2="76" gradientUnits="userSpaceOnUse"><stop stopColor="#80d5fa" /><stop offset="1" stopColor="#47afea" /></linearGradient></defs></svg>;
}
