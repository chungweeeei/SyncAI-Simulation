import json
from pathlib import Path
from typing import Dict, List, Optional


class VertexResolver:

    def __init__(self, map_name: str):
        self._vertices: List[dict] = []
        self._by_name: Dict[str, dict] = {}
        self._load(map_name)

    def _load(self, map_name: str):
        vertexes_path = Path(f"~/map/{map_name}_vertexes.json").expanduser()
        if not vertexes_path.exists():
            return

        with open(vertexes_path) as f:
            self._vertices = json.load(f)

        for v in self._vertices:
            self._by_name[v["name"].lower().strip()] = v

    def resolve(self, name: str) -> Optional[dict]:
        return self._by_name.get(name.lower().strip())

    def get_all_vertices(self) -> List[dict]:
        return self._vertices
