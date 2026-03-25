from pathlib import Path

def read_pgm_size(pgm_path: Path) -> tuple[int, int]:
    with open(pgm_path, "rb") as f:
        magic = f.readline().decode().strip()
        if magic not in ("P5", "P2"):
            raise ValueError(f"Unsupported PGM format: {magic}")

        # Skip comments
        line = f.readline().decode().strip()
        while line.startswith("#"):
            line = f.readline().decode().strip()

        width, height = map(int, line.split())
        return width, height