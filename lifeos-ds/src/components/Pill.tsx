import type { ReactNode } from "react";
import "./Pill.css";

export interface PillProps {
  children: ReactNode;
  /** Color intent. Maps to the brand/semantic token washes. */
  tone?: "neutral" | "accent" | "gold" | "green" | "blue" | "rose";
  /** `solid` fills the pill; `soft` uses a tinted wash; `outline` is bordered. */
  variant?: "soft" | "solid" | "outline";
  /** Optional leading glyph/emoji (e.g. a streak flame or lock). */
  icon?: ReactNode;
  className?: string;
}

/**
 * Small editorial label/badge — domain tags, status chips, rank labels.
 * Uppercase UI lettering on a warm wash.
 */
export function Pill({
  children,
  tone = "neutral",
  variant = "soft",
  icon,
  className,
}: PillProps) {
  return (
    <span
      className={["lo-pill", `lo-pill--${tone}`, `lo-pill--${variant}`, className || ""]
        .filter(Boolean)
        .join(" ")}
    >
      {icon && <span className="lo-pill__icon">{icon}</span>}
      {children}
    </span>
  );
}
