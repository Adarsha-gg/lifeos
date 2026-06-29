import "./RankBadge.css";

export interface RankBadgeProps {
  /** Current learner level, shown large in the crest. */
  level: number;
  /** Rank title beneath/around the crest (e.g. "Apprentice Cartographer"). */
  title?: string;
  /** Crest size. */
  size?: "sm" | "md" | "lg";
  /** Tier color of the crest medallion. */
  tier?: "bronze" | "silver" | "gold";
  className?: string;
}

const TIER_LABEL: Record<NonNullable<RankBadgeProps["tier"]>, string> = {
  bronze: "Bronze",
  silver: "Silver",
  gold: "Gold",
};

/**
 * Gold-leaf rank crest: a gilt medallion showing the learner's level with an
 * optional rank title. The centerpiece of the profile/rank header.
 */
export function RankBadge({
  level,
  title,
  size = "md",
  tier = "gold",
  className,
}: RankBadgeProps) {
  return (
    <div className={["lo-rank", `lo-rank--${size}`, className || ""].filter(Boolean).join(" ")}>
      <div className={`lo-rank__crest lo-rank__crest--${tier}`} aria-hidden>
        <span className="lo-rank__ray" />
        <span className="lo-rank__lvl-k">LVL</span>
        <span className="lo-rank__lvl">{level}</span>
      </div>
      {title && (
        <div className="lo-rank__meta">
          <div className="lo-rank__title lo-display">{title}</div>
          <div className="lo-rank__tier">{TIER_LABEL[tier]} tier</div>
        </div>
      )}
    </div>
  );
}
