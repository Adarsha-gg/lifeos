import { GameQuestCard } from "lifeos-ds";

export function Playable() {
  return (
    <div style={{ maxWidth: 480 }}>
      <GameQuestCard
        title="Orbit"
        glyph="🪐"
        skill="Systems & feedback"
        description="Balance gravity and thrust to hold a stable orbit — a hands-on feel for feedback loops."
        bestScore="Lvl 4"
        xpReward={60}
      />
    </div>
  );
}

export function Locked() {
  return (
    <div style={{ maxWidth: 480 }}>
      <GameQuestCard
        title="Dawn of Civilization"
        glyph="🏛️"
        skill="Resource strategy"
        description="Guide a settlement through scarcity and growth. Unlocks once you reach level 8."
        locked
        xpReward={120}
      />
    </div>
  );
}
