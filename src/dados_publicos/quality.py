"""Regras de qualidade sobre a SILVER. Falha => pipeline para."""
import polars as pl

from .config import DATA, Layer

# Município de SP (bbox WGS84, margem pequena) – ver extent do ISO 19139
BBOX = (-46.82625, -24.00813, -46.3651, -23.35658)


def check(layer: Layer) -> list[str]:
    df = pl.read_parquet(DATA / "silver" / layer.name / "data.parquet")
    erros = []
    if df.height == 0:
        erros.append("tabela vazia")
    if df[layer.key].is_duplicated().any():
        erros.append(f"chave {layer.key} duplicada")
    if df[layer.key].null_count():
        erros.append(f"chave {layer.key} nula")
    fora = df.filter(~pl.col("lon").is_between(BBOX[0], BBOX[2])
                     | ~pl.col("lat").is_between(BBOX[1], BBOX[3]))
    if fora.height:
        erros.append(f"{fora.height} pontos fora do município")
    inv = df.filter(pl.col("prazo_dias") < 0)
    if inv.height:
        erros.append(f"{inv.height} registros com parecer antes da abertura")
    if df["dt_abertura"].null_count():
        erros.append("dt_abertura nula/ilegível")
    return erros
