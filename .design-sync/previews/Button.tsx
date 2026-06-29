import { Button } from "lifeos-ds";

export function Variants() {
  return (
    <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
      <Button variant="primary" icon="📖">Begin reading</Button>
      <Button variant="quest" icon="🗡️">Start quest</Button>
      <Button variant="ghost" icon="🗺️">Open map</Button>
      <Button variant="link">Skip for now</Button>
    </div>
  );
}

export function Sizes() {
  return (
    <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
      <Button size="sm">Small</Button>
      <Button size="md">Medium</Button>
      <Button size="lg">Large</Button>
    </div>
  );
}

export function States() {
  return (
    <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
      <Button variant="primary">Enabled</Button>
      <Button variant="primary" disabled>Disabled</Button>
      <Button variant="quest" block icon="✦">Full-width quest</Button>
    </div>
  );
}
