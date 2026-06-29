import "./XPBar.css";

export interface XPBarProps {
  /** XP accumulated within the current level. */
  current: number;
  /** XP needed to reach the next level. */
  next: number;
  /** Show the numeric "current / next XP" readout. */
  showValue?: boolean;
  /** Optional label shown above the bar (e.g. "XP to next rank"). */
  label?: string;
  /** Bar thickness. */
  size?: "sm" | "md";
  className?: string;
}

/**
 * Gold XP progress bar showing how far the learner is to the next level.
 * Clamps to 0–100% and renders a soft gilt fill.
 */
export function XPBar({
  current,
  next,
  showValue = true,
  label,
  size = "md",
  className,
}: XPBarProps) {
  const safeNext = Math.max(next, 1);
  const pct = Math.max(0, Math.min(100, Math.round((current / safeNext) * 100)));
  return (
    <div className={["lo-xp", `lo-xp--${size}`, className || ""].filter(Boolean).join(" ")}>
      {(label || showValue) && (
        <div className="lo-xp__meta">
          {label && <span className="lo-xp__label">{label}</span>}
          {showValue && (
            <span className="lo-xp__value">
              {current.toLocaleString()} / {next.toLocaleString()} XP
            </span>
          )}
        </div>
      )}
      <div className="lo-xp__track" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
        <div className="lo-xp__fill" style={{ width: `${pct}%` }}>
          <span className="lo-xp__shine" />
        </div>
      </div>
    </div>
  );
}
