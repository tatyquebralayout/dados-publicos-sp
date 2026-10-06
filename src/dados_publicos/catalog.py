"""Lê o GetCapabilities do WFS e grava o catálogo completo em config/catalog.csv."""
import csv
import xml.etree.ElementTree as ET

import requests

from .config import ROOT

_NS = {"w": "http://www.opengis.net/wfs/2.0"}
CATALOG = ROOT / "config" / "catalog.csv"


def build(cfg: dict) -> int:
    r = requests.get(cfg["wfs_url"], params={"service": "WFS", "version": "2.0.0",
                     "request": "GetCapabilities"}, timeout=180)
    r.raise_for_status()
    rows = []
    for f in ET.fromstring(r.content).findall(".//w:FeatureType", _NS):
        name = f.find("w:Name", _NS).text
        crs = f.find("w:DefaultCRS", _NS).text.rsplit(":", 1)[-1]
        rows.append({"typename": name, "name": name.split(":", 1)[-1],
                     "title": (f.find("w:Title", _NS).text or "").strip(), "srid": crs})
    rows.sort(key=lambda x: x["name"].lower())
    with CATALOG.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["typename", "name", "title", "srid"])
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def read() -> list[dict]:
    with CATALOG.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))
