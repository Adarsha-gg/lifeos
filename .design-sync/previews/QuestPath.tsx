import { QuestPath } from "lifeos-ds";

export function FullPath() {
  return (
    <div style={{ maxWidth: 460 }}>
      <QuestPath
        steps={[
          {
            lane: "Review",
            title: "Clear 3 due cards",
            detail: "Spaced repetition — due today.",
            state: "current",
            xp: 80,
          },
          {
            lane: "Ready next",
            title: "Al-Khwarizmi & Algorithmic Procedure",
            detail: "Level-5 fit, builds on logic foundations.",
            state: "ready",
            xp: 120,
          },
          {
            lane: "Stretch",
            title: "Gödel & the Limits of Proof",
            detail: "Unlocks after two more logic lessons.",
            state: "locked",
            xp: 200,
          },
          {
            lane: "Explore",
            title: "Play: Dawn of Civilization",
            detail: "A training quest for systems leverage.",
            state: "ready",
            xp: 60,
          },
        ]}
      />
    </div>
  );
}

export function WithProgress() {
  return (
    <div style={{ maxWidth: 460 }}>
      <QuestPath
        steps={[
          { lane: "Done", title: "Foundations of Logic", state: "done", xp: 100 },
          { lane: "Done", title: "Truth Tables", state: "done", xp: 90 },
          { lane: "Current", title: "Formal Proof", detail: "You're halfway through.", state: "current", xp: 140 },
          { lane: "Next", title: "Predicate Logic", state: "ready", xp: 160 },
        ]}
      />
    </div>
  );
}
