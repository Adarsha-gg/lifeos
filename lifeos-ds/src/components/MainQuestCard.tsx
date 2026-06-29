import { Button } from "./Button";
import { Pill } from "./Pill";
import "./MainQuestCard.css";

export type QuestKind = "review" | "lesson" | "game" | "curriculum";

export interface MainQuestCardProps {
  /** What kind of activity the single best next action is. */
  kind: QuestKind;
  /** Quest title — the thing to do next. */
  title: string;
  /** One-line plain-language reason this is the recommended next step. */
  reason: string;
  /** Domain/track label (e.g. "Systems Thinking"). */
  domain?: string;
  /** XP awarded on completion. */
  xpReward?: number;
  /** Estimated minutes. */
  minutes?: number;
  /** Call-to-action label. Defaults per kind. */
  ctaLabel?: string;
  /** Click handler for the primary CTA. */
  onStart?: () => void;
  className?: string;
}

const KIND: Record<QuestKind, { tag: string; icon: string; cta: string; tone: "accent" | "blue" | "gold" | "green" }> = {
  review: { tag: "Due Review", icon: "📜", cta: "Review now", tone: "blue" },
  lesson: { tag: "Ready Lesson", icon: "📖", cta: "Begin reading", tone: "accent" },
  game: { tag: "Training Quest", icon: "🎲", cta: "Play quest", tone: "green" },
  curriculum: { tag: "Deep Track", icon: "🗺️", cta: "Continue track", tone: "gold" },
};

/**
 * The hero of the Quest Hub: the single best next action. Gold gilt quest card
 * with a clear reason and one obvious button. Answers "What should I do first?".
 */
export function MainQuestCard({
  kind,
  title,
  reason,
  domain,
  xpReward,
  minutes,
  ctaLabel,
  onStart,
  className,
}: MainQuestCardProps) {
  const k = KIND[kind];
  return (
    <section className={["lo-mainquest", className || ""].filter(Boolean).join(" ")}>
      <div className="lo-mainquest__gilt" aria-hidden />
      <div className="lo-mainquest__head">
        <Pill tone={k.tone} variant="solid" icon={k.icon}>
          {k.tag}
        </Pill>
        <span className="lo-mainquest__kicker lo-kicker">Your main quest</span>
      </div>
      {domain && <div className="lo-mainquest__domain">{domain}</div>}
      <h2 className="lo-mainquest__title lo-display">{title}</h2>
      <p className="lo-mainquest__reason lo-serif">{reason}</p>
      <div className="lo-mainquest__foot">
        <Button variant="quest" size="lg" onClick={onStart} icon={k.icon}>
          {ctaLabel || k.cta}
        </Button>
        <div className="lo-mainquest__rewards">
          {typeof xpReward === "number" && (
            <span className="lo-mainquest__reward">
              <b>+{xpReward}</b> XP
            </span>
          )}
          {typeof minutes === "number" && (
            <span className="lo-mainquest__reward">~{minutes} min</span>
          )}
        </div>
      </div>
    </section>
  );
}
