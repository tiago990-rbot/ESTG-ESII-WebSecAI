export default function EyeMark({ className = "", decorative = true }: { className?: string; decorative?: boolean }) {
  return <svg className={"eyeMark " + className} viewBox="0 0 64 48" fill="none" aria-hidden={decorative ? true : undefined} role={decorative ? undefined : "img"} aria-label={decorative ? undefined : "Olho WebSecAI"}>
    <path d="M3 24C11 11 21 5 32 5s21 6 29 19C53 37 43 43 32 43S11 37 3 24Z" stroke="currentColor" strokeWidth="2" />
    <circle cx="32" cy="24" r="13" stroke="currentColor" strokeWidth="1.5" strokeDasharray="34 7" />
    <circle cx="32" cy="24" r="6" fill="currentColor" /><circle cx="34" cy="21" r="2" fill="var(--bg)" />
    <path d="M32 0v7m0 34v7M0 24h8m48 0h8" stroke="currentColor" strokeWidth="1.5" />
  </svg>;
}
