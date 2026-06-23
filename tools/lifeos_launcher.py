#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tkinter as tk
from pathlib import Path

from lifeos_paths import APP_ROOT, VAULT_ROOT

ROOT = VAULT_ROOT
OPEN_SCRIPT = APP_ROOT / "tools" / "open_lifeos_dashboard.ps1"


def launch_lifeos() -> None:
    subprocess.Popen([
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(OPEN_SCRIPT),
    ], cwd=str(APP_ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> int:
    root = tk.Tk()
    root.title("LifeOS")
    root.attributes("-topmost", True)
    root.resizable(False, False)
    root.configure(bg="#020403")

    # Small floating HUD button. Right-click closes it.
    button = tk.Button(
        root,
        text="LifeOS",
        command=launch_lifeos,
        bg="#39ff88",
        fg="#031006",
        activebackground="#00f5ff",
        activeforeground="#031006",
        relief="flat",
        font=("Consolas", 11, "bold"),
        padx=14,
        pady=8,
        cursor="hand2",
    )
    button.pack()
    button.bind("<Button-3>", lambda _event: root.destroy())

    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = screen_w - width - 18
    y = screen_h - height - 58
    root.geometry(f"{width}x{height}+{x}+{y}")

    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
