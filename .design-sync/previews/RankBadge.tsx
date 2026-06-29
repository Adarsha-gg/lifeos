import { RankBadge } from "lifeos-ds";

export function Tiers() {
  return (
    <div style={{ display: "flex", gap: 28, flexWrap: "wrap", alignItems: "center" }}>
      <RankBadge level={2} tier="bronze" />
      <RankBadge level={7} tier="silver" />
      <RankBadge level={12} tier="gold" />
    </div>
  );
}

export function WithTitle() {
  return <RankBadge level={5} tier="gold" title="Apprentice Cartographer" size="lg" />;
}

export function Sizes() {
  return (
    <div style={{ display: "flex", gap: 24, flexWrap: "wrap", alignItems: "center" }}>
      <RankBadge level={4} size="sm" />
      <RankBadge level={4} size="md" />
      <RankBadge level={4} size="lg" />
    </div>
  );
}
