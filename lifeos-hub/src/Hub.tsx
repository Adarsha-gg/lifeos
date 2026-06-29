import { useMemo, useState } from "react";
import {
  ProfileRankHeader,
  MainQuestCard,
  QuestPath,
  DeckCard,
  DeckControls,
  GraphPreview,
  GameQuestCard,
  CurriculumRail,
  MemoryPanel,
  TeacherPanel,
  Button,
  Pill,
} from "lifeos-ds";
import {
  loadProfile,
  graphStats,
  DECK,
  QUEST_PATH,
  GAMES,
  TRACKS,
} from "./data";

const NAV = [
  { id: "character", ic: "🛡️", label: "Your character" },
  { id: "quest", ic: "📜", label: "Main quest" },
  { id: "path", ic: "🧭", label: "Quest path" },
  { id: "deck", ic: "🃏", label: "Learning deck" },
  { id: "map", ic: "🗺️", label: "World map" },
  { id: "games", ic: "🎲", label: "Practice & games" },
  { id: "library", ic: "📚", label: "Tracks & reader" },
  { id: "memory", ic: "💾", label: "Memory & profile" },
  { id: "mentor", ic: "🎓", label: "Mentor desk" },
] as const;

function go(id: string, close: () => void) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  close();
}

export function Hub() {
  const profile = useMemo(loadProfile, []);
  const stats = useMemo(graphStats, []);
  const [open, setOpen] = useState(false);
  const [card, setCard] = useState(0);

  const lesson = DECK[card % DECK.length];
  const isTeacher = profile.role === "teacher";

  return (
    <div className="lo-root hub">
      {/* top bar */}
      <header className="hub__topbar">
        <button className="hub__burger" aria-label="Open menu" onClick={() => setOpen(true)}>
          <span /><span /><span />
        </button>
        <div className="hub__wordmark">Life<b>OS</b></div>
        <div className="hub__topspacer" />
        <Pill tone="gold" variant="soft" icon="⭐">{profile.xp}/{profile.xpToNext} XP</Pill>
      </header>

      {/* drawer */}
      <div className={`hub__scrim ${open ? "open" : ""}`} onClick={() => setOpen(false)} />
      <nav className={`hub__drawer ${open ? "open" : ""}`} aria-hidden={!open}>
        <div className="hub__drawer-head">
          <span className="hub__drawer-title">Quest menu</span>
          <button className="hub__drawer-close" aria-label="Close menu" onClick={() => setOpen(false)}>×</button>
        </div>
        {NAV.filter((n) => n.id !== "mentor" || isTeacher).map((n) => (
          <button key={n.id} className="hub__navlink" onClick={() => go(n.id, () => setOpen(false))}>
            <span className="ic">{n.ic}</span>
            {n.label}
          </button>
        ))}
      </nav>

      {/* one page */}
      <main className="hub__main">
        {/* 1 — character */}
        <section id="character" className="hub__section">
          <ProfileRankHeader
            name={profile.name}
            role={profile.role}
            level={profile.level}
            rankTitle={profile.rankTitle}
            tier={profile.tier}
            xp={profile.xp}
            xpToNext={profile.xpToNext}
            streak={profile.streak}
            persistence={profile.persistence}
          />
        </section>

        {/* 2 — main quest */}
        <section id="quest" className="hub__section">
          <MainQuestCard
            kind="review"
            domain="Systems Thinking"
            title="3 cards are due for review"
            reason="Reviewing now keeps these concepts in long-term memory — and protects your streak."
            xpReward={80}
            minutes={6}
            onStart={() => go("deck", () => {})}
          />
        </section>

        {/* 3 — quest path */}
        <section id="path" className="hub__section">
          <div className="hub__section-head">
            <h2 className="hub__section-title">Your quest path</h2>
            <Pill tone="neutral" variant="soft">4 steps</Pill>
          </div>
          <QuestPath steps={QUEST_PATH} />
        </section>

        {/* 4 — learning deck */}
        <section id="deck" className="hub__section">
          <div className="hub__section-head">
            <h2 className="hub__section-title">Learning deck</h2>
            <a className="hub__section-link" href="/learn/">Open full deck →</a>
          </div>
          <div className="hub__deck-wrap">
            <div className="hub__deck-stack">
              <DeckCard
                title={lesson.title}
                description={lesson.description}
                domain={lesson.domain}
                levelFit={lesson.levelFit}
                minutes={lesson.minutes}
                art={lesson.art}
              />
            </div>
            <DeckControls
              onNo={() => setCard((c) => c + 1)}
              onRead={() => { window.location.href = lesson.href; }}
            />
            <div className="hub__hint">Card {(card % DECK.length) + 1} of {DECK.length} · only "No" and "Read", as it should be</div>
          </div>
        </section>

        {/* 5 — world map */}
        <section id="map" className="hub__section">
          <GraphPreview
            nodeCount={stats.nodeCount}
            masteredCount={stats.masteredCount}
            onOpen={() => { window.location.href = "/learn/skill-tree.html"; }}
          />
        </section>

        {/* 6 — practice & games */}
        <section id="games" className="hub__section">
          <div className="hub__section-head">
            <h2 className="hub__section-title">Practice &amp; games</h2>
            <Pill tone="green" variant="soft">Training quests</Pill>
          </div>
          <div className="hub__row hub__games">
            {GAMES.map((g) => (
              <GameQuestCard
                key={g.title}
                title={g.title}
                description={g.description}
                skill={g.skill}
                glyph={g.glyph}
                bestScore={g.bestScore}
                xpReward={g.xpReward}
                locked={g.locked}
                onPlay={() => { if (!g.locked) window.location.href = g.href; }}
              />
            ))}
          </div>
        </section>

        {/* 7 — tracks & reader */}
        <section id="library" className="hub__section">
          <CurriculumRail
            tracks={TRACKS}
            onOpen={(i) => { window.location.href = TRACKS[i].href; }}
          />
        </section>

        {/* 8 — memory & profile */}
        <section id="memory" className="hub__section">
          <MemoryPanel
            cloud={profile.persistence === "cloud-configured" ? "configured" : "not-configured"}
            syncCode="LIFEOS-7QF2-9KD1-AAC8"
            onExport={() => alert("Exports your LifeOS memory JSON (wire to /api or download).")}
            onImport={() => alert("Import a LifeOS memory JSON / paste a sync code.")}
            onCopyCode={() => navigator.clipboard?.writeText("LIFEOS-7QF2-9KD1-AAC8")}
          />
        </section>

        {/* 9 — mentor desk (teachers) */}
        <section id="mentor" className="hub__section">
          <TeacherPanel
            learner={isTeacher ? { name: "Mira", level: 7, rankTitle: "Journeyman of Systems", xp: 240, xpToNext: 600, mastered: 18, total: 42, weakDomain: "Probability" } : undefined}
            onImportLearner={() => alert("Import a learner bundle / paste their sync code.")}
            onRecommend={() => go("path", () => {})}
          />
          {!isTeacher && (
            <div className="hub__hint">
              <Button variant="ghost" size="sm" icon="🎓" onClick={() => alert("Switches this device to teacher/mentor mode.")}>
                I'm a mentor — switch to teacher mode
              </Button>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
