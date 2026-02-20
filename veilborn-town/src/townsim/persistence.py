from __future__ import annotations

import json
from pathlib import Path

from townsim.models import Event, World


def load_world(path: str | Path) -> World:
    p = Path(path)
    return World.model_validate_json(p.read_text(encoding="utf-8"))


def save_world(path: str | Path, world: World) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(world.model_dump_json(indent=2), encoding="utf-8")


def append_events_jsonl(path: str | Path, events: list[Event]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event.model_dump(), ensure_ascii=False) + "\n")
