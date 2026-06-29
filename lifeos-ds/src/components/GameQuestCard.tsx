import { Button } from "./Button";
import { Pill } from "./Pill";
import "./GameQuestCard.css";

export interface GameQuestCardProps {
  /** Game title (e.g. "Orbit", "Dawn of Civilization"). */
  title: string;
  /** What the player practices / learns. */
  description: string;
  /** Skill/domain this game trains. */
  skill?: string;
  /** Emoji/glyph for the game's CSS-art tile. */
  glyph?: string;
  /** Best score / completion, shown as a small stat. */
  bestScore?: string;
  /** XP reward. */
  xpReward?: number;
  /** Whether the quest is locked (prerequisites unmet). */
  locked?: boolean;
  /** Play handler. */
  onPlay?: () => void;
  className?: string;
}

/**
 * A playable game presented as a training quest — never a hidden link. Warm
 * CSS-art tile, skill tag, score stat, and a play CTA. Answers "Where do I
 * play/practice?".
 */
export function GameQuestCard({
  title,
  description,
  skill,
  glyph = "🎲",
  bestScore,
  xpReward,
  locked = false,
  onPlay,
  className,
}: GameQuestCardProps) {
  return (
    <article
      className={["lo-game", locked ? "lo-game--locked" : "", className || ""]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="lo-game__tile" aria-hidden>
        <span className="lo-game__glyph">{locked ? "🔒" : glyph}</span>
      </div>
      <div className="lo-game__body">
        <div className="lo-game__chips">
          <Pill tone="green" variant="soft" icon="🎯">Training quest</Pill>
          {skill && <Pill tone="neutral" variant="outline">{skill}</Pill>}
        </div>
        <h3 className="lo-game__title lo-display">{title}</h3>
        <p className="lo-game__desc lo-serif">{description}</p>
        <div className="lo-game__foot">
          <Button
            variant={locked ? "ghost" : "primary"}
            size="sm"
            disabled={locked}
            onClick={onPlay}
            icon={locked ? "🔒" : "▶"}
          >
            {locked ? "Locked" : "Play quest"}
          </Button>
          <div className="lo-game__stats">
            {bestScore && <span className="lo-game__stat">Best · <b>{bestScore}</b></span>}
            {typeof xpReward === "number" && (
              <span className="lo-game__stat lo-game__stat--xp">+{xpReward} XP</span>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}
