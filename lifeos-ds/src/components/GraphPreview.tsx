import { Pill } from "./Pill";
import { Button } from "./Button";
import "./GraphPreview.css";

export interface GraphPreviewNode {
  /** 0–100 horizontal position within the preview canvas. */
  x: number;
  /** 0–100 vertical position. */
  y: number;
  /** Node readiness — drives the dot color. */
  state?: "mastered" | "ready" | "locked";
  /** Short label shown on the largest nodes. */
  label?: string;
}

export interface GraphPreviewProps {
  /** Total nodes in the learner's personal graph. */
  nodeCount: number;
  /** Nodes the learner has mastered. */
  masteredCount: number;
  /** A handful of nodes to plot in the mini-map (keep it light — ~6–10). */
  nodes?: GraphPreviewNode[];
  /** Click handler for "Open world map". */
  onOpen?: () => void;
  className?: string;
}

const DEFAULT_NODES: GraphPreviewNode[] = [
  { x: 18, y: 30, state: "mastered", label: "Logic" },
  { x: 44, y: 18, state: "mastered" },
  { x: 70, y: 32, state: "ready", label: "Systems" },
  { x: 30, y: 62, state: "ready" },
  { x: 58, y: 70, state: "locked" },
  { x: 84, y: 60, state: "locked" },
];

const EDGES: [number, number][] = [
  [0, 1],
  [1, 2],
  [0, 3],
  [3, 4],
  [2, 5],
  [4, 5],
];

const COLOR: Record<NonNullable<GraphPreviewNode["state"]>, string> = {
  mastered: "var(--lo-green)",
  ready: "var(--lo-gold)",
  locked: "var(--lo-muted)",
};

/**
 * A light personal-graph mini-map — "Where is my world map?". Plots a handful of
 * nodes/edges as a constellation summary with a link to the full graph. Stays
 * cheap on purpose so it never competes with the real graph's render budget.
 */
export function GraphPreview({
  nodeCount,
  masteredCount,
  nodes = DEFAULT_NODES,
  onOpen,
  className,
}: GraphPreviewProps) {
  return (
    <section className={["lo-graph", className || ""].filter(Boolean).join(" ")}>
      <div className="lo-graph__head">
        <div>
          <div className="lo-kicker">Your world map</div>
          <h3 className="lo-graph__title lo-display">Knowledge constellation</h3>
        </div>
        <Pill tone="green" variant="soft">
          {masteredCount}/{nodeCount} mastered
        </Pill>
      </div>

      <div className="lo-graph__canvas">
        <svg viewBox="0 0 100 80" preserveAspectRatio="none" className="lo-graph__svg">
          {EDGES.map(([a, b], i) =>
            nodes[a] && nodes[b] ? (
              <line
                key={i}
                x1={nodes[a].x}
                y1={nodes[a].y}
                x2={nodes[b].x}
                y2={nodes[b].y}
                className="lo-graph__edge"
              />
            ) : null
          )}
          {nodes.map((n, i) => (
            <circle
              key={i}
              cx={n.x}
              cy={n.y}
              r={n.label ? 3.4 : 2.2}
              fill={COLOR[n.state || "ready"]}
              className="lo-graph__node"
            />
          ))}
        </svg>
        {nodes
          .filter((n) => n.label)
          .map((n, i) => (
            <span
              key={i}
              className="lo-graph__nodelabel"
              style={{ left: `${n.x}%`, top: `${n.y}%` }}
            >
              {n.label}
            </span>
          ))}
      </div>

      <div className="lo-graph__foot">
        <div className="lo-graph__legend">
          <span><i style={{ background: COLOR.mastered }} />Mastered</span>
          <span><i style={{ background: COLOR.ready }} />Ready</span>
          <span><i style={{ background: COLOR.locked }} />Locked</span>
        </div>
        <Button variant="ghost" size="sm" onClick={onOpen} icon="🗺️">
          Open world map
        </Button>
      </div>
    </section>
  );
}
