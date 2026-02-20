from __future__ import annotations

from townsim.models import NPC, POI, Relationship, Town, World

SLOTS = ["morning", "midday", "afternoon", "evening", "night"]

TOWN_PREFIXES = ["Oak", "River", "Stone", "Moss", "Bright", "Ash"]
TOWN_SUFFIXES = ["hollow", "ford", "stead", "brook", "cross", "gate"]
TOWN_TAGS = ["trade", "quiet", "pilgrim", "frontier", "river", "craft"]

NPC_NAMES = [
    "Arin", "Bela", "Corin", "Dara", "Edda", "Fenn", "Galen", "Hale",
    "Iris", "Jora", "Kellan", "Lina",
]
TRAITS = ["kind", "stern", "curious", "witty", "greedy", "patient", "brave", "shy"]
GOALS = [
    "earn enough coins", "repair the old gate", "gain local respect", "learn shrine rites",
    "open a better stall", "find a reliable partner", "keep the town safe", "throw a feast",
]


def _pick_many(rng, items: list[str], n: int) -> list[str]:
    return rng.sample(items, k=n)


def _schedule_for(rng) -> dict[str, list[str]]:
    return {
        "morning": ["workshop", "market"],
        "midday": ["market", "workshop", "tavern"],
        "afternoon": ["workshop", "market"],
        "evening": [rng.choice(["tavern", "shrine"]), "home"],
        "night": ["home", "tavern"],
    }


def generate_world(seed: int, rng) -> World:
    town_name = f"{rng.choice(TOWN_PREFIXES)}{rng.choice(TOWN_SUFFIXES)}"
    town_tags = _pick_many(rng, TOWN_TAGS, rng.randint(2, 3))

    pois: list[POI] = [
        POI(id="poi-tavern", name="Driftwood Tavern", type="tavern", tags=["food", "rumors"], open_slots=SLOTS),
        POI(id="poi-market", name="Town Market", type="market", tags=["trade"], open_slots=["morning", "midday", "afternoon", "evening"]),
        POI(id="poi-shrine", name="Lantern Shrine", type="shrine", tags=["ritual"], open_slots=["morning", "evening", "night"]),
        POI(id="poi-workshop", name="Oldmill Workshop", type="workshop", tags=["craft"], open_slots=["morning", "midday", "afternoon"]),
        POI(id="poi-gate", name="North Gate", type="gate", tags=["watch"], open_slots=SLOTS),
    ]

    chosen_names = rng.sample(NPC_NAMES, k=8)
    npcs: list[NPC] = []

    for i, name in enumerate(chosen_names):
        home_id = f"poi-home-{i+1}"
        pois.append(
            POI(
                id=home_id,
                name=f"{name}'s Home",
                type="home",
                tags=["residence"],
                open_slots=SLOTS,
            )
        )
        npcs.append(
            NPC(
                id=f"npc-{i+1}",
                name=name,
                personality=_pick_many(rng, TRAITS, rng.randint(3, 5)),
                needs={
                    "hunger": rng.randint(60, 90),
                    "rest": rng.randint(60, 90),
                    "social": rng.randint(60, 90),
                },
                home_poi_id=home_id,
                schedule=_schedule_for(rng),
                goals=_pick_many(rng, GOALS, rng.randint(2, 4)),
            )
        )

    relationships: list[Relationship] = []
    seen_pairs: set[tuple[int, int]] = set()
    while len(relationships) < 10:
        a = rng.randrange(0, len(npcs))
        b = rng.randrange(0, len(npcs))
        if a == b:
            continue
        p = tuple(sorted((a, b)))
        if p in seen_pairs:
            continue
        seen_pairs.add(p)
        relationships.append(
            Relationship(
                a=npcs[a].id,
                b=npcs[b].id,
                affinity=rng.randint(-40, 60),
            )
        )

    return World(
        world_id=f"world-{seed}",
        seed=seed,
        day=0,
        time_slot="morning",
        town=Town(name=town_name, tags=town_tags),
        pois=pois,
        npcs=npcs,
        relationships=relationships,
        state={"coins": {}},
    )
