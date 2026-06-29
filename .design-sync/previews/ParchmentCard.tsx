import { ParchmentCard, Pill, Button } from "lifeos-ds";

export function Raised() {
  return (
    <ParchmentCard kicker="Today's focus" title="Algorithmic thinking" style={{ maxWidth: 420 }}>
      <p style={{ margin: 0, color: "var(--lo-ink-soft)", fontFamily: "var(--lo-font-serif)" }}>
        A short, source-first reading on how Al-Khwarizmi turned procedure into a
        repeatable method — the seed of every algorithm since.
      </p>
    </ParchmentCard>
  );
}

export function Inset() {
  return (
    <ParchmentCard variant="inset" kicker="Notebook" title="Key terms" style={{ maxWidth: 420 }}>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <Pill tone="neutral">Procedure</Pill>
        <Pill tone="neutral">Invariant</Pill>
        <Pill tone="neutral">Decomposition</Pill>
      </div>
    </ParchmentCard>
  );
}

export function Quest() {
  return (
    <ParchmentCard
      variant="quest"
      kicker="Main quest"
      title="Finish your daily review"
      action={<Pill tone="gold" variant="solid">+80 XP</Pill>}
      style={{ maxWidth: 420 }}
    >
      <p style={{ margin: "0 0 16px", color: "var(--lo-ink-soft)", fontFamily: "var(--lo-font-serif)" }}>
        Three cards are due. Clear them to keep your streak alive.
      </p>
      <Button variant="quest" icon="📜">Review now</Button>
    </ParchmentCard>
  );
}
