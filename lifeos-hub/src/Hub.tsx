import { useEffect, useMemo, useState } from "react";
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
import type { GraphPreviewNode } from "lifeos-ds";
import {
  loadProfile,
  graphStats,
  DECK,
  QUEST_PATH,
  GAMES,
  TRACKS,
  LEVEL_SYSTEM,
  LS_KEYS,
  type DeckLesson,
  type QuestStep,
} from "./data";

const NAV = [
  { id: "character", ic: "🛡️", label: "Your character" },
  { id: "progress", ic: "⭐", label: "Level progression" },
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

type MiniGraph = { nodeCount: number; masteredCount: number; nodes: GraphPreviewNode[]; edges: [number, number][] };
type GraphNode = { id: string; title?: string; domain?: string; kind?: string; url?: string; summary?: string; difficulty?: string; xp?: number; x?: number; y?: number };
type GraphEdge = { from: string; to: string };

function readDone() {
  try {
    const progress = JSON.parse(localStorage.getItem(LS_KEYS.progress) || "{}");
    return progress && typeof progress.done === "object" ? progress.done as Record<string, any> : {};
  } catch {
    return {};
  }
}

function readMap(key: string) {
  try {
    const parsed = JSON.parse(localStorage.getItem(key) || "{}");
    return parsed && typeof parsed === "object" ? parsed as Record<string, any> : {};
  } catch {
    return {};
  }
}

function writeDeckChoice(key: string, id: string) {
  const current = readMap(key);
  current[id] = { at: new Date().toISOString() };
  localStorage.setItem(key, JSON.stringify(current));
}

function hash(s: string) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function shortLabel(title = "Node") {
  const words = title.split(/\s+/).filter(Boolean);
  return words.slice(0, 3).join(" ");
}

function miniPosition(nodes: GraphNode[]) {
  const xs = nodes.map((n) => Number(n.x)).filter(Number.isFinite);
  const ys = nodes.map((n) => Number(n.y)).filter(Number.isFinite);
  const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
  const hasSpread = xs.length === nodes.length && ys.length === nodes.length && maxX - minX > 4 && maxY - minY > 4;
  return nodes.map((n, i) => {
    if (hasSpread) {
      return {
        x: 8 + ((Number(n.x) - minX) / Math.max(1, maxX - minX)) * 84,
        y: 8 + ((Number(n.y) - minY) / Math.max(1, maxY - minY)) * 64,
      };
    }
    const a = -Math.PI / 2 + (i / Math.max(1, nodes.length)) * Math.PI * 2;
    return { x: 50 + Math.cos(a) * 35, y: 40 + Math.sin(a) * 26 };
  });
}

function usePersonalMiniGraph(fallback: MiniGraph): MiniGraph {
  const [mini, setMini] = useState<MiniGraph>(fallback);
  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const done = readDone();
        const doneIds = new Set(Object.keys(done));
        let response = await fetch("/learn/knowledge-graph.json", { cache: "no-store" });
        if (!response.ok) response = await fetch("/output/learn/knowledge-graph.json", { cache: "no-store" });
        if (!response.ok) throw new Error("knowledge graph unavailable");
        const graph = await response.json() as { nodes: GraphNode[]; edges: GraphEdge[]; domains?: { id: string; color: string }[] };
        const byId = new Map(graph.nodes.map((n) => [n.id, n]));
        const domainColor = new Map((graph.domains || []).map((d) => [d.id, d.color]));
        const learned = Object.entries(done)
          .sort((a, b) => Date.parse(String((b[1] as any)?.at || 0)) - Date.parse(String((a[1] as any)?.at || 0)))
          .map(([id]) => id)
          .filter((id) => byId.has(id));
        const picked: string[] = [];
        for (const id of learned) if (picked.length < 8) picked.push(id);
        for (const e of graph.edges || []) {
          if (picked.length >= 18) break;
          if (doneIds.has(e.from) && byId.has(e.to) && !picked.includes(e.to)) picked.push(e.to);
          if (picked.length >= 18) break;
          if (doneIds.has(e.to) && byId.has(e.from) && !picked.includes(e.from)) picked.push(e.from);
        }
        const selected = picked.map((id) => byId.get(id)!).filter(Boolean);
        const pos = miniPosition(selected);
        const index = new Map(picked.map((id, i) => [id, i]));
        const edges = (graph.edges || [])
          .filter((e) => index.has(e.from) && index.has(e.to))
          .slice(0, 28)
          .map((e) => [index.get(e.from)!, index.get(e.to)!] as [number, number]);
        const nodes = selected.map((n, i) => ({
          x: pos[i].x,
          y: pos[i].y,
          state: doneIds.has(n.id) ? "mastered" as const : "ready" as const,
          color: domainColor.get(n.domain || "") || undefined,
          label: doneIds.has(n.id) && i < 3 ? shortLabel(n.title) : undefined,
        }));
        if (!cancelled) setMini({ nodeCount: graph.nodes.length || fallback.nodeCount, masteredCount: learned.length, nodes, edges });
      } catch {
        if (!cancelled) setMini(fallback);
      }
    }
    load();
    window.addEventListener("storage", load);
    return () => { cancelled = true; window.removeEventListener("storage", load); };
  }, [fallback.nodeCount, fallback.masteredCount]);
  return mini;
}

function domainTitle(id?: string, domains?: { id: string; name?: string }[]) {
  const name = domains?.find((d) => d.id === id)?.name;
  if (name) return name;
  return (id || "Learning").replace(/-/g, " ").replace(/\b\w/g, (m) => m.toUpperCase());
}

function artForDomain(domain?: string): DeckLesson["art"] {
  if (domain === "physics" || domain === "math") return "atom";
  if (domain === "history" || domain === "statecraft" || domain === "culture") return "compass";
  if (domain === "systems" || domain === "growth" || domain === "startup") return "scroll";
  return "constellation";
}

function levelFitFor(node: GraphNode) {
  if (node.difficulty === "stretch") return "Level 4 stretch";
  if (node.difficulty === "advanced") return "Level 3 fit";
  return "Level 2 fit";
}

function toDeckLesson(node: GraphNode, domains?: { id: string; name?: string }[]): DeckLesson {
  return {
    id: node.id,
    title: node.title || shortLabel(node.id),
    description: node.summary || `Continue this source-first lesson from your graph frontier.`,
    domain: domainTitle(node.domain, domains),
    levelFit: levelFitFor(node),
    minutes: Math.max(8, Math.round((Number(node.xp) || 90) / 6)),
    art: artForDomain(node.domain),
    href: node.url || "/learn/",
  };
}

function useHubDeck(fallback: DeckLesson[]) {
  const [lessons, setLessons] = useState<DeckLesson[]>(fallback);
  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        let response = await fetch("/learn/knowledge-graph.json", { cache: "no-store" });
        if (!response.ok) response = await fetch("/output/learn/knowledge-graph.json", { cache: "no-store" });
        if (!response.ok) throw new Error("knowledge graph unavailable");
        const graph = await response.json() as { nodes: GraphNode[]; edges: GraphEdge[]; domains?: { id: string; name?: string }[] };
        const doneIds = new Set(Object.keys(readDone()));
        const skipped = readMap(LS_KEYS.skipped);
        const adjacent = new Set<string>();
        for (const edge of graph.edges || []) {
          if (doneIds.has(edge.from)) adjacent.add(edge.to);
          if (doneIds.has(edge.to)) adjacent.add(edge.from);
        }
        const day = new Date().toISOString().slice(0, 10);
        const ranked = (graph.nodes || [])
          .filter((node) => node.url && node.kind !== "game" && !doneIds.has(node.id) && !skipped[node.id])
          .map((node) => {
            let score = 0;
            if (adjacent.has(node.id)) score += 120;
            if (node.difficulty === "core") score += 45;
            if (node.difficulty === "advanced") score += 28;
            score += Math.max(0, 40 - Math.abs((Number(node.x) || 40) - 28) / 2);
            score += (hash(node.id + day) % 1000) / 1000;
            return { node, score };
          })
          .sort((a, b) => b.score - a.score)
          .slice(0, 8)
          .map(({ node }) => toDeckLesson(node, graph.domains));
        if (!cancelled && ranked.length) setLessons(ranked);
      } catch {
        if (!cancelled) setLessons(fallback);
      }
    }
    load();
    window.addEventListener("storage", load);
    return () => { cancelled = true; window.removeEventListener("storage", load); };
  }, [fallback]);
  return lessons;
}

function questPathFor(lesson: DeckLesson): QuestStep[] {
  const nextXp = Math.max(60, lesson.minutes * 6);
  return [
    QUEST_PATH[0],
    { lane: "Ready next", title: lesson.title, detail: `${lesson.levelFit} · ${lesson.minutes} min · from your graph frontier.`, state: "ready", xp: nextXp, href: lesson.href },
    QUEST_PATH[2],
    QUEST_PATH[3],
  ];
}

export function Hub() {
  const profile = useMemo(loadProfile, []);
  const stats = useMemo(graphStats, []);
  const miniGraph = usePersonalMiniGraph({ nodeCount: stats.nodeCount, masteredCount: stats.masteredCount, nodes: [], edges: [] });
  const [open, setOpen] = useState(false);
  const [card, setCard] = useState(0);
  const deck = useHubDeck(DECK);

  const lesson = deck[card % Math.max(1, deck.length)] || DECK[0];
  const questPath = useMemo(() => questPathFor(lesson), [lesson]);
  const isTeacher = profile.role === "teacher";

  function skipLesson() {
    writeDeckChoice(LS_KEYS.skipped, lesson.id);
    setCard((c) => c + 1);
  }

  function readLesson() {
    writeDeckChoice(LS_KEYS.yes, lesson.id);
    window.location.href = lesson.href;
  }

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

        {/* 2 — level progression */}
        <section id="progress" className="hub__section">
          <div className="hub__section-head">
            <h2 className="hub__section-title">Level progression</h2>
            <Pill tone="gold" variant="soft">Level {profile.level}/4</Pill>
          </div>
          <div className="hub__level-ladder" aria-label="LifeOS level progression">
            {LEVEL_SYSTEM.map((step) => {
              const state = step.level < profile.level ? "done" : step.level === profile.level ? "current" : "locked";
              return (
                <div key={step.level} className={`hub__level-step ${state}`}>
                  <span className="hub__level-badge">L{step.level}</span>
                  <div>
                    <b>{step.title}</b>
                    <small>{step.threshold.toLocaleString()} XP · {step.unlock}</small>
                  </div>
                </div>
              );
            })}
          </div>
          <div className="hub__progress-note">
            You are in <b>{profile.rankTitle}</b>. Finish main quests and reviews to fill this level, then unlock the next band.
          </div>
        </section>

        {/* 3 — main quest */}
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

        {/* 4 — quest path */}
        <section id="path" className="hub__section">
          <div className="hub__section-head">
            <h2 className="hub__section-title">Your quest path</h2>
            <Pill tone="neutral" variant="soft">4 steps</Pill>
          </div>
          <QuestPath steps={questPath} />
        </section>

        {/* 5 — learning deck */}
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
              onNo={skipLesson}
              onRead={readLesson}
            />
            <div className="hub__hint">Card {(card % Math.max(1, deck.length)) + 1} of {deck.length} · graph-ranked · only "No" and "Read"</div>
          </div>
        </section>

        {/* 6 — personal world map */}
        <section id="map" className="hub__section">
          <GraphPreview
            nodeCount={miniGraph.nodeCount}
            masteredCount={miniGraph.masteredCount}
            nodes={miniGraph.nodes}
            edges={miniGraph.edges}
            onOpen={() => { window.location.href = "/learn/skill-tree.html"; }}
          />
        </section>

        {/* 7 — practice & games */}
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

        {/* 8 — tracks & reader */}
        <section id="library" className="hub__section">
          <CurriculumRail
            tracks={TRACKS}
            onOpen={(i) => { window.location.href = TRACKS[i].href; }}
          />
        </section>

        {/* 9 — memory & profile */}
        <section id="memory" className="hub__section">
          <MemoryPanel
            cloud={profile.persistence === "cloud-configured" ? "configured" : "not-configured"}
            syncCode="LIFEOS-7QF2-9KD1-AAC8"
            onExport={() => alert("Exports your LifeOS memory JSON (wire to /api or download).")}
            onImport={() => alert("Import a LifeOS memory JSON / paste a sync code.")}
            onCopyCode={() => navigator.clipboard?.writeText("LIFEOS-7QF2-9KD1-AAC8")}
          />
        </section>

        {/* 10 — mentor desk (teachers) */}
        <section id="mentor" className="hub__section">
          <TeacherPanel
            learner={isTeacher ? { name: "Mira", level: 3, rankTitle: "Level 3 · Pathfinder", xp: 240, xpToNext: 720, mastered: 18, total: 42, weakDomain: "Probability" } : undefined}
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
