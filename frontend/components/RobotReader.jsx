"use client";

// Cartoon illustration: a friendly robot reading a book, surrounded by
// PDF documents and a stack of books. Pure inline SVG (no image assets).
export default function RobotReader() {
  return (
    <svg
      viewBox="0 0 340 280"
      role="img"
      aria-label="Cartoon robot reading books and PDF documents"
      style={{ width: "100%", height: "auto", display: "block" }}
    >
      <defs>
        <linearGradient id="rr-body" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#a78bfa" />
          <stop offset="1" stopColor="#6d28d9" />
        </linearGradient>
        <linearGradient id="rr-head" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#c4b5fd" />
          <stop offset="1" stopColor="#8b5cf6" />
        </linearGradient>
        <linearGradient id="rr-book" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#fcd34d" />
          <stop offset="1" stopColor="#f59e0b" />
        </linearGradient>
      </defs>

      {/* soft backdrop blobs */}
      <circle cx="170" cy="145" r="118" fill="#ffffff" opacity="0.10" />
      <circle cx="62" cy="60" r="26" fill="#06b6d4" opacity="0.25" />
      <circle cx="292" cy="52" r="16" fill="#fbbf24" opacity="0.5" />

      {/* book stack, bottom left */}
      <g>
        <rect x="26" y="222" width="112" height="20" rx="7" fill="#f472b6" />
        <rect x="32" y="202" width="100" height="20" rx="7" fill="#06b6d4" />
        <rect x="26" y="182" width="112" height="20" rx="7" fill="#fbbf24" />
        <rect x="40" y="189" width="60" height="4" rx="2" fill="#ffffff" opacity="0.7" />
        <rect x="44" y="209" width="52" height="4" rx="2" fill="#ffffff" opacity="0.7" />
        <rect x="40" y="229" width="60" height="4" rx="2" fill="#ffffff" opacity="0.7" />
      </g>

      {/* floating PDF card, right (back) */}
      <g transform="rotate(-9 272 150)">
        <rect x="244" y="112" width="58" height="76" rx="8" fill="#ffffff" opacity="0.95" />
        <rect x="244" y="112" width="58" height="22" rx="8" fill="#ef4444" />
        <rect x="244" y="126" width="58" height="10" fill="#ef4444" />
        <text x="273" y="127" textAnchor="middle" fontSize="11" fontWeight="800" fill="#fff" fontFamily="sans-serif">
          PDF
        </text>
        <rect x="251" y="142" width="44" height="5" rx="2.5" fill="#c7d2fe" />
        <rect x="251" y="151" width="44" height="5" rx="2.5" fill="#e0e7ff" />
        <rect x="251" y="160" width="30" height="5" rx="2.5" fill="#e0e7ff" />
      </g>

      {/* robot legs */}
      <rect x="140" y="228" width="22" height="22" rx="9" fill="#5b21b6" />
      <rect x="188" y="228" width="22" height="22" rx="9" fill="#5b21b6" />

      {/* robot body */}
      <rect x="118" y="148" width="114" height="86" rx="26" fill="url(#rr-body)" />
      <rect x="138" y="166" width="74" height="44" rx="14" fill="#ffffff" opacity="0.18" />
      <circle cx="158" cy="188" r="6" fill="#fbbf24" />
      <circle cx="177" cy="188" r="6" fill="#06b6d4" />
      <circle cx="196" cy="188" r="6" fill="#f472b6" />

      {/* robot arms */}
      <rect x="96" y="160" width="22" height="52" rx="11" fill="#7c3aed" transform="rotate(12 107 186)" />
      <rect x="232" y="160" width="22" height="52" rx="11" fill="#7c3aed" transform="rotate(-12 243 186)" />
      <circle cx="103" cy="212" r="11" fill="#c4b5fd" />
      <circle cx="247" cy="212" r="11" fill="#c4b5fd" />

      {/* open book held in front */}
      <g>
        <path d="M118 196 Q145 184 172 196 L172 232 Q145 220 118 232 Z" fill="url(#rr-book)" />
        <path d="M172 196 Q199 184 226 196 L226 232 Q199 220 172 232 Z" fill="url(#rr-book)" />
        <path d="M124 199 Q147 189 168 199 L168 229 Q147 219 124 229 Z" fill="#fff7ed" />
        <path d="M176 199 Q197 189 220 199 L220 229 Q197 219 176 229 Z" fill="#fff7ed" />
        <line x1="172" y1="196" x2="172" y2="232" stroke="#b45309" strokeWidth="3" />
        <rect x="131" y="206" width="28" height="4" rx="2" fill="#cbd5e1" />
        <rect x="131" y="213" width="28" height="4" rx="2" fill="#e2e8f0" />
        <rect x="185" y="206" width="28" height="4" rx="2" fill="#cbd5e1" />
        <rect x="185" y="213" width="28" height="4" rx="2" fill="#e2e8f0" />
      </g>

      {/* robot ears */}
      <rect x="98" y="88" width="16" height="30" rx="8" fill="#06b6d4" />
      <rect x="236" y="88" width="16" height="30" rx="8" fill="#06b6d4" />

      {/* robot head */}
      <rect x="110" y="56" width="130" height="84" rx="30" fill="url(#rr-head)" />
      <rect x="110" y="56" width="130" height="84" rx="30" fill="none" stroke="#5b21b6" strokeWidth="4" opacity="0.35" />

      {/* antenna */}
      <line x1="175" y1="56" x2="175" y2="34" stroke="#5b21b6" strokeWidth="5" strokeLinecap="round" />
      <circle cx="175" cy="28" r="9" fill="#fbbf24" stroke="#b45309" strokeWidth="3" />

      {/* eyes */}
      <circle cx="148" cy="98" r="15" fill="#ffffff" />
      <circle cx="202" cy="98" r="15" fill="#ffffff" />
      <circle cx="150" cy="100" r="7" fill="#1e1b4b" />
      <circle cx="204" cy="100" r="7" fill="#1e1b4b" />
      <circle cx="152" cy="97" r="2.5" fill="#ffffff" />
      <circle cx="206" cy="97" r="2.5" fill="#ffffff" />

      {/* cheeks + smile */}
      <circle cx="130" cy="116" r="7" fill="#f472b6" opacity="0.65" />
      <circle cx="220" cy="116" r="7" fill="#f472b6" opacity="0.65" />
      <path d="M160 118 Q175 130 190 118" fill="none" stroke="#1e1b4b" strokeWidth="4" strokeLinecap="round" />

      {/* floating PDF card, left (front) */}
      <g transform="rotate(8 66 120)">
        <rect x="38" y="84" width="54" height="70" rx="8" fill="#ffffff" />
        <path d="M78 84 h-12 a6 6 0 0 0 -6 6 v12 z" fill="#cbd5e1" />
        <rect x="38" y="84" width="54" height="20" rx="8" fill="#ef4444" />
        <rect x="38" y="96" width="54" height="10" fill="#ef4444" />
        <text x="65" y="98" textAnchor="middle" fontSize="10" fontWeight="800" fill="#fff" fontFamily="sans-serif">
          PDF
        </text>
        <rect x="45" y="111" width="40" height="5" rx="2.5" fill="#c7d2fe" />
        <rect x="45" y="120" width="40" height="5" rx="2.5" fill="#e0e7ff" />
        <rect x="45" y="129" width="26" height="5" rx="2.5" fill="#e0e7ff" />
      </g>

      {/* sparkles */}
      <g strokeLinecap="round">
        <path d="M292 200 v14 M285 207 h14" stroke="#fbbf24" strokeWidth="4" />
        <path d="M48 150 v10 M43 155 h10" stroke="#06b6d4" strokeWidth="4" />
        <circle cx="306" cy="120" r="5" fill="#f472b6" />
        <circle cx="36" cy="66" r="5" fill="#ffffff" opacity="0.8" />
      </g>
    </svg>
  );
}
