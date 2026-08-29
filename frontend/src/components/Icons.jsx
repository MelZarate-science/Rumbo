const base = { fill: 'none', stroke: 'currentColor', strokeWidth: 1.6, 'aria-hidden': true };

export function IconSearch({ size = 24 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base}>
      <circle cx="10" cy="10" r="6" />
      <path d="M14.5 14.5L20 20" strokeLinecap="round" />
    </svg>
  );
}

export function IconBuilding({ size = 24 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base}>
      <rect x="5" y="4" width="14" height="17" rx="1" />
      <path d="M9 8h1M14 8h1M9 12h1M14 12h1M9 16h1M14 16h1" strokeLinecap="round" />
    </svg>
  );
}

export function IconShield({ size = 24 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base}>
      <path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3z" />
      <circle cx="12" cy="12" r="2" />
      <path d="M12 14v2" strokeLinecap="round" />
    </svg>
  );
}

export function IconBell({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base}>
      <path d="M6 10a6 6 0 1 1 12 0c0 3.5 1 5 2 6H4c1-1 2-2.5 2-6Z" />
      <path d="M10 19a2 2 0 0 0 4 0" strokeLinecap="round" />
    </svg>
  );
}

export function IconArrowLeft({ size = 15 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base} strokeWidth={1.8}>
      <path d="M15 5l-7 7 7 7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
