import { CurriculumRail } from "lifeos-ds";

export function Shelf() {
  return (
    <div style={{ maxWidth: 560 }}>
      <CurriculumRail
        tracks={[
          {
            title: "Founder Essays — Paul Graham",
            description: "Do Things That Don't Scale, and other source companions.",
            kind: "source",
            glyph: "✍️",
            done: 3,
            total: 9,
          },
          {
            title: "Mastery: Probability",
            description: "From counting to Bayes, the mastery-style way.",
            kind: "curriculum",
            glyph: "📐",
            done: 7,
            total: 12,
          },
          {
            title: "The Timeless Way of Building",
            description: "Local-only private reading with highlights.",
            kind: "private",
            glyph: "🏛️",
            done: 1,
            total: 5,
          },
        ]}
      />
    </div>
  );
}
