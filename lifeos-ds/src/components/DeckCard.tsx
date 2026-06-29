import type { ReactNode } from "react";
import { Pill } from "./Pill";
import "./DeckCard.css";

export interface DeckCardProps {
  /** Lesson title. */
  title: string;
  /** Short, rich editorial description (the card blurb). */
  description: string;
  /** Domain/track label. */
  domain?: string;
  /** Difficulty/level fit label (e.g. "Level 4 fit"). */
  levelFit?: string;
  /** Estimated read minutes. */
  minutes?: number;
  /**
   * CSS-art scene for the card top. Pass one of the built-in art keys for
   * generated storybook art, or pass a custom node (e.g. an <img>).
   */
  art?: "scroll" | "compass" | "constellation" | "atom" | ReactNode;
  /** Stacking depth hint for the deck illusion (0 = front card). */
  depth?: 0 | 1 | 2;
  className?: string;
}

const ART_KEYS = new Set(["scroll", "compass", "constellation", "atom"]);

/**
 * A single Tinder-style learning card: storybook CSS-art header, serif title and
 * rich blurb, domain + level-fit chips. Pairs with DeckControls (No / Read).
 */
export function DeckCard({
  title,
  description,
  domain,
  levelFit,
  minutes,
  art = "scroll",
  depth = 0,
  className,
}: DeckCardProps) {
  const isArtKey = typeof art === "string" && ART_KEYS.has(art);
  return (
    <article
      className={["lo-deck", `lo-deck--depth-${depth}`, className || ""]
        .filter(Boolean)
        .join(" ")}
    >
      <div className={isArtKey ? `lo-deck__art lo-deck__art--${art}` : "lo-deck__art"}>
        {!isArtKey && art}
        {isArtKey && <span className="lo-deck__art-glow" aria-hidden />}
      </div>
      <div className="lo-deck__body">
        <div className="lo-deck__chips">
          {domain && <Pill tone="accent" variant="soft">{domain}</Pill>}
          {levelFit && <Pill tone="gold" variant="outline">{levelFit}</Pill>}
        </div>
        <h3 className="lo-deck__title lo-display">{title}</h3>
        <p className="lo-deck__desc lo-serif">{description}</p>
        {typeof minutes === "number" && (
          <div className="lo-deck__meta">📖 ~{minutes} min read</div>
        )}
      </div>
    </article>
  );
}
