import { Pill } from "./Pill";
import "./QuestPath.css";

export type StepState = "done" | "current" | "ready" | "locked";

export interface QuestStepItem {
  /** Step heading. */
  title: string;
  /** One-line description / reason. */
  detail?: string;
  /** Lane label: review, ready next, stretch, explore. */
  lane?: string;
  /** Progress state of this step. */
  state?: StepState;
  /** XP reward for the step. */
  xp?: number;
}

export interface QuestPathProps {
  /** Ordered steps: review/current → ready next → stretch/unlock → explore. */
  steps: QuestStepItem[];
  className?: string;
}

const STATE_META: Record<StepState, { icon: string; tone: "green" | "gold" | "accent" | "neutral"; label: string }> = {
  done: { icon: "✓", tone: "green", label: "Done" },
  current: { icon: "◆", tone: "accent", label: "In progress" },
  ready: { icon: "▸", tone: "gold", label: "Ready" },
  locked: { icon: "🔒", tone: "neutral", label: "Locked" },
};

/**
 * The Quest Path — a vertical storybook stepper laying out the learner's route:
 * review/current → ready next → stretch/unlock → explore. Answers
 * "What comes next?" as an ordered journey, not a pile of links.
 */
export function QuestPath({ steps, className }: QuestPathProps) {
  return (
    <ol className={["lo-qpath", className || ""].filter(Boolean).join(" ")}>
      {steps.map((s, i) => {
        const st = s.state || "ready";
        const m = STATE_META[st];
        return (
          <li key={i} className={`lo-qstep lo-qstep--${st}`}>
            <div className="lo-qstep__rail" aria-hidden>
              <span className="lo-qstep__node">{m.icon}</span>
              {i < steps.length - 1 && <span className="lo-qstep__line" />}
            </div>
            <div className="lo-qstep__body">
              <div className="lo-qstep__top">
                {s.lane && <span className="lo-qstep__lane lo-kicker">{s.lane}</span>}
                <Pill tone={m.tone} variant="soft">
                  {m.label}
                </Pill>
              </div>
              <div className="lo-qstep__title lo-display">{s.title}</div>
              {s.detail && <div className="lo-qstep__detail lo-serif">{s.detail}</div>}
              {typeof s.xp === "number" && (
                <div className="lo-qstep__xp">+{s.xp} XP</div>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
