import { TeacherPanel } from "lifeos-ds";

export function EmptyState() {
  return (
    <div style={{ maxWidth: 480 }}>
      <TeacherPanel />
    </div>
  );
}

export function InspectingLearner() {
  return (
    <div style={{ maxWidth: 480 }}>
      <TeacherPanel
        learner={{
          name: "Mira",
          level: 7,
          rankTitle: "Journeyman of Systems",
          xp: 240,
          xpToNext: 600,
          mastered: 18,
          total: 42,
          weakDomain: "Probability",
        }}
      />
    </div>
  );
}
