import { useEffect, useMemo, useRef, useState, type CSSProperties, type PointerEvent as ReactPointerEvent } from "react";
import {
  MainQuestCard,
  DeckCard,
  DeckControls,
  GraphPreview,
  Pill,
} from "lifeos-ds";
import type { GraphPreviewNode } from "lifeos-ds";
import {
  loadProfile,
  graphStats,
  DECK,
  HUB_PORTALS,
  LS_KEYS,
  PRICE_PLANS,
  type DeckLesson,
  type PricePlan,
} from "./data";

const SWIPE_THRESHOLD = 86;
const SWIPE_EXIT_MS = 360;
const MEMORY_KEYS = [LS_KEYS.progress, LS_KEYS.profile, LS_KEYS.notes, LS_KEYS.skipped, LS_KEYS.yes, LS_KEYS.level] as const;

const NAV = [
  { id: "quest", ic: "📜", label: "Today's due" },
  { id: "deck", ic: "🃏", label: "Swipe deck" },
] as const;

type MiniGraph = { nodeCount: number; masteredCount: number; nodes: GraphPreviewNode[]; edges: [number, number][] };
type GraphNode = { id: string; title?: string; domain?: string; kind?: string; url?: string; summary?: string; difficulty?: string; xp?: number; x?: number; y?: number };
type GraphEdge = { from: string; to: string };
type AuthUser = { name?: string; email?: string; picture?: string; provider?: "google" | "local"; signedInAt?: string };
type GeneratedArtManifest = { records?: { id?: string; generated_available?: boolean }[] };

function go(id: string, close: () => void) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  close();
}

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

function memoryBundle() {
  const storage: Record<string, string> = {};
  for (const key of MEMORY_KEYS) {
    const value = localStorage.getItem(key);
    if (value != null) storage[key] = value;
  }
  return { version: 2, exported_at: new Date().toISOString(), storage };
}

function readAuthUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(LS_KEYS.authUser);
    return raw ? JSON.parse(raw) as AuthUser : null;
  } catch {
    return null;
  }
}

function readNotes() {
  return localStorage.getItem(LS_KEYS.notes) || "";
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

const SEEDED_GENERATED_ART_IDS = new Set<string>([
  "analytical-minds-al-khwarizmi-and-algorithmic-procedure",
  "analytical-minds-alan-turing-and-computability",
  "analytical-minds-descartes-and-coordinate-method",
  "analytical-minds-einstein-and-principle-reasoning",
  "analytical-minds-elinor-ostrom-and-commons-governance",
  "analytical-minds-euclid-and-axiomatic-structure",
  "analytical-minds-judea-pearl-and-causal-graphs",
  "analytical-minds-maxwell-and-field-equations",
]);

function mythicArtUrl(id: string) {
  return `/learn/art/mythic/${encodeURIComponent(id)}.svg`;
}

function generatedArtUrl(id: string) {
  return `/learn/art/generated/${encodeURIComponent(id)}.jpg`;
}

function artUrlForLesson(id: string, generatedArtIds: Set<string>) {
  return generatedArtIds.has(id) ? generatedArtUrl(id) : mythicArtUrl(id);
}

function useGeneratedArtIds() {
  const [ids, setIds] = useState(() => new Set(SEEDED_GENERATED_ART_IDS));
  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        let response = await fetch("/learn/art/mythic-art-manifest.json", { cache: "no-store" });
        if (!response.ok) response = await fetch("/output/learn/art/mythic-art-manifest.json", { cache: "no-store" });
        if (!response.ok) return;
        const manifest = await response.json() as GeneratedArtManifest;
        const available = new Set(SEEDED_GENERATED_ART_IDS);
        for (const record of manifest.records || []) {
          if (record.generated_available && record.id) available.add(record.id);
        }
        if (!cancelled) setIds(available);
      } catch {
        if (!cancelled) setIds(new Set(SEEDED_GENERATED_ART_IDS));
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);
  return ids;
}

function toDeckLesson(node: GraphNode, domains: { id: string; name?: string }[] | undefined, generatedArtIds: Set<string>): DeckLesson {
  return {
    id: node.id,
    title: node.title || shortLabel(node.id),
    description: node.summary || `Continue this source-first lesson from your graph frontier.`,
    domain: domainTitle(node.domain, domains),
    levelFit: levelFitFor(node),
    minutes: Math.max(8, Math.round((Number(node.xp) || 90) / 6)),
    art: artForDomain(node.domain),
    artUrl: artUrlForLesson(node.id, generatedArtIds),
    href: node.url || "/learn/",
  };
}

function useHubDeck(fallback: DeckLesson[], generatedArtIds: Set<string>) {
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
          .map(({ node }) => toDeckLesson(node, graph.domains, generatedArtIds));
        if (!cancelled && ranked.length) setLessons(ranked);
      } catch {
        if (!cancelled) setLessons(fallback);
      }
    }
    load();
    window.addEventListener("storage", load);
    return () => { cancelled = true; window.removeEventListener("storage", load); };
  }, [fallback, generatedArtIds]);
  return lessons;
}

function decodeGoogleCredential(credential: string): AuthUser {
  const payload = credential.split(".")[1];
  if (!payload) throw new Error("Google credential missing payload");
  const normalized = payload.replace(/-/g, "+").replace(/_/g, "/").padEnd(Math.ceil(payload.length / 4) * 4, "=");
  const binary = atob(normalized);
  const bytes = Uint8Array.from(binary, (c) => c.charCodeAt(0));
  const decoded = JSON.parse(new TextDecoder().decode(bytes));
  return {
    name: decoded.name,
    email: decoded.email,
    picture: decoded.picture,
    provider: "google",
    signedInAt: new Date().toISOString(),
  };
}

function googleClientId() {
  return String(((import.meta as any).env?.VITE_LIFEOS_GOOGLE_CLIENT_ID || (window as any).LIFEOS_GOOGLE_CLIENT_ID || "")).trim();
}

function loadGoogleScript() {
  if ((window as any).google?.accounts?.id) return Promise.resolve();
  return new Promise<void>((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>('script[src="https://accounts.google.com/gsi/client"]');
    if (existing) {
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener("error", () => reject(new Error("Google Identity script failed to load")), { once: true });
      return;
    }
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Google Identity script failed to load"));
    document.head.appendChild(script);
  });
}

function planHref(plan: PricePlan) {
  return String(((import.meta as any).env?.[plan.envKey] || (window as any)[plan.windowKey] || "")).trim();
}

export function Hub() {
  const [memoryVersion, setMemoryVersion] = useState(0);
  const [authUser, setAuthUser] = useState<AuthUser | null>(() => readAuthUser());
  const [notes, setNotes] = useState(() => readNotes());
  const profile = useMemo(loadProfile, [memoryVersion, authUser]);
  const stats = useMemo(graphStats, [memoryVersion]);
  const miniGraph = usePersonalMiniGraph({ nodeCount: stats.nodeCount, masteredCount: stats.masteredCount, nodes: [], edges: [] });
  const [open, setOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const [card, setCard] = useState(0);
  const [drag, setDrag] = useState({ dx: 0, dy: 0, active: false });
  const [exit, setExit] = useState<"left" | "right" | null>(null);
  const [notice, setNotice] = useState("");
  const [dismissed, setDismissed] = useState<Set<string>>(() => new Set());
  const dragStart = useRef<{ x: number; y: number } | null>(null);
  const generatedArtIds = useGeneratedArtIds();
  const deck = useHubDeck(DECK, generatedArtIds);
  const visibleDeck = useMemo(() => deck.filter((item) => !dismissed.has(item.id)), [deck, dismissed]);
  const dailyPicks = useMemo(() => visibleDeck.slice(0, 3), [visibleDeck]);
  const completed = useMemo(() => {
    return Object.entries(readDone())
      .sort((a, b) => Date.parse(String((b[1] as any)?.at || 0)) - Date.parse(String((a[1] as any)?.at || 0)))
      .slice(0, 6);
  }, [memoryVersion]);

  useEffect(() => {
    const refresh = () => {
      setMemoryVersion((n) => n + 1);
      setAuthUser(readAuthUser());
      setNotes(readNotes());
    };
    window.addEventListener("storage", refresh);
    return () => window.removeEventListener("storage", refresh);
  }, []);

  const lesson = visibleDeck[card % Math.max(1, visibleDeck.length)] || DECK[0];
  const deckArt = lesson.artUrl ? (
    <img
      className="hub__mythic-art"
      src={lesson.artUrl}
      alt=""
      loading="eager"
      onError={(event) => {
        const fallback = mythicArtUrl(lesson.id);
        if (!event.currentTarget.src.endsWith(fallback)) {
          event.currentTarget.src = fallback;
          return;
        }
        event.currentTarget.style.display = "none";
      }}
    />
  ) : lesson.art;
  const swipeStyle = {
    "--hub-dx": `${drag.dx}px`,
    "--hub-dy": `${Math.max(-28, Math.min(28, drag.dy))}px`,
    "--hub-rot": `${drag.dx / 18}deg`,
    "--hub-no-opacity": `${drag.dx < -18 ? Math.min(1, Math.abs(drag.dx) / 112) : 0}`,
    "--hub-read-opacity": `${drag.dx > 18 ? Math.min(1, drag.dx / 112) : 0}`,
  } as CSSProperties & Record<string, string>;

  function bumpMemory() {
    setMemoryVersion((n) => n + 1);
    window.dispatchEvent(new Event("storage"));
  }

  function resetSwipe() {
    dragStart.current = null;
    setDrag({ dx: 0, dy: 0, active: false });
  }

  function commitSwipe(direction: "left" | "right") {
    if (exit) return;
    setExit(direction);
    if (direction === "left") writeDeckChoice(LS_KEYS.skipped, lesson.id);
    else writeDeckChoice(LS_KEYS.yes, lesson.id);
    window.setTimeout(() => {
      if (direction === "right") {
        window.location.href = lesson.href;
        return;
      }
      setDismissed((prev) => new Set(prev).add(lesson.id));
      setCard(0);
      setExit(null);
      resetSwipe();
    }, SWIPE_EXIT_MS);
  }

  function onSwipeStart(event: ReactPointerEvent<HTMLDivElement>) {
    if (exit || (event.target as HTMLElement).closest("button,a")) return;
    dragStart.current = { x: event.clientX, y: event.clientY };
    event.currentTarget.setPointerCapture?.(event.pointerId);
    setDrag({ dx: 0, dy: 0, active: true });
  }

  function onSwipeMove(event: ReactPointerEvent<HTMLDivElement>) {
    if (!dragStart.current || exit) return;
    const dx = event.clientX - dragStart.current.x;
    const dy = event.clientY - dragStart.current.y;
    if (Math.abs(dx) > 8 && Math.abs(dx) > Math.abs(dy)) event.preventDefault();
    setDrag({ dx, dy, active: true });
  }

  function onSwipeEnd(event: ReactPointerEvent<HTMLDivElement>) {
    if (!dragStart.current || exit) return;
    const dx = event.clientX - dragStart.current.x;
    event.currentTarget.releasePointerCapture?.(event.pointerId);
    if (Math.abs(dx) >= SWIPE_THRESHOLD) {
      commitSwipe(dx < 0 ? "left" : "right");
      return;
    }
    resetSwipe();
  }

  function chooseDailyPick(id: string) {
    const index = visibleDeck.findIndex((item) => item.id === id);
    if (index >= 0) setCard(index);
    document.getElementById("deck")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function storeAuthUser(user: AuthUser) {
    localStorage.setItem(LS_KEYS.authUser, JSON.stringify(user));
    const profileData = readMap(LS_KEYS.profile);
    if (user.name && !profileData.name) {
      profileData.name = user.name;
      localStorage.setItem(LS_KEYS.profile, JSON.stringify(profileData));
    }
    setAuthUser(user);
    bumpMemory();
  }

  async function signInWithGoogle() {
    const clientId = googleClientId();
    if (!clientId) {
      setNotice("Google sign-in is ready, but no client ID is configured. Add VITE_LIFEOS_GOOGLE_CLIENT_ID in Vercel/local env.");
      setAccountOpen(true);
      return;
    }
    try {
      await loadGoogleScript();
      const google = (window as any).google;
      google.accounts.id.initialize({
        client_id: clientId,
        callback: (response: any) => {
          try {
            const user = decodeGoogleCredential(String(response?.credential || ""));
            storeAuthUser(user);
            setNotice(`Signed in as ${user.email || user.name || "Google user"}.`);
          } catch (error) {
            setNotice(error instanceof Error ? error.message : "Could not decode Google profile.");
          }
        },
      });
      google.accounts.id.prompt();
      setNotice("Google sign-in prompt opened.");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Google sign-in could not start.");
    }
  }

  function signOut() {
    localStorage.removeItem(LS_KEYS.authUser);
    setAuthUser(null);
    setNotice("Signed out locally.");
    bumpMemory();
  }

  function saveNotes() {
    localStorage.setItem(LS_KEYS.notes, notes.trim());
    setNotice("Notes saved locally and included in memory export.");
    bumpMemory();
  }

  function downloadMemory() {
    const blob = new Blob([JSON.stringify(memoryBundle(), null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `lifeos-memory-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
    setNotice("Memory bundle downloaded.");
  }

  async function sendToPhone() {
    const url = `${window.location.origin}/hub`;
    const title = "LifeOS morning quest";
    const text = "Open today's LifeOS learning deck on your phone.";
    try {
      if (navigator.share) {
        await navigator.share({ title, text, url });
        setNotice("Phone share sheet opened.");
        return;
      }
      await navigator.clipboard?.writeText(url);
      setNotice("Hub link copied. Send it to your phone or open it from mobile.");
    } catch {
      setNotice("Sharing was blocked. Copy this URL manually: " + url);
    }
  }

  function openPlan(plan: PricePlan) {
    const href = planHref(plan);
    if (!href) {
      setNotice(`Stripe checkout for ${plan.title} is ready, but ${plan.envKey} is not configured yet.`);
      return;
    }
    window.location.href = href;
  }

  function openPortal(href: string, localOnly?: boolean) {
    if (localOnly && !/^(localhost|127\.0\.0\.1)$/i.test(window.location.hostname)) {
      setNotice("That reader is local-only. Run LifeOS locally, then open /private.");
      return;
    }
    window.location.href = href;
  }

  return (
    <div className="lo-root hub">
      <header className="hub__topbar">
        <button className="hub__burger" aria-label="Open menu" onClick={() => setOpen(true)}>
          <span /><span /><span />
        </button>
        <div className="hub__wordmark">Life<b>OS</b></div>
        <div className="hub__topspacer" />
        <button className="hub__account" aria-expanded={accountOpen} onClick={() => { setAccountOpen((v) => !v); setOpen(false); }}>
          {authUser?.picture ? <img src={authUser.picture} alt="" /> : <span className="hub__account-avatar">🧙</span>}
          <span className="hub__account-copy">
            <strong>{authUser?.name || profile.name || "You"}</strong>
            <small>Level {profile.level} · {profile.rankTitle.split("·").pop()?.trim() || "Scout"}</small>
          </span>
          <span className="hub__account-xp">⭐ {profile.xp}/{profile.xpToNext}</span>
        </button>
      </header>

      <div className={`hub__scrim ${open ? "open" : ""}`} onClick={() => setOpen(false)} />
      <nav className={`hub__drawer ${open ? "open" : ""}`} aria-hidden={!open}>
        <div className="hub__drawer-head">
          <span className="hub__drawer-title">Quest menu</span>
          <button className="hub__drawer-close" aria-label="Close menu" onClick={() => setOpen(false)}>×</button>
        </div>
        <div className="hub__drawer-group">
          <div className="hub__drawer-kicker">Primary</div>
          {NAV.map((n) => (
            <button key={n.id} className="hub__navlink" onClick={() => go(n.id, () => setOpen(false))}>
              <span className="ic">{n.ic}</span>
              {n.label}
            </button>
          ))}
        </div>
        <div className="hub__drawer-group">
          <div className="hub__drawer-kicker">Secondary</div>
          {HUB_PORTALS.map((group) => (
            <div className="hub__drawer-subgroup" key={group.title}>
              <div className="hub__drawer-subtitle">{group.title}</div>
              {group.portals.map((portal) => (
                <button
                  key={portal.title}
                  className="hub__navlink hub__navlink--portal"
                  onClick={() => { setOpen(false); openPortal(portal.href, portal.localOnly); }}
                >
                  <span className="ic">{portal.glyph}</span>
                  {portal.title}
                </button>
              ))}
            </div>
          ))}
        </div>
      </nav>

      {accountOpen && <div className="hub__account-scrim" onClick={() => setAccountOpen(false)} />}
      {accountOpen && (
        <aside className="hub__account-panel" aria-label="Account, progress, and upgrade menu">
          <div className="hub__account-head">
            <div>
              <div className="hub__drawer-kicker">Your LifeOS</div>
              <h2>{authUser?.name || profile.name || "Adventurer"}</h2>
              <p>{authUser?.email || "Local-first profile"}</p>
            </div>
            <button className="hub__drawer-close" aria-label="Close account" onClick={() => setAccountOpen(false)}>×</button>
          </div>

          <div className="hub__account-stats">
            <div><b>L{profile.level}</b><span>{profile.rankTitle}</span></div>
            <div><b>{profile.streak}</b><span>day streak</span></div>
            <div><b>{completed.length}</b><span>recent done</span></div>
          </div>

          <div className="hub__account-actions">
            <button onClick={signInWithGoogle}>🔐 {authUser ? "Refresh Google" : "Sign in with Google"}</button>
            {authUser && <button className="ghost" onClick={signOut}>Sign out</button>}
            <button className="ghost" onClick={sendToPhone}>📱 Send to phone</button>
            <button className="ghost" onClick={downloadMemory}>💾 Export memory</button>
          </div>

          <section className="hub__account-card">
            <h3>Completed quests</h3>
            {completed.length ? (
              <ul className="hub__done-list">
                {completed.map(([id, item]) => (
                  <li key={id}><span>✓</span>{String((item as any)?.title || id).replace(/-/g, " ")}</li>
                ))}
              </ul>
            ) : <p>No completed quests yet. Read a card, mark it learned, and this fills in.</p>}
          </section>

          <GraphPreview
            className="hub__account-graph"
            nodeCount={miniGraph.nodeCount}
            masteredCount={miniGraph.masteredCount}
            nodes={miniGraph.nodes}
            edges={miniGraph.edges}
            onOpen={() => { window.location.href = "/learn/skill-tree.html"; }}
          />

          <section className="hub__account-card">
            <h3>Private notes</h3>
            <textarea
              className="hub__notes"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Capture what today changed in your model of the world."
            />
            <button className="hub__mini-action" onClick={saveNotes}>Save notes</button>
          </section>

          <section className="hub__account-card">
            <div className="hub__pricing-head">
              <div>
                <h3>Newcomer pricing</h3>
                <p>Early pricing for new learners only. Stripe Payment Links wire in by env var.</p>
              </div>
              <Pill tone="gold" variant="soft">Founding offer</Pill>
            </div>
            <div className="hub__plans">
              {PRICE_PLANS.map((plan) => (
                <button key={plan.id} className="hub__plan" onClick={() => openPlan(plan)}>
                  <span>{plan.title}</span>
                  <b>{plan.price}<small>{plan.cadence}</small></b>
                  <em>{plan.savings}</em>
                  <p>{plan.description}</p>
                </button>
              ))}
            </div>
          </section>
        </aside>
      )}

      <main className="hub__main hub__main--primary">
        {notice && <div className="hub__notice" role="status">{notice}</div>}

        <section id="quest" className="hub__section">
          <MainQuestCard
            kind="review"
            domain="Morning Agent"
            title="3 things are ready for you today"
            reason="Clear the due review, then pick from the agent's morning recommendations. Keep the streak alive without opening five dashboards."
            xpReward={80}
            minutes={6}
            onStart={() => { window.location.href = "/learn/learning-system.html"; }}
          />
          <div className="hub__morning" aria-label="Morning agent picks">
            <div className="hub__morning-head">
              <span>✨ Morning agent brief</span>
              <small>3 graph-ranked picks</small>
            </div>
            {dailyPicks.map((pick, index) => (
              <button key={pick.id} className="hub__morning-pick" onClick={() => chooseDailyPick(pick.id)}>
                <span>{index + 1}</span>
                <b>{pick.title}</b>
                <small>{pick.domain} · {pick.minutes} min</small>
              </button>
            ))}
          </div>
        </section>

        <section id="deck" className="hub__section">
          <div className="hub__section-head">
            <h2 className="hub__section-title">Learning deck</h2>
          </div>
          <div className="hub__deck-wrap">
            <div className="hub__deck-stack">
              <div
                key={lesson.id}
                className={["hub__swipe-card", drag.active ? "is-dragging" : "", exit ? `exit-${exit}` : ""].filter(Boolean).join(" ")}
                style={swipeStyle}
                onPointerDown={onSwipeStart}
                onPointerMove={onSwipeMove}
                onPointerUp={onSwipeEnd}
                onPointerCancel={resetSwipe}
              >
                <span className="hub__swipe-badge hub__swipe-badge--no">NO</span>
                <span className="hub__swipe-badge hub__swipe-badge--read">READ</span>
                <DeckCard
                  title={lesson.title}
                  description={lesson.description}
                  domain={lesson.domain}
                  levelFit={lesson.levelFit}
                  minutes={lesson.minutes}
                  art={deckArt}
                />
              </div>
            </div>
            <DeckControls
              onNo={() => commitSwipe("left")}
              onRead={() => commitSwipe("right")}
              disabled={Boolean(exit)}
            />
            <div className="hub__hint">{visibleDeck.length ? `Card ${(card % visibleDeck.length) + 1} of ${visibleDeck.length}` : "No graph-ranked cards left"} · graph-ranked · only "No" and "Read"</div>
          </div>
        </section>
      </main>
    </div>
  );
}
