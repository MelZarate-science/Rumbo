export default function CompassMark({ size = 30, needleColor = '#123a5c' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" aria-hidden="true">
      <circle cx="50" cy="50" r="46" fill="none" stroke="#f0900f" strokeWidth="7" />
      <path d="M50 14 L60 50 L50 86 L40 50 Z" fill={needleColor} />
    </svg>
  );
}
