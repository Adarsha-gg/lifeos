import { MainQuestCard } from "lifeos-ds";

export function DueReview() {
  return (
    <div style={{ maxWidth: 480 }}>
      <MainQuestCard
        kind="review"
        domain="Systems Thinking"
        title="3 cards are due for review"
        reason="Reviewing now keeps these concepts in long-term memory — and protects your 7-day streak."
        xpReward={80}
        minutes={6}
      />
    </div>
  );
}

export function ReadyLesson() {
  return (
    <div style={{ maxWidth: 480 }}>
      <MainQuestCard
        kind="lesson"
        domain="Analytical Minds"
        title="Al-Khwarizmi and Algorithmic Procedure"
        reason="It builds directly on the logic foundations you mastered last week — a level-5 fit."
        xpReward={120}
        minutes={12}
      />
    </div>
  );
}

export function TrainingGame() {
  return (
    <div style={{ maxWidth: 480 }}>
      <MainQuestCard
        kind="game"
        domain="Probability"
        title="Play: The Monty Hall Trial"
        reason="A short playable drill to cement the counter-intuitive result you just read about."
        xpReward={60}
        minutes={4}
      />
    </div>
  );
}
