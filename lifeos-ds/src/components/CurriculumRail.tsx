import { Pill } from "./Pill";
import "./CurriculumRail.css";

export interface CurriculumTrack {
  /** Track title (e.g. "Paul Graham — Founder Essays"). */
  title: string;
  /** Short description of the track. */
  description?: string;
  /** Number of lessons/chapters completed. */
  done: number;
  /** Total lessons/chapters. */
  total: number;
  /** Track kind — drives the spine color + tag. */
  kind?: "curriculum" | "source" | "private";
  /** Emoji/glyph for the book spine. */
  glyph?: string;
}

export interface CurriculumRailProps {
  /** Section heading. */
  title?: string;
  /** Horizontal rail of deep tracks / source companions. */
  tracks: CurriculumTrack[];
  /** Click handler — receives the track index. */
  onOpen?: (index: number) => void;
  className?: string;
}

const KIND: Record<NonNullable<CurriculumTrack["kind"]>, { tag: string; tone: "gold" | "accent" | "blue" }> = {
  curriculum: { tag: "Curriculum", tone: "gold" },
  source: { tag: "Source companion", tone: "accent" },
  private: { tag: "Private · local", tone: "blue" },
};

/**
 * A horizontal shelf of deep-learning tracks and source companions, drawn as
 * book spines on a parchment shelf. Routes to curriculum and the private reader.
 */
export function CurriculumRail({
  title = "Deep tracks & source readers",
  tracks,
  onOpen,
  className,
}: CurriculumRailProps) {
  return (
    <section className={["lo-curr", className || ""].filter(Boolean).join(" ")}>
      <div className="lo-curr__head">
        <div className="lo-kicker">Where you read</div>
        <h3 className="lo-curr__title lo-display">{title}</h3>
      </div>
      <div className="lo-curr__shelf">
        {tracks.map((t, i) => {
          const k = KIND[t.kind || "curriculum"];
          const pct = Math.round((t.done / Math.max(t.total, 1)) * 100);
          return (
            <button
              key={i}
              type="button"
              className={`lo-book lo-book--${t.kind || "curriculum"}`}
              onClick={() => onOpen?.(i)}
            >
              <span className="lo-book__spine" aria-hidden>{t.glyph || "📕"}</span>
              <span className="lo-book__inner">
                <Pill tone={k.tone} variant="soft">{k.tag}</Pill>
                <span className="lo-book__title lo-display">{t.title}</span>
                {t.description && <span className="lo-book__desc lo-serif">{t.description}</span>}
                <span className="lo-book__progress">
                  <span className="lo-book__bar"><i style={{ width: `${pct}%` }} /></span>
                  <span className="lo-book__count">{t.done}/{t.total}</span>
                </span>
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
