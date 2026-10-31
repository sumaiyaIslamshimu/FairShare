// Hand-drawn SVG illustrations (no image files). Palette: bright forest, mint, coral on cream.
const C = {
  forest: "#17794a", moss: "#3fae6e", sage: "#bfe8cf", mist: "#dff3e5",
  cream: "#ffffff", line: "#d5e8da", green: "#1fa463", clay: "#f08a4b", peach: "#f9d5b8", leaf: "#7fd39c",
};

export function CompareArt({ className = "" }) {
  return (
    <svg className={className} viewBox="0 0 760 330" role="img"
      aria-label="Illustration of one product compared across several stores">
      <defs>
        <linearGradient id="fsBlob" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor={C.mist} />
          <stop offset="1" stopColor={C.sage} />
        </linearGradient>
        <filter id="fsShadow" x="-20%" y="-20%" width="140%" height="160%">
          <feDropShadow dx="0" dy="8" stdDeviation="10" floodColor={C.forest} floodOpacity="0.16" />
        </filter>
      </defs>

      <ellipse cx="380" cy="172" rx="360" ry="146" fill="url(#fsBlob)" />

      {/* leaves */}
      <path d="M30 70C26 44 46 26 76 28c0 28-14 46-46 42z" fill={C.leaf} />
      <path d="M708 66c4-24-14-42-42-40-2 26 14 44 42 40z" fill={C.leaf} opacity=".8" />
      <circle cx="728" cy="170" r="5" fill={C.clay} />
      <circle cx="34" cy="190" r="4" fill={C.clay} />

      {/* store card 1 */}
      <g filter="url(#fsShadow)">
        <rect x="70" y="95" width="190" height="125" rx="16" fill={C.cream} stroke={C.line} />
      </g>
      <circle cx="98" cy="123" r="12" fill={C.sage} />
      <rect x="118" y="115" width="74" height="8" rx="4" fill={C.line} />
      <rect x="118" y="130" width="48" height="6" rx="3" fill={C.mist} />
      <rect x="92" y="156" width="84" height="14" rx="7" fill={C.sage} />
      <circle cx="98" cy="196" r="5" fill={C.moss} />
      <rect x="110" y="192" width="60" height="8" rx="4" fill={C.mist} />

      {/* store card 2: best price (raised) */}
      <g filter="url(#fsShadow)">
        <rect x="290" y="52" width="200" height="158" rx="18" fill="#fff" stroke={C.green} strokeWidth="2.5" />
      </g>
      <circle cx="322" cy="90" r="13" fill={C.moss} />
      <rect x="344" y="82" width="70" height="8" rx="4" fill={C.line} />
      <rect x="344" y="98" width="46" height="6" rx="3" fill={C.mist} />
      <rect x="314" y="120" width="98" height="26" rx="13" fill={C.mist} />
      <text x="363" y="137" textAnchor="middle" fontSize="12.5" fontWeight="700" fill={C.forest}>Best price</text>
      <rect x="314" y="160" width="116" height="18" rx="9" fill={C.forest} />
      <circle cx="322" cy="196" r="5" fill={C.moss} />
      <rect x="334" y="192" width="64" height="8" rx="4" fill={C.mist} />

      {/* store card 3 */}
      <g filter="url(#fsShadow)">
        <rect x="520" y="95" width="190" height="125" rx="16" fill={C.cream} stroke={C.line} />
      </g>
      <circle cx="548" cy="123" r="12" fill={C.sage} />
      <rect x="568" y="115" width="74" height="8" rx="4" fill={C.line} />
      <rect x="568" y="130" width="48" height="6" rx="3" fill={C.mist} />
      <rect x="542" y="156" width="100" height="14" rx="7" fill={C.peach} />
      <circle cx="548" cy="196" r="5" fill={C.clay} />
      <rect x="560" y="192" width="60" height="8" rx="4" fill={C.mist} />

      {/* magnifier */}
      <circle cx="150" cy="252" r="32" fill="#ffffff" fillOpacity=".6" stroke={C.forest} strokeWidth="6" />
      <line x1="173" y1="275" x2="200" y2="302" stroke={C.forest} strokeWidth="8" strokeLinecap="round" />
      <path d="M138 244h18l10 10-14 14-14-14z" fill={C.sage} stroke={C.forest} strokeWidth="2" strokeLinejoin="round" />
      <circle cx="150" cy="252" r="2.5" fill={C.forest} />

      {/* price-drop chip */}
      <g filter="url(#fsShadow)">
        <rect x="560" y="240" width="140" height="62" rx="14" fill={C.cream} stroke={C.line} />
      </g>
      <line x1="576" y1="288" x2="684" y2="288" stroke={C.line} strokeDasharray="4 4" />
      <polyline points="576,254 598,262 620,258 644,276 664,280 684,284" fill="none"
        stroke={C.green} strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="684" cy="284" r="5" fill={C.green} />
    </svg>
  );
}

const Disc = ({ children }) => (
  <svg viewBox="0 0 96 96" width="72" height="72" aria-hidden="true">
    <circle cx="48" cy="48" r="46" fill={C.mist} />
    {children}
  </svg>
);

export const StepSearch = () => (
  <Disc>
    <circle cx="43" cy="43" r="16" fill={C.cream} stroke={C.forest} strokeWidth="4" />
    <line x1="55" y1="55" x2="70" y2="70" stroke={C.forest} strokeWidth="6" strokeLinecap="round" />
    <path d="M62 24c-1-8 5-12 12-12 0 8-4 12-12 12z" fill={C.leaf} />
  </Disc>
);

export const StepCompare = () => (
  <Disc>
    <rect x="20" y="42" width="15" height="30" rx="4" fill={C.sage} />
    <rect x="41" y="54" width="15" height="18" rx="4" fill={C.green} />
    <rect x="62" y="36" width="15" height="36" rx="4" fill={C.sage} />
    <path d="M44 42l4 4 8-9" fill="none" stroke={C.green} strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
  </Disc>
);

export const StepTrack = () => (
  <Disc>
    <polyline points="20,34 36,40 50,36 64,54 76,60" fill="none" stroke={C.green}
      strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
    <circle cx="76" cy="60" r="5" fill={C.green} />
    <path d="M30 70h36" stroke={C.line} strokeWidth="3" strokeLinecap="round" />
    <path d="M62 22a8 8 0 0 1 8 8c0 6 2 7 2 9H52c0-2 2-3 2-9a8 8 0 0 1 8-8z" fill={C.clay} />
  </Disc>
);