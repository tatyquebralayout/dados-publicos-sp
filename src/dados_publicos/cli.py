import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor

import duckdb
import requests

from . import catalog, config, geo, ingest, ops, quality, sp156, sp156_etl, transform
from .config import DATA

STAGES = ["update", "freshness", "prune", "geo", "sp156-download", "sp156-bronze", "sp156-silver", "sp156-quality", "sp156-gold", "sp156", "catalog", "ingest", "bronze", "silver", "gold", "check", "unify", "all"]


def run_layer(cfg, L, stage) -> dict:
    """Processa uma camada; nunca levanta — devolve status para o resumo final."""
    res = {"layer": L.name, "status": "ok", "rows": None, "detail": ""}
    try:
        if stage in ("ingest", "all"):
            m = ingest.ingest(cfg, L)
            res["rows"] = m["rows"]
            if m["rows"] == 0:
                res["status"] = "vazia"
                return res
        if stage in ("bronze", "all"):
            transform.bronze(L)
        if stage in ("silver", "all"):
            transform.silver(L, cfg["timezone"])
        if stage in ("check", "all"):
            erros = quality.check(L)
            if erros:
                res.update(status="qualidade", detail="; ".join(erros))
                return res
        if stage in ("gold", "all"):
            transform.gold(L)
    except Exception as e:  # uma camada ruim não derruba o lote
        res.update(status="erro", detail=f"{type(e).__name__}: {e}")
    return res


def unify(family: str, layers) -> int:
    """Silver unificada da família: une todas as silvers com a coluna `camada`."""
    parts = [L.name for L in layers.values()
             if L.family == family and (DATA / "silver" / L.name / "data.parquet").exists()]
    if not parts:
        return 0
    sel = " UNION ALL BY NAME ".join(
        f"SELECT '{n}' AS camada, * EXCLUDE (_raw_run) "
        f"FROM read_parquet('{DATA}/silver/{n}/data.parquet')" for n in parts)
    out = DATA / "silver" / f"{family}_todas"
    out.mkdir(parents=True, exist_ok=True)
    duckdb.sql(f"COPY (SELECT * FROM ({sel})) TO '{out}' "
               "(FORMAT parquet, COMPRESSION zstd, PARTITION_BY (ano_mes), OVERWRITE_OR_IGNORE)")
    return duckdb.sql(f"SELECT count(*) FROM read_parquet('{out}/**/*.parquet')").fetchone()[0]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="dados-publicos")
    ap.add_argument("stage", choices=STAGES)
    ap.add_argument("layer", nargs="?", help="camada ou família (padrão: todas)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--force", action="store_true", help="reprocessa a bronze mesmo se atualizada")
    ap.add_argument("--keep", type=int, default=2, help="prune: execuções de raw a manter por camada")
    ap.add_argument("--apply", action="store_true", help="prune: apaga de verdade (padrão: dry-run)")
    a = ap.parse_args(argv)
    cfg, layers = config.load()
    if a.stage == "freshness":
        st = ops.freshness(cfg)
        print(json.dumps(st, indent=2, ensure_ascii=False))
        return 2 if st["avisos"] else 0
    if a.stage == "prune":
        lst = ops.prune(a.keep, a.apply)
        print(("removidos" if a.apply else "removeria (dry-run)"), len(lst), "diretórios de raw")
        print(*lst[:10], sep="\n")
        return 0
    if a.stage == "update":  # rotina agendável: baixa só o novo e refaz as camadas derivadas
        try:
            sp156.download(cfg)
        except requests.RequestException as e:
            print(f"AVISO: fonte indisponível ({type(e).__name__}); seguindo com o raw local")
        for p in sorted({x.stem for x in sp156_etl.RAW.glob("*.csv")} | {x.stem for x in sp156_etl.RAW.glob("*.xlsx")}):
            r = sp156_etl.bronze_period(p, a.force)
            if r["status"] != "atualizado":
                print(r, flush=True)
        print(sp156_etl.silver())
        qr = sp156_etl.quality()
        print("qualidade:", {k: v for k, v in qr.items() if k != "erros"}, qr["erros"] or "OK")
        if qr["erros"]:
            return 1
        print(*sp156_etl.gold(), sep="\n")
        print({k: v for k, v in geo.build().items() if k != "qualidade"})
        try:
            for av in ops.freshness(cfg)["avisos"]:
                print("AVISO:", av)
        except requests.RequestException as e:
            print(f"AVISO: frescor não verificado ({type(e).__name__})")
        return 0
    if a.stage == "geo":
        r = geo.build()
        print({k: v for k, v in r.items() if k != "qualidade"})
        print(r["qualidade"])
        return 0
    if a.stage == "sp156-download":
        res = sp156.download(cfg)
        from collections import Counter
        print(Counter(r["status"] for r in res), "arquivos:", len(res))
        return 0
    if a.stage in ("sp156-bronze", "sp156"):
        for p in sorted({x.stem for x in sp156_etl.RAW.glob("*.csv")} | {x.stem for x in sp156_etl.RAW.glob("*.xlsx")}):
            print(sp156_etl.bronze_period(p, a.force), flush=True)
    if a.stage in ("sp156-silver", "sp156"):
        print(sp156_etl.silver())
    if a.stage in ("sp156-quality", "sp156"):
        r = sp156_etl.quality()
        print("qualidade:", {k: v for k, v in r.items() if k != "erros"})
        for e in r["erros"]:
            print("  !", e)
        if r["erros"] and a.stage == "sp156":
            return 1
    if a.stage in ("sp156-gold", "sp156"):
        print(*sp156_etl.gold(), sep="\n")
    if a.stage.startswith("sp156"):
        return 0
    if a.stage == "catalog":
        print(catalog.build(cfg), "camadas catalogadas em", catalog.CATALOG)
        return 0
    fams = {L.family for L in layers.values() if L.family}
    sel = [L for L in layers.values() if a.layer in (None, L.name, L.family)]
    if not sel:
        sys.exit(f"nada selecionado para '{a.layer}'")
    if a.stage != "unify":
        with ThreadPoolExecutor(a.workers) as ex:
            results = list(ex.map(lambda L: run_layer(cfg, L, a.stage), sel))
        resumo = {}
        for r in results:
            resumo.setdefault(r["status"], []).append(r)
        print({k: len(v) for k, v in resumo.items()},
              "| linhas:", sum(r["rows"] or 0 for r in results))
        for r in results:
            if r["status"] in ("erro", "qualidade"):
                print(f"  ! {r['layer']}: {r['status']} — {r['detail']}")
    if a.stage in ("unify", "all"):
        for f in sorted(fams if a.layer in (None, *fams) else {L.family for L in sel if L.family}):
            print(f"unify {f}_todas:", unify(f, layers), "linhas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
