from __future__ import annotations

import argparse
import json
from pathlib import Path

from townsim.generator import generate_world
from townsim.persistence import append_events_jsonl, load_world, save_world
from townsim.rng import make_rng
from townsim.simulator import simulate_days


def _log_path_from_world(world_path: Path) -> Path:
    return world_path.with_name("event_log.jsonl")


def cmd_generate(args: argparse.Namespace) -> None:
    rng = make_rng(args.seed)
    world = generate_world(seed=args.seed, rng=rng)
    out = Path(args.out)
    save_world(out, world)
    print(f"Generated world at {out}")


def cmd_simulate(args: argparse.Namespace) -> None:
    world_path = Path(args.world)
    world = load_world(world_path)
    rng = make_rng(world.seed)
    events = simulate_days(world=world, days=args.days, rng=rng)
    append_events_jsonl(_log_path_from_world(world_path), events)
    save_world(world_path, world)
    print(f"Simulated {args.days} day(s), wrote {len(events)} events")


def _read_last_events(log_path: Path, limit: int = 5) -> list[dict]:
    if not log_path.exists():
        return []
    lines = [ln for ln in log_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    out = []
    for ln in lines[-limit:]:
        out.append(json.loads(ln))
    return out


def cmd_show(args: argparse.Namespace) -> None:
    world_path = Path(args.world)
    world = load_world(world_path)
    print(f"World: {world.world_id}")
    print(f"Town: {world.town.name} ({', '.join(world.town.tags)})")
    print(f"Day: {world.day}, Slot: {world.time_slot}")
    print(f"POIs: {len(world.pois)}, NPCs: {len(world.npcs)}, Relationships: {len(world.relationships)}")
    print("NPCs:")
    for npc in world.npcs:
        top_goal = npc.goals[0] if npc.goals else "(none)"
        print(f"- {npc.name}: {top_goal}")

    events = _read_last_events(_log_path_from_world(world_path), limit=5)
    if events:
        print("Last events:")
        for e in events:
            print(f"- [d{e['day']} {e['slot']}] {e['text']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="townsim")
    sub = parser.add_subparsers(dest="command", required=True)

    p_gen = sub.add_parser("generate", help="Generate a deterministic town world")
    p_gen.add_argument("--seed", type=int, required=True)
    p_gen.add_argument("--out", type=str, required=True)
    p_gen.set_defaults(func=cmd_generate)

    p_sim = sub.add_parser("simulate", help="Simulate one or more in-game days")
    p_sim.add_argument("--world", type=str, required=True)
    p_sim.add_argument("--days", type=int, default=1)
    p_sim.set_defaults(func=cmd_simulate)

    p_show = sub.add_parser("show", help="Show a world summary")
    p_show.add_argument("--world", type=str, required=True)
    p_show.set_defaults(func=cmd_show)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
