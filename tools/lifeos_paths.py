from __future__ import annotations

import os
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
VAULT_ROOT = Path(os.environ.get("LIFEOS_VAULT", r"C:\Users\adars\adarsha-knowledge-base")).expanduser().resolve()
