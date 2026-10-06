"""RAW: baixa a camada via WFS 2.0 com paginação e grava páginas imutáveis + manifesto."""
import hashlib
import json
from datetime import datetime, timezone

import requests

from .config import DATA, Layer

_PARAMS = {"service": "WFS", "version": "2.0.0", "request": "GetFeature",
           "outputFormat": "application/json"}


def _get(session: requests.Session, url: str, params: dict, retries: int = 4) -> bytes:
    for i in range(retries):
        try:
            r = session.get(url, params=params, timeout=120)
            r.raise_for_status()
            return r.content
        except requests.RequestException:
            if i == retries - 1:
                raise


def ingest(cfg: dict, layer: Layer) -> dict:
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = DATA / "raw" / layer.name / run
    out.mkdir(parents=True)
    size, start, pages, total = cfg["page_size"], 0, [], 0
    with requests.Session() as s:
        while True:
            body = _get(s, cfg["wfs_url"], {**_PARAMS, "typeNames": layer.typename,
                        "count": size, "startIndex": start, "sortBy": layer.key})
            n = len(json.loads(body)["features"])
            if n == 0:
                break
            f = out / f"page_{len(pages):05d}.json"
            f.write_bytes(body)
            pages.append({"file": f.name, "rows": n, "sha256": hashlib.sha256(body).hexdigest()})
            total += n
            start += n
            if n < size:
                break
    manifest = {"layer": layer.name, "typename": layer.typename, "run": run,
                "rows": total, "pages": pages}
    (out / "_manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest
