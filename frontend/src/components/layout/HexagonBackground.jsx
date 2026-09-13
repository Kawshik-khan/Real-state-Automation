import React, { useRef, useEffect } from 'react';

/**
 * GeometricBackground — Triangle tessellation pattern at subtle opacity
 * with Gaussian blur. Near the mouse cursor, the pattern LINES themselves
 * glow emerald green (via an SVG mask + green-stroked duplicate layer).
 */
export default function HexagonBackground() {
  const svgRef = useRef(null);
  const gradRef = useRef(null);

  useEffect(() => {
    const handler = (e) => {
      if (!gradRef.current || !svgRef.current) return;
      // Convert viewport coords to SVG user-space coords
      const svg = svgRef.current;
      const rect = svg.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      // Update the radial gradient center (in px)
      gradRef.current.setAttribute('cx', x);
      gradRef.current.setAttribute('cy', y);
    };
    window.addEventListener('mousemove', handler, { passive: true });
    return () => window.removeEventListener('mousemove', handler);
  }, []);

  /* ── Shared pattern path data ── */
  const patternPaths = (
    <>
      {/* Row 1: Large upward triangles */}
      <path d="M0 52 L30 0 L60 52 Z"   fill="none" />
      <path d="M60 52 L90 0 L120 52 Z"  fill="none" />
      {/* Row 1: Downward triangles (interlocking) */}
      <path d="M30 0 L60 52 L0 52 Z"    fill="none" />
      <path d="M90 0 L120 52 L60 52 Z"   fill="none" />
      {/* Row 2: Shifted triangles */}
      <path d="M0 52 L30 104 L-30 104 Z" fill="none" />
      <path d="M0 52 L60 52 L30 104 Z"   fill="none" />
      <path d="M60 52 L90 104 L30 104 Z"  fill="none" />
      <path d="M60 52 L120 52 L90 104 Z"  fill="none" />
      <path d="M120 52 L150 104 L90 104 Z" fill="none" />
      {/* Inner sub-divisions */}
      <path d="M15 26 L45 26"            fill="none" />
      <path d="M75 26 L105 26"           fill="none" />
      <path d="M30 52 L30 78"            fill="none" />
      <path d="M90 52 L90 78"            fill="none" />
      {/* Diagonal cross-connectors */}
      <path d="M0 0 L30 0"               fill="none" />
      <path d="M60 0 L90 0"              fill="none" />
      <path d="M15 26 L0 52"             fill="none" />
      <path d="M45 26 L60 52"            fill="none" />
      <path d="M75 26 L60 52"            fill="none" />
      <path d="M105 26 L120 52"          fill="none" />
    </>
  );

  return (
    <div className="geo-background" aria-hidden="true">
      <svg
        ref={svgRef}
        className="geo-svg"
        xmlns="http://www.w3.org/2000/svg"
        width="100%"
        height="100%"
        preserveAspectRatio="none"
      >
        <defs>
          {/* Gaussian blur for the base pattern */}
          <filter id="geoBlur">
            <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" />
          </filter>

          {/* ── Base pattern: subtle gray lines ── */}
          <pattern
            id="triPatternBase"
            width="120"
            height="104"
            patternUnits="userSpaceOnUse"
          >
            <g className="geo-line">
              {patternPaths}
            </g>
          </pattern>

          {/* ── Glow pattern: green glowing lines ── */}
          <pattern
            id="triPatternGlow"
            width="120"
            height="104"
            patternUnits="userSpaceOnUse"
          >
            <g className="geo-line-glow">
              {patternPaths}
            </g>
          </pattern>

          {/* ── Radial mask that follows the cursor ── */}
          <radialGradient
            id="cursorGrad"
            ref={gradRef}
            cx="-300"
            cy="-300"
            r="220"
            gradientUnits="userSpaceOnUse"
          >
            <stop offset="0%" stopColor="white" stopOpacity="1" />
            <stop offset="60%" stopColor="white" stopOpacity="0.4" />
            <stop offset="100%" stopColor="white" stopOpacity="0" />
          </radialGradient>

          <mask id="cursorMask">
            <rect width="100%" height="100%" fill="url(#cursorGrad)" />
          </mask>
        </defs>

        {/* Layer 1: Base gray pattern (always visible, blurred) */}
        <rect
          width="100%"
          height="100%"
          fill="url(#triPatternBase)"
          filter="url(#geoBlur)"
        />

        {/* Layer 2: Green glow pattern (only visible near cursor via mask) */}
        <rect
          width="100%"
          height="100%"
          fill="url(#triPatternGlow)"
          mask="url(#cursorMask)"
        />
      </svg>
    </div>
  );
}
