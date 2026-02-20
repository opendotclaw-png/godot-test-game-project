from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Slot = Literal["morning", "midday", "afternoon", "evening", "night"]
PoiType = Literal["tavern", "market", "shrine", "workshop", "home", "gate"]
EventType = Literal["move", "talk", "buy", "work", "rest", "rumor"]


class Needs(BaseModel):
    hunger: int = Field(ge=0, le=100)
    rest: int = Field(ge=0, le=100)
    social: int = Field(ge=0, le=100)


class POI(BaseModel):
    id: str
    name: str
    type: PoiType
    tags: list[str] = Field(default_factory=list)
    open_slots: list[Slot]


class NPC(BaseModel):
    id: str
    name: str
    personality: list[str] = Field(min_length=3, max_length=5)
    needs: Needs
    home_poi_id: str
    schedule: dict[Slot, list[str]]
    goals: list[str] = Field(min_length=2, max_length=4)
    current_plan: str | None = None
    memory: list[str] = Field(default_factory=list)


class Relationship(BaseModel):
    a: str
    b: str
    affinity: int = Field(ge=-100, le=100)


class Town(BaseModel):
    name: str
    tags: list[str] = Field(default_factory=list)


class World(BaseModel):
    world_id: str
    seed: int
    day: int = 0
    time_slot: Slot = "morning"
    town: Town
    pois: list[POI]
    npcs: list[NPC]
    relationships: list[Relationship] = Field(default_factory=list)
    state: dict[str, object] = Field(default_factory=dict)


class Event(BaseModel):
    day: int
    slot: Slot
    type: EventType
    actors: list[str]
    location: str | None = None
    text: str
    effects: dict[str, object] = Field(default_factory=dict)
