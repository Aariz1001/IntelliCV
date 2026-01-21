from __future__ import annotations

import json
from pathlib import Path


def load_json(path: str) -> dict:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return json.loads(file_path.read_text(encoding="utf-8"))


def save_json(data: dict, path: str) -> None:
    file_path = Path(path)
    file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
