import { RankBadge } from "./RankBadge";
import { XPBar } from "./XPBar";
import { Pill } from "./Pill";
import "./ProfileRankHeader.css";

export type PersistenceState =
  | "local-only"
  | "export-available"
  | "cloud-configured"
  | "teacher-mode";

export interface ProfileRankHeaderProps {
  /** Learner display name, if known. */
  name?: string;
  /** Learner or teacher role. */
  role?: "learner" | "teacher";
  /** Current level. */
  level: number;
  /** Rank title (e.g. "Apprentice Cartographer"). */
  rankTitle: string;
  /** Crest tier color. */
  tier?: "bronze" | "silver" | "gold";
  /** XP within the current level. */
  xp: number;
  /** XP required for the next level. */
  xpToNext: number;
  /** Current day streak. Hidden when 0. */
  streak?: number;
  /** How the learner's memory is persisted — drives the status chip. */
  persistence?: PersistenceState;
  className?: string;
}

const PERSIST: Record<PersistenceState, { label: string; tone: "neutral" | "gold" | "green" | "blue" }> = {
  "local-only": { label: "Local only", tone: "neutral" },
  "export-available": { label: "Export ready", tone: "gold" },
  "cloud-configured": { label: "Cloud synced", tone: "green" },
  "teacher-mode": { label: "Teacher mode", tone: "blue" },
};

/**
 * The Quest Hub's character header: rank crest, name/role, level + rank title,
 * XP-to-next-level bar, streak, and a memory-persistence status chip.
 * Answers "Who am I as a learner?" at a glance.
 */
export function ProfileRankHeader({
  name,
  role = "learner",
  level,
  rankTitle,
  tier = "gold",
  xp,
  xpToNext,
  streak = 0,
  persistence = "local-only",
  className,
}: ProfileRankHeaderProps) {
  const p = PERSIST[persistence];
  return (
    <header className={["lo-prh", className || ""].filter(Boolean).join(" ")}>
      <RankBadge level={level} tier={tier} size="lg" />
      <div className="lo-prh__body">
        <div className="lo-prh__topline">
          {name ? (
            <h2 className="lo-prh__name lo-display">{name}</h2>
          ) : (
            <h2 className="lo-prh__name lo-display">Wandering Scholar</h2>
          )}
          <Pill tone={role === "teacher" ? "blue" : "accent"} variant="soft">
            {role}
          </Pill>
        </div>
        <div className="lo-prh__rank lo-serif">{rankTitle}</div>
        <XPBar current={xp} next={xpToNext} label="XP to next rank" size="md" />
        <div className="lo-prh__chips">
          {streak > 0 && (
            <Pill tone="accent" variant="solid" icon="🔥">
              {streak} day streak
            </Pill>
          )}
          <Pill tone={p.tone} variant="soft">
            {p.label}
          </Pill>
        </div>
      </div>
    </header>
  );
}
