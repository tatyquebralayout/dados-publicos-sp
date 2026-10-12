"""SP156 completo: descobre os CSVs no CKAN e baixa de forma resumível (verifica tamanho)."""
import csv
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor

import requests

from .config import DATA, ROOT

UA = {"User-Agent": "Mozilla/5.0 dados-publicos"}
RAW = DATA / "raw" / "sp156"
INDEX = ROOT / "config" / "sp156_resources.csv"
_PERIOD = re.compile(r"(?:(\d)º\s*TRI|(\d)[º°]\s*SEM)\s*(\d{4})", re.I)


def _period(name: str):
    m = _PERIOD.search(name)
    if not m:
        return None
    year = int(m.group(3))
    if m.group(1):
        return year, f"{year}T{m.group(1)}"
    return year, f"{year}S{m.group(2)}"


def get_json(url: str, tentativas: int = 5) -> dict:
    """GET com retentativa e espera crescente; o CKAN derruba conexões de vez em quando."""
    for i in range(tentativas):
        try:
            r = requests.get(url, headers=UA, timeout=120)
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError):
            if i == tentativas - 1:
                raise
            time.sleep(5 * 2 ** i)


def listar(cfg: dict) -> list[dict]:
    """Lista os recursos de dados do CKAN (um por período, CSV preferido), sem gravar nada."""
    best: dict[str, dict] = {}
    for res in get_json(cfg["sp156"]["ckan_package"])["result"]["resources"]:
        if not res["name"].strip().startswith("Dados do SP156"):
            continue
        p = _period(res["name"])
        if not p or p[0] < cfg["sp156"]["from_year"]:
            continue
        url, fmt = res["url"], res["format"].lower().strip(".")
        ext = url.rsplit(".", 1)[-1].lower()
        if ext not in ("csv", "xlsx"):
            continue
        cur = best.get(p[1])
        # CSV tem prioridade; o CKAN às vezes rotula .xlsx como CSV, então vale a extensão real da URL
        if cur is None or (ext == "csv" and cur["ext"] != "csv"):
            best[p[1]] = {"periodo": p[1], "ano": p[0], "ext": ext, "size": res.get("size") or 0,
                          "url": url}
    return sorted(best.values(), key=lambda x: x["periodo"])


def discover(cfg: dict) -> list[dict]:
    """Lista os recursos de dados e grava o índice em config/sp156_resources.csv."""
    rows = listar(cfg)
    with INDEX.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["periodo", "ano", "ext", "size", "url"])
        w.writeheader()
        w.writerows(rows)
    return rows


def _download(row: dict) -> dict:
    dst = RAW / f"{row['periodo']}.{row['ext']}"
    size = int(row["size"])
    if dst.exists() and (size == 0 or dst.stat().st_size == size):
        return {**row, "status": "cache", "file": dst.name}
    tmp = dst.with_suffix(dst.suffix + ".part")
    for tentativa in range(5):
        try:
            with requests.get(row["url"], headers=UA, stream=True, timeout=(30, 120)) as r:
                r.raise_for_status()
                with tmp.open("wb") as fh:
                    for chunk in r.iter_content(1 << 20):
                        fh.write(chunk)
            break
        except requests.RequestException as e:
            tmp.unlink(missing_ok=True)
            if tentativa == 4:
                return {**row, "status": f"erro: {type(e).__name__}", "file": dst.name}
            time.sleep(5 * 2 ** tentativa)
    if size and tmp.stat().st_size != size:
        tmp.unlink()
        return {**row, "status": "tamanho_divergente", "file": dst.name}
    tmp.rename(dst)
    return {**row, "status": "baixado", "file": dst.name}


def download(cfg: dict) -> list[dict]:
    RAW.mkdir(parents=True, exist_ok=True)
    rows = discover(cfg)
    with ThreadPoolExecutor(cfg["sp156"]["workers"]) as ex:
        out = list(ex.map(_download, rows))
    (RAW / "_manifest.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    return out
