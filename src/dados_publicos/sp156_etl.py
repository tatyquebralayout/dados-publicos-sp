"""SP156 completo: CSVs heterogêneos -> bronze (esquema canônico, texto) -> silver tipada (DuckDB)."""
import shutil
import tempfile
import unicodedata
from pathlib import Path

import duckdb
import polars as pl

from .config import DATA, ROOT

RAW, BRONZE, SILVER = DATA / "raw" / "sp156", DATA / "bronze" / "sp156", DATA / "silver" / "sp156"

# nome normalizado (minúsculo, sem acento) -> coluna canônica
ALIASES = {
    "data de abertura": "dt_abertura",
    "data de finalizacao": "dt_finalizacao", "data do parecer": "dt_finalizacao",
    "canal": "canal", "meio de comunicacao": "canal",
    "tema": "tema", "assunto": "assunto", "servico": "servico",
    "status": "status", "status da solicitacao": "status",
    "orgao": "orgao", "logradouro": "logradouro",
    "bairro": "bairro", "numero": "numero", "cep": "cep",
    "subprefeitura": "subprefeitura", "prefeitura operacional": "subprefeitura",
    "distrito": "distrito", "latitude": "lat", "longitude": "lon",
}
CANON = ["dt_abertura", "dt_finalizacao", "canal", "tema", "assunto", "servico", "status", "orgao",
         "logradouro", "bairro", "numero", "cep", "subprefeitura", "distrito", "lat", "lon"]
# satisfação (2015-2019) e demais colunas antigas ficam de fora: cobertura parcial e esquema instável

# 2021T1 mistura dois layouts no mesmo arquivo (15 colunas, ordem diferente a partir da linha 275.427).
# Mapeamento INFERIDO pelo conteúdo das colunas: canônica -> posição (0-14) no layout alternativo.
ALT_LAYOUT = {"2021T1": {"servico": 0, "orgao": 1, "dt_abertura": 2, "tema": 5, "dt_finalizacao": 6,
                         "assunto": 7, "canal": 8, "status": 9, "logradouro": 10,
                         "subprefeitura": 11, "distrito": 12, "numero": 13, "cep": 14}}

# Município de SP (bbox WGS84)
BBOX = (-46.82625, -24.00813, -46.3651, -23.35658)


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.strip().lstrip("﻿")).encode("ascii", "ignore").decode()
    return " ".join(s.lower().split())


def _to_utf8(src: Path, dst: Path) -> str:
    """Transcodifica em streaming (cp1252 ou utf-8[-bom]) e devolve o separador."""
    with src.open("rb") as f:
        head = f.read(200_000)
    try:
        head.decode("utf-8")
        enc = "utf-8-sig"
    except UnicodeDecodeError:
        enc = "cp1252"
    first = head.split(b"\n")[0].decode(enc, errors="replace")
    sep = ";" if first.count(";") > first.count(",") else ","
    with src.open("r", encoding=enc, errors="replace", newline="") as r, \
            dst.open("w", encoding="utf-8", newline="") as w:
        while chunk := r.read(1 << 22):
            w.write(chunk)
    return sep


def bronze_period(periodo: str, force: bool = False) -> dict:
    src = RAW / f"{periodo}.csv"
    xlsx = RAW / f"{periodo}.xlsx"
    if not src.exists() and not xlsx.exists():
        return {"periodo": periodo, "status": "sem_arquivo"}
    out_f = BRONZE / f"periodo={periodo}" / "part.parquet"
    fonte = src if src.exists() else xlsx
    if not force and out_f.exists() and out_f.stat().st_mtime > fonte.stat().st_mtime:
        return {"periodo": periodo, "status": "atualizado"}  # incremental: bronze mais nova que o raw
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "u.csv"
        if src.exists():
            sep = _to_utf8(src, tmp)
        else:  # períodos publicados só em XLSX: aba 1 = solicitações (aba 2 = satisfação)
            pl.read_excel(xlsx, sheet_id=1, engine="calamine", infer_schema_length=0) \
                .write_csv(tmp, separator=";")
            sep = ";"
        con = duckdb.connect()
        con.execute("SET preserve_insertion_order=false")
        rel = con.execute(
            "SELECT * FROM read_csv(?, delim=?, quote='\"', escape='\"', header=true, all_varchar=true, "
            "null_padding=true, strict_mode=false, ignore_errors=true, parallel=false, sample_size=-1)",
            [str(tmp), sep])
        cols = [d[0] for d in rel.description]
        ren = {}
        for c in cols:
            k = ALIASES.get(_norm(c))
            if k and k not in ren.values():
                ren[c] = k
        faltam = [c for c in CANON if c not in ren.values()]
        inv = {v: k for k, v in ren.items()}
        sel_parts = {c: (f'nullif(trim("{inv[c]}"), \'\')' if c in inv else "NULL::VARCHAR")
                     for c in CANON}
        alt = ALT_LAYOUT.get(periodo)
        if alt and len(cols) == 15:
            p = [f'nullif(trim("{c}"), \'\')' for c in cols]
            is_alt = f"NOT regexp_matches(coalesce(trim(\"{cols[0]}\"), ''), '^[0-9]{{2}}/[0-9]{{2}}/[0-9]{{4}}')"
            for c in CANON:
                a = p[alt[c]] if c in alt else "NULL::VARCHAR"
                sel_parts[c] = f"CASE WHEN {is_alt} THEN {a} ELSE {sel_parts[c]} END"
        sel = ", ".join(f"{sel_parts[c]} AS {c}" for c in CANON)
        any_ = " OR ".join(f"{c} IS NOT NULL" for c in CANON)  # descarta linhas totalmente vazias
        out = BRONZE / f"periodo={periodo}"
        out.mkdir(parents=True, exist_ok=True)
        con.execute(
            f"COPY (SELECT * FROM (SELECT {sel}, '{periodo}' AS periodo FROM read_csv(?, delim=?, "
            f"quote='\"', escape='\"', header=true, all_varchar=true, null_padding=true, strict_mode=false, "
            f"ignore_errors=true, parallel=false, sample_size=-1)) WHERE {any_}) "
            f"TO '{out}/part.parquet' (FORMAT parquet, COMPRESSION zstd)", [str(tmp), sep])
        n = con.execute(f"SELECT count(*) FROM read_parquet('{out}/part.parquet')").fetchone()[0]
    return {"periodo": periodo, "status": "ok", "rows": n, "faltando": faltam}


def silver() -> dict:
    shutil.rmtree(SILVER, ignore_errors=True)  # idempotência: sem arquivos órfãos de execuções antigas
    SILVER.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("SET memory_limit='3GB'; SET preserve_insertion_order=false;")
    con.execute(f"SET temp_directory='{tempfile.gettempdir()}/duck_tmp'")
    # código -> nome do distrito (a fonte passou a trazer o código em 2025T2+; ver geo.write_district_codes)
    con.execute(f"CREATE TEMP TABLE dcod AS SELECT cd::VARCHAR AS cd, nome "
                f"FROM read_csv('{ROOT / 'config' / 'distritos.csv'}')")
    ts = lambda c: ("COALESCE(" + ", ".join(
        f"try_strptime(trim({c}), '{f}')" for f in
        ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d")) + ")")
    num = lambda c: f"try_cast(replace(nullif(trim({c}), ''), ',', '.') AS DOUBLE)"
    sql = f"""
    COPY (
      WITH b AS (SELECT * FROM read_parquet('{BRONZE}/*/part.parquet')),
      t AS (SELECT *, {ts('dt_abertura')} AS _ab, {ts('dt_finalizacao')} AS _fim,
                   {num('lat')} AS _lat, {num('lon')} AS _lon FROM b)
      SELECT periodo,
             _ab AS dt_abertura, _fim AS dt_finalizacao,
             year(_ab) AS ano, month(_ab) AS mes,
             CASE WHEN _fim::DATE >= _ab::DATE THEN date_diff('day', _ab::DATE, _fim::DATE) END AS prazo_dias,
             upper(trim(canal)) AS canal, trim(tema) AS tema, trim(assunto) AS assunto,
             trim(servico) AS servico, upper(trim(status)) AS status, trim(orgao) AS orgao,
             trim(logradouro) AS logradouro, trim(bairro) AS bairro,
             try_cast(numero AS INTEGER) AS numero,
             CASE WHEN regexp_matches(trim(cep), '^[0-9]+$') THEN lpad(trim(cep), 8, '0') END AS cep,
             upper(trim(subprefeitura)) AS subprefeitura, coalesce(d.nome, upper(trim(distrito))) AS distrito,
             (year(_ab) >= 2020) AS prazo_confiavel,  -- antes de 2020 'Data do Parecer' não é a data de finalização
             CASE WHEN _lat BETWEEN {BBOX[1]} AND {BBOX[3]} AND _lon BETWEEN {BBOX[0]} AND {BBOX[2]}
                  THEN _lat END AS lat,
             CASE WHEN _lat BETWEEN {BBOX[1]} AND {BBOX[3]} AND _lon BETWEEN {BBOX[0]} AND {BBOX[2]}
                  THEN _lon END AS lon
      FROM t LEFT JOIN dcod d ON d.cd = trim(t.distrito)
      WHERE _ab IS NOT NULL
        -- arquivos trimestrais repetem meses vizinhos (2017-06 em 2017T2/T3; 2018-10 em 2018T3/T4)
        AND (periodo NOT LIKE '%T_' OR periodo = year(_ab)::VARCHAR || 'T' || ((month(_ab) + 2) // 3)::VARCHAR)
    ) TO '{SILVER}' (FORMAT parquet, COMPRESSION zstd, PARTITION_BY (ano, mes),
                     OVERWRITE_OR_IGNORE, ROW_GROUP_SIZE 500000)"""
    con.execute(sql)
    g = f"read_parquet('{SILVER}/**/*.parquet', hive_partitioning=true)"
    res = {
        "linhas_bronze": con.execute(f"SELECT count(*) FROM read_parquet('{BRONZE}/*/part.parquet')").fetchone()[0],
        "linhas_silver": con.execute(f"SELECT count(*) FROM {g}").fetchone()[0],
    }
    res["descartadas_sobreposicao_ou_data_invalida"] = res["linhas_bronze"] - res["linhas_silver"]
    return res


GOLD = DATA / "gold" / "sp156"
_G = f"read_parquet('{SILVER}/**/*.parquet', hive_partitioning=true)"


def quality() -> dict:
    """Relatório de qualidade por período + regras que bloqueiam o pipeline."""
    GOLD.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("SET memory_limit='3GB'")
    con.execute(f"""
      COPY (SELECT periodo, count(*) AS linhas,
        min(dt_abertura)::DATE AS dt_min, max(dt_abertura)::DATE AS dt_max,
        round(100.0*count(lat)/count(*), 2) AS pct_com_coordenada,
        round(100.0*count(distrito)/count(*), 2) AS pct_com_distrito,
        round(100.0*count(dt_finalizacao)/count(*), 2) AS pct_com_finalizacao,
        count(*) FILTER (WHERE dt_finalizacao::DATE < dt_abertura::DATE) AS finalizacao_antes_abertura,
        count(*) FILTER (WHERE tema IS NULL) AS sem_tema
      FROM {_G} GROUP BY periodo ORDER BY periodo) TO '{GOLD}/qualidade_periodo.parquet'
      (FORMAT parquet)""")
    q = con.execute(f"SELECT * FROM read_parquet('{GOLD}/qualidade_periodo.parquet')").pl()
    erros = []
    esperado = {p.name.split("=")[1]: None for p in BRONZE.iterdir()}
    if set(q["periodo"]) != set(esperado):
        erros.append(f"períodos ausentes na silver: {sorted(set(esperado) - set(q['periodo']))}")
    for r in q.iter_rows(named=True):
        ano, tri = int(r["periodo"][:4]), r["periodo"][4:]
        lo = f"{ano}-{(int(tri[1]) - 1) * 3 + 1:02d}" if tri[0] == "T" else None
        if lo and str(r["dt_min"])[:7] < lo:
            erros.append(f"{r['periodo']}: abertura {r['dt_min']} antes do trimestre")
        if r["linhas"] < 100_000:
            erros.append(f"{r['periodo']}: só {r['linhas']} linhas")
        if r["finalizacao_antes_abertura"] > 0.01 * r["linhas"]:
            erros.append(f"{r['periodo']}: >1% com finalização antes da abertura")
    return {"periodos": q.height, "linhas": int(q["linhas"].sum()), "erros": erros}


def gold() -> list[str]:
    GOLD.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("SET memory_limit='3GB'")
    out = []
    jobs = {
        "mensal_tema_canal": f"""SELECT ano, mes, tema, canal, status, count(*) AS solicitacoes,
            round(median(prazo_dias), 2) AS prazo_mediano_dias
            FROM {_G} GROUP BY ALL ORDER BY ALL""",
        "distrito_ano": f"""SELECT ano, subprefeitura, distrito, tema, count(*) AS solicitacoes,
            count(lat) AS com_coordenada, round(median(prazo_dias), 2) AS prazo_mediano_dias
            FROM {_G} WHERE distrito IS NOT NULL GROUP BY ALL ORDER BY ALL""",
        "orgao_ano": f"""SELECT ano, orgao, count(*) AS solicitacoes,
            round(avg((status = 'FINALIZADA')::INT) * 100, 2) AS pct_finalizadas,
            round(median(prazo_dias), 2) AS prazo_mediano_dias
            FROM {_G} GROUP BY ALL ORDER BY ALL""",
    }
    for name, sql in jobs.items():
        dst = GOLD / f"{name}.parquet"
        con.execute(f"COPY ({sql}) TO '{dst}' (FORMAT parquet, COMPRESSION zstd)")
        out.append(f"{name}: {con.execute(f'SELECT count(*) FROM read_parquet(?)', [str(dst)]).fetchone()[0]} linhas")
    return out
