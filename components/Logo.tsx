export default function Logo({ className = "" }: { className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <svg viewBox="0 0 32 32" aria-hidden="true" className="h-8 w-8 shrink-0">
        <rect width="32" height="32" rx="9" fill="#0A6E8C" />
        {/* Desert sun setting over pool water */}
        <path d="M9.5 17a6.5 6.5 0 0 1 13 0Z" fill="#E0893B" />
        <path
          d="M6 22.5c2.5 0 2.5-2 5-2s2.5 2 5 2 2.5-2 5-2 2.5 2 5 2"
          stroke="#FBF9F5"
          strokeWidth="2.2"
          strokeLinecap="round"
          fill="none"
        />
      </svg>
      <span className="font-display text-xl font-extrabold tracking-tight text-ink">
        DesertDesk
      </span>
    </span>
  );
}
