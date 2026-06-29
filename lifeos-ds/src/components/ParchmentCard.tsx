import type { ReactNode } from "react";
import "./ParchmentCard.css";

export interface ParchmentCardProps {
  /** Card heading, rendered in the editorial display serif. */
  title?: ReactNode;
  /** Small uppercase label shown above the title. */
  kicker?: ReactNode;
  /** Visual emphasis. `raised` is the default paper card; `inset` is recessed;
   *  `quest` adds a gold gilt edge for hero/quest surfaces. */
  variant?: "raised" | "inset" | "quest";
  /** Optional element rendered in the top-right (badge, action, icon). */
  action?: ReactNode;
  /** Removes inner padding for media-edge layouts. */
  flush?: boolean;
  children?: ReactNode;
  className?: string;
}

/**
 * The base warm-parchment surface every other LifeOS panel is built from.
 * Soft paper texture, hand-bound border, optional gilt edge for quest cards.
 */
export function ParchmentCard({
  title,
  kicker,
  variant = "raised",
  action,
  flush = false,
  children,
  className,
}: ParchmentCardProps) {
  return (
    <section
      className={[
        "lo-card",
        `lo-card--${variant}`,
        flush ? "lo-card--flush" : "",
        className || "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {(title || kicker || action) && (
        <header className="lo-card__head">
          <div>
            {kicker && <div className="lo-kicker">{kicker}</div>}
            {title && <h3 className="lo-card__title lo-display">{title}</h3>}
          </div>
          {action && <div className="lo-card__action">{action}</div>}
        </header>
      )}
      {children}
    </section>
  );
}
