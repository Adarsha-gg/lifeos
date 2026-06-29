// Quest Hub data layer. Reads the existing LifeOS localStorage schema where
// present (so the hub reflects real progress), and falls back to sensible
// seeded content so the page is never empty. No backend required — static-safe.

export const LS_KEYS = {
  progress: "lifeos.learning.progress.v1",
  level: "lifeos.level.lastSeen.v1",
  profile: "lifeos.profile.v1",
  skipped: "lifeos.deck.skipped.v2",
  yes: "lifeos.deck.yes.v2",
} as const;

function readJSON<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

const RANKS = [
  "Wandering Novice",
  "Apprentice Cartographer",
  "Journeyman of Systems",
  "Adept of the Archive",
  "Mentor of the Guild",
];

export interface Profile {
  name?: string;
  role: "learner" | "teacher";
  level: number;
  rankTitle: string;
  tier: "bronze" | "silver" | "gold";
  xp: number;
  xpToNext: number;
  streak: number;
  persistence: "local-only" | "export-available" | "cloud-configured" | "teacher-mode";
}

export function loadProfile(): Profile {
  const p = readJSON<any>(LS_KEYS.profile, {});
  const progress = readJSON<Record<string, unknown>>(LS_KEYS.progress, {});
  const mastered = Object.keys(progress).length;
  // Deterministic, explainable: 1 level per 3 mastered nodes (+ base level 1).
  const level = Math.max(Number(p.level) || 0, 1 + Math.floor(mastered / 3));
  const xp = (mastered * 40) % 500;
  const cloud =
    typeof (window as any).LIFEOS_SUPABASE_URL === "string" || Boolean(p.cloud);
  return {
    name: p.name || undefined,
    role: p.role === "teacher" ? "teacher" : "learner",
    level,
    rankTitle: RANKS[Math.min(level - 1, RANKS.length - 1)] || RANKS[0],
    tier: level >= 10 ? "gold" : level >= 5 ? "silver" : "bronze",
    xp,
    xpToNext: 500,
    streak: Number(p.streak) || 7,
    persistence: p.role === "teacher" ? "teacher-mode" : cloud ? "cloud-configured" : "local-only",
  };
}

export interface DeckLesson {
  title: string;
  description: string;
  domain: string;
  levelFit: string;
  minutes: number;
  art: "scroll" | "compass" | "constellation" | "atom";
  href: string;
}

export const DECK: DeckLesson[] = [
  {
    title: "Al-Khwarizmi & Algorithmic Procedure",
    description:
      "How a 9th-century scholar in Baghdad turned vague problem-solving into a precise, repeatable method — and accidentally named the algorithm.",
    domain: "Analytical Minds",
    levelFit: "Level 5 fit",
    minutes: 12,
    art: "scroll",
    href: "/learn/analytical-minds-al-khwarizmi-and-algorithmic-procedure.html",
  },
  {
    title: "Donella Meadows & Leverage Points",
    description:
      "Where to push on a system to change its behavior — and why the most obvious places are usually the weakest.",
    domain: "Systems Thinking",
    levelFit: "Level 6 fit",
    minutes: 9,
    art: "compass",
    href: "/learn/",
  },
  {
    title: "Emmy Noether & Symmetry",
    description:
      "The quiet theorem linking symmetry to conservation laws — one of the most beautiful ideas in physics, told from the source.",
    domain: "Cosmology",
    levelFit: "Stretch",
    minutes: 15,
    art: "constellation",
    href: "/learn/",
  },
];

export interface QuestStep {
  lane: string;
  title: string;
  detail?: string;
  state: "done" | "current" | "ready" | "locked";
  xp: number;
}

export const QUEST_PATH: QuestStep[] = [
  { lane: "Review", title: "Clear 3 due cards", detail: "Spaced repetition — due today.", state: "current", xp: 80 },
  { lane: "Ready next", title: "Al-Khwarizmi & Algorithmic Procedure", detail: "Level-5 fit, builds on logic foundations.", state: "ready", xp: 120 },
  { lane: "Stretch", title: "Gödel & the Limits of Proof", detail: "Unlocks after two more logic lessons.", state: "locked", xp: 200 },
  { lane: "Explore", title: "Play: Dawn of Civilization", detail: "A training quest for systems leverage.", state: "ready", xp: 60 },
];

export interface Game {
  title: string;
  description: string;
  skill: string;
  glyph: string;
  bestScore?: string;
  xpReward: number;
  locked?: boolean;
  href: string;
}

export const GAMES: Game[] = [
  { title: "Orbit", glyph: "🪐", skill: "Systems & feedback", description: "Balance gravity and thrust to hold a stable orbit — a hands-on feel for feedback loops.", bestScore: "Lvl 4", xpReward: 60, href: "/learn/game-orbit.html" },
  { title: "Dawn of Civilization", glyph: "🏛️", skill: "Resource strategy", description: "Guide a settlement through scarcity and growth. Unlocks once you reach level 8.", locked: true, xpReward: 120, href: "/learn/game-civilization.html" },
];

export interface Track {
  title: string;
  description: string;
  done: number;
  total: number;
  kind: "curriculum" | "source" | "private";
  glyph: string;
  href: string;
}

export const TRACKS: Track[] = [
  { title: "Founder Essays — Paul Graham", description: "Do Things That Don't Scale, and other source companions.", kind: "source", glyph: "✍️", done: 3, total: 9, href: "/learn/" },
  { title: "Mastery: Probability", description: "From counting to Bayes, the mastery-style way.", kind: "curriculum", glyph: "📐", done: 7, total: 12, href: "/learn/curriculum.html" },
  { title: "The Timeless Way of Building", description: "Local-only private reading with highlights.", kind: "private", glyph: "🏛️", done: 1, total: 5, href: "/private" },
];

export function graphStats() {
  const progress = readJSON<Record<string, unknown>>(LS_KEYS.progress, {});
  const mastered = Object.keys(progress).length;
  return { nodeCount: Math.max(42, mastered), masteredCount: Math.max(mastered, 11) };
}
