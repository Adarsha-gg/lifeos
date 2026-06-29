import { GraphPreview } from "lifeos-ds";

export function PersonalMap() {
  return (
    <div style={{ maxWidth: 460 }}>
      <GraphPreview nodeCount={42} masteredCount={11} />
    </div>
  );
}

export function CustomNodes() {
  return (
    <div style={{ maxWidth: 460 }}>
      <GraphPreview
        nodeCount={18}
        masteredCount={6}
        nodes={[
          { x: 16, y: 26, state: "mastered", label: "Logic" },
          { x: 40, y: 16, state: "mastered" },
          { x: 64, y: 30, state: "ready", label: "Proof" },
          { x: 28, y: 58, state: "ready" },
          { x: 54, y: 66, state: "locked" },
          { x: 82, y: 54, state: "locked", label: "Gödel" },
        ]}
      />
    </div>
  );
}
