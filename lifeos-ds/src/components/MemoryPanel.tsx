import { Button } from "./Button";
import { Pill } from "./Pill";
import "./MemoryPanel.css";

export type CloudState = "configured" | "not-configured";

export interface MemoryPanelProps {
  /** Whether optional cloud sync (Supabase) is configured in the environment. */
  cloud?: CloudState;
  /** The current sync code to copy/paste, if generated. */
  syncCode?: string;
  /** Handlers for the memory tools. */
  onExport?: () => void;
  onImport?: () => void;
  onCopyCode?: () => void;
  onCloudLogin?: () => void;
  className?: string;
}

/**
 * Local-first memory tools — "How is my memory persisted?". Export/import the
 * LifeOS memory JSON, copy a sync code, and (only if configured) sign in for
 * cloud sync. When cloud isn't configured the UI says so plainly.
 */
export function MemoryPanel({
  cloud = "not-configured",
  syncCode,
  onExport,
  onImport,
  onCopyCode,
  onCloudLogin,
  className,
}: MemoryPanelProps) {
  const cloudOn = cloud === "configured";
  return (
    <section className={["lo-mem", className || ""].filter(Boolean).join(" ")}>
      <div className="lo-mem__head">
        <div>
          <div className="lo-kicker">Your memory</div>
          <h3 className="lo-mem__title lo-display">Profile &amp; persistence</h3>
        </div>
        <Pill tone={cloudOn ? "green" : "neutral"} variant="soft" icon={cloudOn ? "☁️" : "💾"}>
          {cloudOn ? "Cloud configured" : "Local only"}
        </Pill>
      </div>

      <p className="lo-mem__note lo-serif">
        Your progress lives in this browser first. Export it to move devices, or
        share a sync code with a mentor.
      </p>

      <div className="lo-mem__actions">
        <Button variant="primary" size="sm" icon="⬇" onClick={onExport}>Export memory</Button>
        <Button variant="ghost" size="sm" icon="⬆" onClick={onImport}>Import memory</Button>
      </div>

      {syncCode && (
        <div className="lo-mem__code">
          <span className="lo-mem__code-label">Sync code</span>
          <code className="lo-mem__code-val">{syncCode}</code>
          <Button variant="link" size="sm" onClick={onCopyCode}>Copy</Button>
        </div>
      )}

      <div className={`lo-mem__cloud ${cloudOn ? "" : "lo-mem__cloud--off"}`}>
        {cloudOn ? (
          <>
            <span className="lo-mem__cloud-txt lo-serif">
              Cloud sync is available via magic link.
            </span>
            <Button variant="quest" size="sm" icon="☁️" onClick={onCloudLogin}>
              Sign in to sync
            </Button>
          </>
        ) : (
          <span className="lo-mem__cloud-txt lo-serif">
            ☁️ Cloud sync is <b>not configured</b>. Set <code>LIFEOS_SUPABASE_URL</code>{" "}
            and <code>LIFEOS_SUPABASE_ANON_KEY</code> to enable it.
          </span>
        )}
      </div>
    </section>
  );
}
