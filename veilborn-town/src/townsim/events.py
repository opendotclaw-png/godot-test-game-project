from __future__ import annotations

from townsim.models import Event, NPC


def remember(npc: NPC, text: str, max_items: int = 10) -> None:
    npc.memory.append(text)
    if len(npc.memory) > max_items:
        del npc.memory[:-max_items]


def remember_many(npcs: list[NPC], text: str) -> None:
    for npc in npcs:
        remember(npc, text)


def event_text(event: Event) -> str:
    return event.text
