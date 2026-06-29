import type { ButtonHTMLAttributes, ReactNode } from "react";
import "./Button.css";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** `primary` is the terracotta call-to-action; `quest` is the gold hero
   *  button; `ghost` is a quiet bordered button; `link` is text-only. */
  variant?: "primary" | "quest" | "ghost" | "link";
  /** Control height. */
  size?: "sm" | "md" | "lg";
  /** Stretches the button to fill its container width. */
  block?: boolean;
  /** Optional leading glyph/emoji. */
  icon?: ReactNode;
  children: ReactNode;
}

/**
 * Primary action control for the Quest Hub. Terracotta primary, gold quest,
 * and quiet ghost/link variants — all in the parchment idiom.
 */
export function Button({
  variant = "primary",
  size = "md",
  block = false,
  icon,
  children,
  className,
  type = "button",
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      className={[
        "lo-btn",
        `lo-btn--${variant}`,
        `lo-btn--${size}`,
        block ? "lo-btn--block" : "",
        className || "",
      ]
        .filter(Boolean)
        .join(" ")}
      {...rest}
    >
      {icon && <span className="lo-btn__icon">{icon}</span>}
      <span>{children}</span>
    </button>
  );
}
