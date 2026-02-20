# townsim

Tiny deterministic CLI town simulation (vertical slice).

It can:
- generate a small world from a seed
- persist world state to `world.json`
- simulate discrete daily time slots
- append events to `event_log.jsonl`

## Requirements
- Python 3.12+
- `uv`

## Setup
```bash
cd veilborn-town
uv venv
uv pip install -e .
```

## Usage
Generate:
```bash
townsim generate --seed 123 --out runs/seed123/world.json
```

Simulate one day:
```bash
townsim simulate --world runs/seed123/world.json --days 1
```

Show summary:
```bash
townsim show --world runs/seed123/world.json
```

## Example show output
```text
World: world-123
Town: Stoneford (trade, river)
Day: 1, Slot: morning
POIs: 13, NPCs: 8, Relationships: 10
NPCs:
- Arin: keep the town safe
- Bela: earn enough coins
...
Last events:
- [d0 evening] Dara chats with Bela.
- [d0 night] Corin gets some rest.
```
