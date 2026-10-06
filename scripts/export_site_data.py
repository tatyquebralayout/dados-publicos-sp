"""Exporta métricas agregadas (JSON) da silver/gold para o site Docusaurus.

Só agregados saem daqui: nada de endereço, logradouro ou linha individual do SP156.
Células de mapa com menos de K_MIN solicitações são suprimidas.

Uso: .venv/bin/python scripts/export_site_data.py
"""
import csv
import datetime as dt
import decimal
import json
import tempfile
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "website" / "static" / "data"
K_MIN = 5
G = f"read_parquet('{DATA}/silver/sp156/**/*.parquet', hive_partitioning=true)"
GEO = f"read_parquet('{DATA}/silver/sp156_geo/coord_distrito.parquet')"
SAC = f"read_parquet('{DATA}/silver/sac_todas/**/*.parquet', hive_partitioning=true)"

STATUS = """CASE
  WHEN status = 'FINALIZADA' THEN 'Finalizada'
  WHEN status = 'CANCELADA' THEN 'Cancelada'
  WHEN status = 'RELACIONADA' THEN 'Relacionada'
  ELSE 'Em aberto' END"""  # ABERTO/ABERTA/EM ANDAMENTO/EM APROVAÇÃO/AGUARDANDO APROVAÇÃO


def _default(o):
    if isinstance(o, (dt.date, dt.datetime)):
        return o.isoformat()
    if isinstance(o, decimal.Decimal):
        return float(o)
    raise TypeError(type(o))


def dump(name: str, obj) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{name}.json"
    p.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":"), default=_default),
                 encoding="utf-8")
    print(f"{name}.json  {p.stat().st_size / 1024:.0f} KB")


def rows(con, sql: str) -> list[dict]:
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def main() -> None:
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial")
    con.execute("SET memory_limit='3GB'; SET preserve_insertion_order=false")
    con.execute(f"SET temp_directory='{tempfile.gettempdir()}/duck_tmp'")

    # ---- visão geral -------------------------------------------------------------------------
    ov = rows(con, f"""SELECT count(*) AS total, count(DISTINCT periodo) AS periodos,
        min(dt_abertura)::DATE AS primeira, max(dt_abertura)::DATE AS ultima,
        round(100.0 * count(lat) / count(*), 1) AS pct_coordenada,
        round(100.0 * count(*) FILTER (WHERE status = 'FINALIZADA') / count(*), 1) AS pct_finalizada,
        median(prazo_dias) FILTER (WHERE prazo_confiavel) AS prazo_mediano_dias, count(DISTINCT servico) AS servicos,
        count(DISTINCT orgao) AS orgaos FROM {G}""")[0]
    ov["pct_distrito_final"] = con.execute(f"""SELECT round(100.0 * count(*) FILTER (
        WHERE s.distrito IS NOT NULL OR c.distrito_geo IS NOT NULL) / count(*), 1)
        FROM {G} s LEFT JOIN {GEO} c USING (lat, lon)""").fetchone()[0]
    sac = rows(con, f"SELECT count(*) AS linhas, count(DISTINCT camada) AS camadas FROM {SAC}")[0]
    ov["sac_linhas"], ov["sac_camadas"] = sac["linhas"], sac["camadas"]
    ov["gerado_em"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    state = DATA / "_state.json"
    if state.exists():
        ov["frescor"] = json.loads(state.read_text())
    dump("overview", ov)

    # ---- série temporal ------------------------------------------------------------------------
    dump("mensal", rows(con, f"""SELECT strftime(dt_abertura, '%Y-%m') AS ym, count(*) AS n
        FROM {G} GROUP BY 1 ORDER BY 1"""))
    dump("anual", rows(con, f"""SELECT ano, count(*) AS n,
        round(100.0 * count(lat) / count(*), 1) AS pct_coordenada,
        round(100.0 * count(*) FILTER (WHERE status = 'FINALIZADA') / count(*), 1) AS pct_finalizada,
        median(prazo_dias) FILTER (WHERE prazo_confiavel) AS prazo_mediano
        FROM {G} GROUP BY 1 ORDER BY 1"""))

    # ---- canal (como publicado: a nomenclatura muda em 2020 e o glossário não mapeia CRM etc.) ----
    dump("canal_ano", rows(con, f"""SELECT ano, coalesce(canal, 'SEM CANAL') AS canal, count(*) AS n
        FROM {G} GROUP BY 1, 2 ORDER BY 1, 3 DESC"""))

    # ---- situação ------------------------------------------------------------------------------
    dump("status_ano", rows(con, f"""SELECT ano, {STATUS} AS situacao, count(*) AS n
        FROM {G} GROUP BY 1, 2 ORDER BY 1, 2"""))

    # ---- temas, serviços, órgãos -------------------------------------------------------------
    dump("tema_ano", rows(con, f"""SELECT ano, tema, count(*) AS n FROM {G}
        WHERE tema IS NOT NULL GROUP BY 1, 2 ORDER BY 1, 3 DESC"""))
    dump("tema_desempenho", rows(con, f"""SELECT tema, count(*) AS n,
        round(100.0 * count(*) FILTER (WHERE status = 'FINALIZADA') / count(*), 1) AS pct_finalizada,
        median(prazo_dias) FILTER (WHERE prazo_confiavel) AS prazo_mediano,
        round(quantile_cont(prazo_dias, 0.9) FILTER (WHERE prazo_confiavel), 0) AS prazo_p90
        FROM {G} WHERE tema IS NOT NULL AND ano >= 2020 GROUP BY 1 ORDER BY 2 DESC"""))
    dump("servicos_top", rows(con, f"""SELECT servico, tema, count(*) AS n, median(prazo_dias) FILTER (WHERE prazo_confiavel) AS prazo_mediano,
        min(ano) AS desde, max(ano) AS ate
        FROM {G} WHERE servico IS NOT NULL GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 30"""))
    dump("orgaos_top", rows(con, f"""SELECT orgao, count(*) AS n,
        round(100.0 * count(*) FILTER (WHERE status = 'FINALIZADA') / count(*), 1) AS pct_finalizada,
        median(prazo_dias) FILTER (WHERE prazo_confiavel) AS prazo_mediano,
        round(quantile_cont(prazo_dias, 0.9) FILTER (WHERE prazo_confiavel), 0) AS prazo_p90
        FROM {G} WHERE orgao IS NOT NULL AND ano >= 2020 GROUP BY 1 ORDER BY 2 DESC LIMIT 25"""))

    # ---- prazo de atendimento (faixas, % por ano) ----------------------------------------------
    dump("prazo_faixas_ano", rows(con, f"""SELECT ano, CASE
          WHEN prazo_dias = 0 THEN '0 (mesmo dia)' WHEN prazo_dias = 1 THEN '1 dia'
          WHEN prazo_dias <= 3 THEN '2 a 3 dias' WHEN prazo_dias <= 7 THEN '4 a 7 dias'
          WHEN prazo_dias <= 15 THEN '8 a 15 dias' WHEN prazo_dias <= 30 THEN '16 a 30 dias'
          ELSE 'mais de 30 dias' END AS faixa, count(*) AS n
        FROM {G} WHERE prazo_dias IS NOT NULL AND prazo_confiavel GROUP BY 1, 2 ORDER BY 1, 2"""))

    # ---- território: distritos -----------------------------------------------------------------
    dist = rows(con, f"""SELECT coalesce(s.distrito, c.distrito_geo) AS distrito, s.ano, count(*) AS n
        FROM {G} s LEFT JOIN {GEO} c USING (lat, lon)
        WHERE coalesce(s.distrito, c.distrito_geo) IS NOT NULL GROUP BY 1, 2""")
    por_d: dict[str, dict] = {}
    for r in dist:
        d = por_d.setdefault(r["distrito"], {"distrito": r["distrito"], "total": 0, "anos": {}})
        d["total"] += r["n"]
        d["anos"][str(r["ano"])] = r["n"]
    dump("distritos", sorted(por_d.values(), key=lambda x: -x["total"]))

    page = sorted((DATA / "raw" / "distrito_municipal").glob("*/page_*.json"))[-1]
    feats = []
    for nm, gj in con.execute(f"""SELECT nm_distrito_municipal,
        ST_AsGeoJSON(ST_Transform(ST_Simplify(geom, 40), 'EPSG:31983', 'EPSG:4326', always_xy := true))
        FROM ST_Read('{page}')""").fetchall():
        geom = json.loads(gj)

        def rnd(c):
            return [round(c[0], 5), round(c[1], 5)] if isinstance(c[0], (int, float)) else [rnd(x) for x in c]

        geom["coordinates"] = rnd(geom["coordinates"])
        feats.append({"type": "Feature", "properties": {"nome": nm}, "geometry": geom})
    dump("distritos_geo", {"type": "FeatureCollection", "features": feats})

    # ---- grade de calor 500 m (todos + 6 maiores temas), com supressão k < K_MIN ------------------
    top_temas = [r[0] for r in con.execute(
        f"SELECT tema FROM {G} WHERE tema IS NOT NULL GROUP BY 1 ORDER BY count(*) DESC LIMIT 6").fetchall()]
    grade = f"read_parquet('{DATA}/gold/sp156/grade_500m_ano_tema.parquet')"
    cells = con.execute(f"""
        WITH base AS (
          SELECT cx, cy, x_utm, y_utm, CASE WHEN tema = ANY(?) THEN tema END AS tema, ano, solicitacoes
          FROM {grade}),
        agg AS (
          SELECT 'Todos os temas' AS tema, cx, cy, any_value(x_utm) x, any_value(y_utm) y, sum(solicitacoes) n
            FROM base GROUP BY cx, cy
          UNION ALL
          SELECT tema, cx, cy, any_value(x_utm), any_value(y_utm), sum(solicitacoes)
            FROM base WHERE tema IS NOT NULL GROUP BY tema, cx, cy)
        SELECT tema, round(ST_Y(p), 5) lat, round(ST_X(p), 5) lon, n FROM (
          SELECT tema, n, ST_Transform(ST_Point(x, y), 'EPSG:31983', 'EPSG:4326', always_xy := true) p
          FROM agg WHERE n >= {K_MIN})""", [top_temas]).fetchall()
    by_tema: dict[str, list] = {}
    for tema, lat, lon, n in cells:
        by_tema.setdefault(tema, []).append([lat, lon, int(n)])
    dump("grade", {"celula_m": 500, "k_min": K_MIN, "temas": ["Todos os temas"] + top_temas, "celulas": by_tema})

    # ---- qualidade dos dados ---------------------------------------------------------------------
    dump("qualidade_periodo", rows(con, f"""SELECT * FROM read_parquet('{DATA}/gold/sp156/qualidade_periodo.parquet')
        ORDER BY periodo"""))
    dump("qualidade_distrito", rows(con, f"""SELECT * FROM read_parquet('{DATA}/gold/sp156/qualidade_distrito.parquet')
        ORDER BY ano"""))

    # ---- GeoSampa: família sac_* ---------------------------------------------------------------
    titles = {}
    with (ROOT / "config" / "catalog.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            titles[r["name"]] = r["title"]
    camadas = rows(con, f"""SELECT camada AS nome, count(*) AS n, min(dt_abertura)::DATE AS de,
        max(dt_abertura)::DATE AS ate, max(dt_carga) AS dt_carga FROM {SAC} GROUP BY 1 ORDER BY 2 DESC""")
    for c in camadas:
        c["titulo"] = titles.get(c["nome"], c["nome"])
    dump("sac_camadas", camadas)

    # ---- camada original: reativação de abrigo/ponto extinto (45 registros; sem endereço) ----------
    R = f"read_parquet('{DATA}/silver/sac_reativacao_abrigo_ponto_extinto/data.parquet')"
    dump("reativacao", {
        "total": con.execute(f"SELECT count(*) FROM {R}").fetchone()[0],
        "por_mes": rows(con, f"SELECT ano_mes AS ym, count(*) AS n FROM {R} GROUP BY 1 ORDER BY 1"),
        "situacao": rows(con, f"SELECT tx_situacao_solicitacao AS situacao, count(*) AS n FROM {R} GROUP BY 1 ORDER BY 2 DESC"),
        "canal": rows(con, f"SELECT tx_canal_atendimento AS canal, count(*) AS n FROM {R} GROUP BY 1 ORDER BY 2 DESC"),
        "prazo_mediano_dias": con.execute(f"SELECT median(prazo_dias) FROM {R}").fetchone()[0],
        "pontos": [[round(a, 5), round(b, 5), ym, s] for a, b, ym, s in con.execute(
            f"SELECT lat, lon, ano_mes, tx_situacao_solicitacao FROM {R} ORDER BY ano_mes").fetchall()],
    })


if __name__ == "__main__":
    main()
