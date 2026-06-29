import { Pill } from "lifeos-ds";

export function Tones() {
  return (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
      <Pill tone="neutral">Systems</Pill>
      <Pill tone="accent">Ready lesson</Pill>
      <Pill tone="gold">Level 4 fit</Pill>
      <Pill tone="green">Mastered</Pill>
      <Pill tone="blue">Due review</Pill>
      <Pill tone="rose">Overdue</Pill>
    </div>
  );
}

export function Variants() {
  return (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
      <Pill tone="accent" variant="soft">Soft</Pill>
      <Pill tone="accent" variant="solid">Solid</Pill>
      <Pill tone="accent" variant="outline">Outline</Pill>
    </div>
  );
}

export function WithIcons() {
  return (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
      <Pill tone="accent" variant="solid" icon="🔥">7 day streak</Pill>
      <Pill tone="gold" variant="soft" icon="⭐">+120 XP</Pill>
      <Pill tone="neutral" variant="outline" icon="🔒">Locked</Pill>
    </div>
  );
}
