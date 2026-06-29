import "./DeckControls.css";

export interface DeckControlsProps {
  /** Skip the current card. */
  onNo?: () => void;
  /** Open/read the current card's lesson. */
  onRead?: () => void;
  /** Disable both controls (e.g. while animating or deck empty). */
  disabled?: boolean;
  className?: string;
}

/**
 * The deck's bottom controls — deliberately just two: No and Read.
 * This is the product's non-negotiable Tinder-deck contract; keep it minimal.
 */
export function DeckControls({ onNo, onRead, disabled = false, className }: DeckControlsProps) {
  return (
    <div className={["lo-deckctl", className || ""].filter(Boolean).join(" ")}>
      <button
        type="button"
        className="lo-deckctl__btn lo-deckctl__no"
        onClick={onNo}
        disabled={disabled}
        aria-label="No, skip this card"
      >
        <span className="lo-deckctl__glyph">✕</span>
        <span className="lo-deckctl__label">No</span>
      </button>
      <button
        type="button"
        className="lo-deckctl__btn lo-deckctl__read"
        onClick={onRead}
        disabled={disabled}
        aria-label="Read this lesson"
      >
        <span className="lo-deckctl__glyph">📖</span>
        <span className="lo-deckctl__label">Read</span>
      </button>
    </div>
  );
}
