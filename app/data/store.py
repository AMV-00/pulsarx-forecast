"""Save files as JSON in data/ (works offline, easy to show judges)."""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _path(name: str) -> Path:
    DATA_DIR.mkdir(exist_ok=True)
    return DATA_DIR / f"{name}.json"


def save(name: str, data) -> None:
    # Write to a temp file, then swap it in, so a reader never sees a half-written file
    p = _path(name)
    tmp = p.with_suffix(f".{os.getpid()}.{time.monotonic_ns()}.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    for _ in range(20):
        try:
            os.replace(tmp, p)
            return
        except PermissionError:  # Windows: file briefly open by a reader
            time.sleep(0.02)
    os.replace(tmp, p)


def load(name: str, default=None):
    p = _path(name)
    for _ in range(20):
        if not p.exists():
            return default
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, PermissionError):
            time.sleep(0.02)  # another request is writing; try again
    return default


def append(name: str, item: dict) -> dict:
    items = load(name, [])
    item = {**item, "time": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    items.append(item)
    save(name, items)
    return item
