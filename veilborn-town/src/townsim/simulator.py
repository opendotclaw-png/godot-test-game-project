from __future__ import annotations

from collections import defaultdict

from townsim.events import remember_many
from townsim.models import Event, NPC, Relationship, World

SLOTS = ["morning", "midday", "afternoon", "evening", "night"]


def _clamp(v: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, v))


def _rel_index(relationships: list[Relationship]) -> dict[tuple[str, str], int]:
    idx: dict[tuple[str, str], int] = {}
    for r in relationships:
        idx[(r.a, r.b)] = r.affinity
        idx[(r.b, r.a)] = r.affinity
    return idx


def _find_relationship(relationships: list[Relationship], a: str, b: str) -> Relationship | None:
    for r in relationships:
        if (r.a == a and r.b == b) or (r.a == b and r.b == a):
            return r
    return None


def _choose_location(world: World, npc: NPC, slot: str, intent: str, rng):
    if intent == "eat":
        preferred = ["tavern", "market"]
    elif intent == "rest":
        preferred = ["home"]
    elif intent == "work":
        preferred = ["workshop", "market"]
    else:
        preferred = ["tavern", "shrine"]

    open_pois = [p for p in world.pois if slot in p.open_slots]
    candidate = [p for p in open_pois if p.type in preferred]

    if not candidate:
        schedule_types = npc.schedule.get(slot, [])
        candidate = [p for p in open_pois if p.type in schedule_types]

    if not candidate:
        candidate = open_pois

    return rng.choice(candidate)


def _intent_for(npc: NPC, slot: str, rng) -> str:
    if npc.needs.hunger <= 30:
        return "eat"
    if npc.needs.rest <= 25:
        return "rest"
    if slot in ["morning", "midday", "afternoon"]:
        return "work"
    if rng.random() < 0.7:
        return "socialize"
    return "goal"


def simulate_days(world: World, days: int, rng) -> list[Event]:
    all_events: list[Event] = []
    last_location: dict[str, str] = {}

    for _ in range(days):
        for slot in SLOTS:
            world.time_slot = slot
            rel_map = _rel_index(world.relationships)
            slot_events: list[Event] = []

            chosen_locations: dict[str, str] = {}
            intent_by_npc: dict[str, str] = {}

            for npc in world.npcs:
                npc.needs.hunger = _clamp(npc.needs.hunger - 10)
                npc.needs.social = _clamp(npc.needs.social - 5)
                if slot != "night":
                    npc.needs.rest = _clamp(npc.needs.rest - 5)

                intent = _intent_for(npc, slot, rng)
                intent_by_npc[npc.id] = intent
                npc.current_plan = intent

                poi = _choose_location(world, npc, slot, intent, rng)
                chosen_locations[npc.id] = poi.id

                if last_location.get(npc.id) != poi.id:
                    e = Event(
                        day=world.day,
                        slot=slot,
                        type="move",
                        actors=[npc.id],
                        location=poi.id,
                        text=f"{npc.name} moves to {poi.name}.",
                        effects={},
                    )
                    slot_events.append(e)
                    remember_many([npc], e.text)
                last_location[npc.id] = poi.id

            by_location: dict[str, list[NPC]] = defaultdict(list)
            npc_index = {n.id: n for n in world.npcs}
            for npc_id, poi_id in chosen_locations.items():
                by_location[poi_id].append(npc_index[npc_id])

            coins = world.state.setdefault("coins", {})

            for npc in world.npcs:
                intent = intent_by_npc[npc.id]
                poi_id = chosen_locations[npc.id]
                if intent == "eat":
                    npc.needs.hunger = _clamp(npc.needs.hunger + 40)
                    e = Event(
                        day=world.day,
                        slot=slot,
                        type="buy",
                        actors=[npc.id],
                        location=poi_id,
                        text=f"{npc.name} eats a meal.",
                        effects={"hunger": +40},
                    )
                    slot_events.append(e)
                    remember_many([npc], e.text)
                elif intent == "rest":
                    npc.needs.rest = _clamp(npc.needs.rest + 50)
                    e = Event(
                        day=world.day,
                        slot=slot,
                        type="rest",
                        actors=[npc.id],
                        location=poi_id,
                        text=f"{npc.name} gets some rest.",
                        effects={"rest": +50},
                    )
                    slot_events.append(e)
                    remember_many([npc], e.text)
                elif intent == "work":
                    npc.needs.hunger = _clamp(npc.needs.hunger - 5)
                    coins[npc.id] = int(coins.get(npc.id, 0)) + 3
                    e = Event(
                        day=world.day,
                        slot=slot,
                        type="work",
                        actors=[npc.id],
                        location=poi_id,
                        text=f"{npc.name} works a shift.",
                        effects={"coins": +3, "hunger": -5},
                    )
                    slot_events.append(e)
                    remember_many([npc], e.text)
                elif intent == "goal":
                    goal = rng.choice(npc.goals)
                    e = Event(
                        day=world.day,
                        slot=slot,
                        type="rumor",
                        actors=[npc.id],
                        location=poi_id,
                        text=f"{npc.name} pursues a goal: {goal}.",
                        effects={},
                    )
                    slot_events.append(e)
                    remember_many([npc], e.text)

            for poi_id, here in by_location.items():
                if len(here) < 2:
                    continue
                for npc in here:
                    others = [o for o in here if o.id != npc.id]
                    if not others:
                        continue
                    partner = rng.choice(others)
                    affinity = rel_map.get((npc.id, partner.id), 0)
                    talk_chance = 0.2 + (100 - npc.needs.social) / 200 + max(0, affinity) / 250
                    if rng.random() < min(0.9, talk_chance):
                        npc.needs.social = _clamp(npc.needs.social + 10)
                        partner.needs.social = _clamp(partner.needs.social + 10)
                        nudge = rng.choice([-1, 0, 1])
                        rel = _find_relationship(world.relationships, npc.id, partner.id)
                        if rel is not None:
                            rel.affinity = max(-100, min(100, rel.affinity + nudge))
                        text = f"{npc.name} chats with {partner.name}."
                        e = Event(
                            day=world.day,
                            slot=slot,
                            type="talk",
                            actors=[npc.id, partner.id],
                            location=poi_id,
                            text=text,
                            effects={"social": +10, "affinity": nudge},
                        )
                        slot_events.append(e)
                        remember_many([npc, partner], text)

            all_events.extend(slot_events)

        world.day += 1
        world.time_slot = "morning"

    return all_events
