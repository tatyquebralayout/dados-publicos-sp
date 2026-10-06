"""BRONZE -> SILVER -> GOLD. Polars para limpeza; DuckDB para agregações."""
import json
import unicodedata
from pathlib import Path

import duckdb
import polars as pl
from pyproj import Transformer

from .config import DATA, Layer


def latest_run(layer: Layer) -> Path:
    runs = sorted(p for p in (DATA / "raw" / layer.name).iterdir() if p.is_dir())
    if not runs:
        raise FileNotFoundError(f"sem raw para {layer.name}; rode `ingest`")
    return runs[-1]


def bronze(layer: Layer) -> Path:
    """Achata GeoJSON em tabela tipada, preservando tudo + lineage. Parquet zstd."""
    run = latest_run(layer)
    rows = []
    for page in sorted(run.glob("page_*.json")):
        for f in json.loads(page.read_text(encoding="utf-8"))["features"]:
            x, y = (f["geometry"] or {"coordinates": [None, None]})["coordinates"][:2]
            rows.append({**f["properties"], "x": x, "y": y})
    df = pl.DataFrame(rows, infer_schema_length=None).with_columns(
        pl.lit(run.name).alias("_raw_run"))
    out = DATA / "bronze" / layer.name / "part-0.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(out, compression="zstd")
    return out


def _norm(s: str | None) -> str | None:
    if s is None:
        return None
    s = " ".join(s.split())
    return s or None


def silver(layer: Layer, tz: str) -> Path:
    df = pl.read_parquet(DATA / "bronze" / layer.name / "part-0.parquet")
    for c in layer.date_cols:  # GeoJSON vem em UTC ("Z") -> hora local de São Paulo
        df = df.with_columns(
            pl.col(c).str.to_datetime(time_zone="UTC", strict=False)
            .dt.convert_time_zone(tz).dt.replace_time_zone(None))
    for c in layer.text_cols:
        df = df.with_columns(pl.col(c).map_elements(_norm, return_dtype=pl.String))
    t = Transformer.from_crs(layer.srid, 4326, always_xy=True)
    xs, ys = df["x"].to_list(), df["y"].to_list()
    pts = [t.transform(a, b) if a is not None else (None, None) for a, b in zip(xs, ys)]
    df = df.with_columns(
        pl.Series("lon", [p[0] for p in pts]), pl.Series("lat", [p[1] for p in pts]),
        ((pl.col("dt_parecer") - pl.col("dt_abertura")).dt.total_seconds() / 86400)
        .alias("prazo_dias"),
        pl.col("dt_abertura").dt.strftime("%Y-%m").alias("ano_mes"),
    ).unique(subset=[layer.key], keep="last").sort(layer.key)
    out = DATA / "silver" / layer.name
    out.mkdir(parents=True, exist_ok=True)
    df.write_parquet(out / "data.parquet", compression="zstd")
    return out / "data.parquet"


def gold(layer: Layer) -> Path:
    src = DATA / "silver" / layer.name / "data.parquet"
    out = DATA / "gold" / layer.name
    out.mkdir(parents=True, exist_ok=True)
    dst = out / "resumo_mensal.parquet"
    duckdb.sql(f"""
        COPY (SELECT ano_mes, tx_situacao_solicitacao AS situacao, tx_canal_atendimento AS canal,
                     count(*) AS solicitacoes,
                     round(avg(prazo_dias), 2) AS prazo_medio_dias,
                     round(median(prazo_dias), 2) AS prazo_mediano_dias
              FROM read_parquet('{src}') GROUP BY ALL ORDER BY ALL)
        TO '{dst}' (FORMAT parquet, COMPRESSION zstd)""")
    return dst
