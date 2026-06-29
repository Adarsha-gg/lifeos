import { DeckCard } from "lifeos-ds";

export function Manuscript() {
  return (
    <DeckCard
      art="scroll"
      domain="Analytical Minds"
      levelFit="Level 5 fit"
      minutes={12}
      title="Al-Khwarizmi & Algorithmic Procedure"
      description="How a 9th-century scholar in Baghdad turned vague problem-solving into a precise, repeatable method — and accidentally named the algorithm."
    />
  );
}

export function Compass() {
  return (
    <DeckCard
      art="compass"
      domain="Systems Thinking"
      levelFit="Level 6 fit"
      minutes={9}
      title="Donella Meadows & Leverage Points"
      description="Where to push on a system to change its behavior — and why the most obvious places are usually the weakest."
    />
  );
}

export function Constellation() {
  return (
    <DeckCard
      art="constellation"
      domain="Cosmology"
      levelFit="Stretch"
      minutes={15}
      title="Emmy Noether & Symmetry"
      description="The quiet theorem linking symmetry to conservation laws — one of the most beautiful ideas in physics, told from the source."
    />
  );
}
