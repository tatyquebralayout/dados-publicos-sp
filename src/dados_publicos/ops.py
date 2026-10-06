"""Fase 6: frescor das fontes, retenção do raw e estado da última execução."""
import json
import shutil
from datetime import date, datetime, timezone

import duckdb
from . import sp156
from .config import DATA

STATE = DATA / "_state.json"
MAX_ATRASO_DIAS = 150  # um trimestre + folga de publicação


def _fim_periodo(p: str) -> date:
    """Último dia do período (trimestre `T` ou semestre `S`)."""
    ano, kind, n = int(p[:4]), p[4], int(p[5])
    m = n * (3 if kind == "T" else 6)  # mês final
    prox = date(ano + (m == 12), m % 12 + 1, 1)
    return date.fromordinal(prox.toordinal() - 1)


def freshness(cfg: dict) -> dict:
    """Compara o CKAN com o que temos localmente. Devolve avisos; vazio = tudo em dia."""
    avisos = []
    modified = sp156.get_json(cfg["sp156"]["ckan_package"])["result"]["metadata_modified"]
    remoto = sp156.discover(cfg)
    novos, republicados = [], []
    for row in remoto:
        f = sp156.RAW / f"{row['periodo']}.{row['ext']}"
        if not f.exists():
            novos.append(row["periodo"])
        elif int(row["size"]) and f.stat().st_size != int(row["size"]):
            republicados.append(row["periodo"])
    if novos:
        avisos.append(f"períodos novos na fonte: {novos}")
    if republicados:
        avisos.append(f"arquivos republicados (tamanho mudou): {republicados}")
    silver = DATA / "silver" / "sp156"
    ultimo = None
    if silver.exists():
        ultimo = duckdb.sql(
            f"SELECT max(periodo) FROM read_parquet('{silver}/**/*.parquet', hive_partitioning=true)"
        ).fetchone()[0]
        atraso = (date.today() - _fim_periodo(ultimo)).days
        if atraso > MAX_ATRASO_DIAS:
            avisos.append(f"último período local {ultimo} terminou há {atraso} dias (> {MAX_ATRASO_DIAS})")
    # camada de exemplo (GeoSampa/SAC) — registra defasagem da carga
    sac = DATA / "silver" / "sac_todas"
    carga = None
    if sac.exists():
        carga = duckdb.sql(
            f"SELECT max(dt_carga) FROM read_parquet('{sac}/**/*.parquet', hive_partitioning=true)"
        ).fetchone()[0]
        if carga:
            carga = date.fromisoformat(str(carga)[:10])
            dias = (datetime.now(timezone.utc).date() - carga).days
            if dias > 365:
                avisos.append(f"camadas sac_* (GeoSampa) com dt_carga {carga}: {dias} dias sem atualização na fonte")
    estado = {"verificado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "ckan_metadata_modified": modified, "ultimo_periodo_local": ultimo,
              "sac_dt_carga": str(carga) if carga else None, "avisos": avisos}
    STATE.write_text(json.dumps(estado, indent=2, ensure_ascii=False))
    return estado


def prune(keep: int, apply: bool) -> list[str]:
    """Mantém só as `keep` execuções mais recentes de raw por camada GeoSampa. Dry-run por padrão."""
    out = []
    for layer in sorted((DATA / "raw").iterdir()):
        runs = sorted(p for p in layer.iterdir() if p.is_dir())
        for old in runs[:-keep] if len(runs) > keep else []:
            out.append(str(old.relative_to(DATA)))
            if apply:
                shutil.rmtree(old)
    return out
