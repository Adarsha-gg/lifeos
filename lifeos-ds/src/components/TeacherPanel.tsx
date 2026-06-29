import { Button } from "./Button";
import { Pill } from "./Pill";
import { XPBar } from "./XPBar";
import "./TeacherPanel.css";

export interface InspectedLearner {
  /** Learner display name. */
  name: string;
  /** Learner level. */
  level: number;
  /** Rank title. */
  rankTitle?: string;
  /** XP within current level. */
  xp: number;
  /** XP needed for next level. */
  xpToNext: number;
  /** Nodes mastered. */
  mastered: number;
  /** Total nodes. */
  total: number;
  /** A weak domain worth a recommended next path. */
  weakDomain?: string;
}

export interface TeacherPanelProps {
  /** The currently-inspected learner bundle, if one has been imported. */
  learner?: InspectedLearner;
  /** Import a learner bundle / sync code. */
  onImportLearner?: () => void;
  /** Recommend a next path for the inspected learner. */
  onRecommend?: () => void;
  className?: string;
}

/**
 * Mentor affordance — "If I am a teacher, how do I inspect a learner's memory?".
 * Import a learner bundle/sync code, see their rank and progress, and recommend
 * a next path. A stand-in until real classroom accounts exist.
 */
export function TeacherPanel({
  learner,
  onImportLearner,
  onRecommend,
  className,
}: TeacherPanelProps) {
  return (
    <section className={["lo-teach", className || ""].filter(Boolean).join(" ")}>
      <div className="lo-teach__head">
        <div>
          <div className="lo-kicker">Mentor desk</div>
          <h3 className="lo-teach__title lo-display">Inspect a learner</h3>
        </div>
        <Pill tone="blue" variant="solid" icon="🎓">Teacher mode</Pill>
      </div>

      {!learner ? (
        <div className="lo-teach__empty">
          <p className="lo-teach__empty-txt lo-serif">
            Import a learner's memory bundle or paste their sync code to inspect
            progress and recommend the next quest.
          </p>
          <Button variant="primary" size="md" icon="⬆" onClick={onImportLearner}>
            Import learner memory
          </Button>
        </div>
      ) : (
        <div className="lo-teach__learner">
          <div className="lo-teach__learner-top">
            <div className="lo-teach__avatar" aria-hidden>{learner.name.charAt(0)}</div>
            <div className="lo-teach__id">
              <div className="lo-teach__name lo-display">{learner.name}</div>
              <div className="lo-teach__rank lo-serif">
                Level {learner.level}
                {learner.rankTitle ? ` · ${learner.rankTitle}` : ""}
              </div>
            </div>
            <div className="lo-teach__mastery">
              <b>{learner.mastered}</b>
              <span>/ {learner.total} mastered</span>
            </div>
          </div>

          <XPBar current={learner.xp} next={learner.xpToNext} label="Progress to next level" size="sm" />

          {learner.weakDomain && (
            <div className="lo-teach__signal">
              <Pill tone="rose" variant="soft" icon="◔">Weak domain</Pill>
              <span className="lo-teach__signal-txt">
                Needs reinforcement in <b>{learner.weakDomain}</b>.
              </span>
            </div>
          )}

          <div className="lo-teach__actions">
            <Button variant="quest" size="sm" icon="🧭" onClick={onRecommend}>
              Recommend next path
            </Button>
            <Button variant="ghost" size="sm" icon="⬆" onClick={onImportLearner}>
              Import another
            </Button>
          </div>
        </div>
      )}
    </section>
  );
}
