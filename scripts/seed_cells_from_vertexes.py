"""Seed WMS cells from map/<map>_vertexes.json.

Idempotent-ish: if a cell with the same display_name already exists in the
target map, it is left alone (POST returns 409). Run after WMS is up and the
cells table has the latest schema (including cell_orientation_r).
"""

import json
import os
import sys
from pathlib import Path

import requests

WMS_URL = os.getenv("SYNCAI_WMS_URL", "http://localhost:8100")
MAP_ID = os.getenv("MAP_ID", "testmap")
AREA_ID = os.getenv("AREA_ID", "default")
VERTEX_FILE = Path(os.getenv(
    "VERTEX_FILE",
    Path(__file__).resolve().parent.parent / "map" / f"{MAP_ID}_vertexes.json",
))

# display_name -> (category, function_type_name)
CATEGORY_MAP: dict[str, tuple[str, str]] = {
    "meeting_room":          ("GENERAL",  "MEETING_ROOM"),
    "pantry":                ("GENERAL",  "PANTRY"),
    "elevator_waiting_point":("WAITING",  "ELEVATOR_WAITING"),
    "waiting_point_01":      ("WAITING",  "GENERAL_WAITING"),
    "waiting_point_02":      ("WAITING",  "GENERAL_WAITING"),
    "front_door":            ("GENERAL",  "FRONT_DOOR"),
    "charging_station":      ("CHARGER",  "CHARGING_STATION"),
    "elevator":              ("GENERAL",  "ELEVATOR"),
    "pickup_conveyor_01":    ("PICKUP",   "CONVEYOR_PICKUP"),
    "dropoff_a":             ("DROPOFF",  "AMR_DROPOFF"),
}


def main() -> int:
    if not VERTEX_FILE.exists():
        print(f"vertex file not found: {VERTEX_FILE}", file=sys.stderr)
        return 1

    vertexes = json.loads(VERTEX_FILE.read_text())
    print(f"Seeding {len(vertexes)} cells from {VERTEX_FILE.name} into map={MAP_ID!r}")

    created = skipped = failed = 0
    for v in vertexes:
        name = v["name"]
        pose = v["pose"]
        category, function_name = CATEGORY_MAP.get(name, ("GENERAL", name.upper()))

        payload = {
            "map_id": MAP_ID,
            "area_id": AREA_ID,
            "cell_position_x": pose["x"],
            "cell_position_y": pose["y"],
            "cell_orientation_r": pose.get("theta", 0.0),
            "display_name": name,
            "function_type_category": category,
            "function_type_name": function_name,
        }
        resp = requests.post(f"{WMS_URL}/api/v1/wms/cells", json=payload, timeout=10)
        if resp.status_code == 201:
            print(f"  + {name:25s} -> {category}/{function_name}")
            created += 1
        elif resp.status_code == 409:
            print(f"  = {name:25s} (already exists, skipped)")
            skipped += 1
        else:
            print(f"  ! {name:25s} HTTP {resp.status_code}: {resp.text}")
            failed += 1

    print(f"\nDone. created={created} skipped={skipped} failed={failed}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
