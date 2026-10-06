import re
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"


@dataclass(frozen=True)
class Layer:
    name: str
    typename: str
    srid: int
    key: str
    date_cols: list[str]
    text_cols: list[str]
    metadata_uuid: str | None = None
    family: str | None = None


def load(path: Path = ROOT / "config" / "layers.yaml") -> tuple[dict, dict[str, Layer]]:
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    layers = {n: Layer(name=n, **v) for n, v in cfg.pop("layers").items()}
    for fam, spec in (cfg.pop("families", None) or {}).items():
        from .catalog import CATALOG, read
        if not CATALOG.exists():
            continue
        rx, skip = re.compile(spec["pattern"]), set(spec.get("exclude", []))
        for row in read():
            if rx.search(row["name"]) and row["name"] not in skip and row["name"] not in layers:
                layers[row["name"]] = Layer(
                    name=row["name"], typename=row["typename"], srid=int(row["srid"]),
                    key=spec["key"], date_cols=spec["date_cols"], text_cols=spec["text_cols"],
                    family=fam)
    return cfg, layers
