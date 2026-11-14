"""Save files as JSON in data/ (works offline, easy to show judges)."""
import json
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _path(name: str) -> Path:
    DATA_DIR.mkdir(exist_ok=True)
    return DATA_DIR / f"{name}.json"


def save(name: str, data) -> None:
    _path(name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load(name: str, default=None):
    p = _path(name)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def append(name: str, item: dict) -> dict:
    items = load(name, [])
    item = {**item, "time": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    items.append(item)
    save(name, items)
    return item
