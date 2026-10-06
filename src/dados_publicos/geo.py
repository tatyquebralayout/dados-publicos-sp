"""Fase 5: cruza coordenadas do SP156 com os distritos (point-in-polygon) e gera grade de calor."""
import glob
import shutil
import tempfile

import duckdb

from .config import DATA
from .sp156_etl import SILVER

GEO = DATA / "silver" / "sp156_geo"
GOLD = DATA / "gold" / "sp156"
CELL = 500  # metros (UTM 23S)


def _con() -> duckdb.DuckDBPyConnection:
    c = duckdb.connect()
    c.execute("INSTALL spatial; LOAD spatial")
    c.execute("SET memory_limit='3GB'; SET preserve_insertion_order=false")
    c.execute(f"SET temp_directory='{tempfile.gettempdir()}/duck_tmp'")
    return c


def district_polygons(con) -> str:
    page = sorted(glob.glob(str(DATA / "raw" / "distrito_municipal" / "*" / "page_*.json")))[-1]
    con.execute(f"""CREATE TEMP TABLE dist AS
        SELECT nm_distrito_municipal AS nm_distrito, sg_distrito_municipal AS sg_distrito, geom
        FROM ST_Read('{page}')""")
    return page


def write_district_codes() -> int:
    """config/distritos.csv: código oficial (cd_distrito_municipal) -> nome. A fonte SP156 passou a
    publicar o código em vez do nome em parte das linhas (2025T2+); o código coincide 100% com este campo."""
    con = _con()
    page = sorted(glob.glob(str(DATA / "raw" / "distrito_municipal" / "*" / "page_*.json")))[-1]
    out = DATA.parent / "config" / "distritos.csv"
    con.execute(f"""COPY (SELECT cd_distrito_municipal::INT AS cd, nm_distrito_municipal AS nome
        FROM ST_Read('{page}') ORDER BY 1) TO '{out}' (FORMAT csv, HEADER)""")
    return con.execute(f"SELECT count(*) FROM read_csv('{out}')").fetchone()[0]


def build() -> dict:
    """Distrito geográfico por coordenada distinta + grade 500 m por ano."""
    shutil.rmtree(GEO, ignore_errors=True)
    GEO.mkdir(parents=True)
    GOLD.mkdir(parents=True, exist_ok=True)
    con = _con()
    district_polygons(con)
    g = f"read_parquet('{SILVER}/**/*.parquet', hive_partitioning=true)"
    # 1) pontos distintos (WGS84) -> UTM 23S -> distrito
    con.execute(f"""CREATE TEMP TABLE pts AS
        SELECT lat, lon, ST_Transform(ST_Point(lon, lat), 'EPSG:4326', 'EPSG:31983', always_xy := true) AS g
        FROM (SELECT DISTINCT lat, lon FROM {g} WHERE lat IS NOT NULL)""")
    con.execute(f"""COPY (
        SELECT p.lat, p.lon, d.nm_distrito AS distrito_geo, d.sg_distrito AS sg_distrito_geo,
               floor(ST_X(p.g) / {CELL})::INT AS cx, floor(ST_Y(p.g) / {CELL})::INT AS cy
        FROM pts p LEFT JOIN dist d ON ST_Within(p.g, d.geom)
    ) TO '{GEO}/coord_distrito.parquet' (FORMAT parquet, COMPRESSION zstd)""")
    cd = f"read_parquet('{GEO}/coord_distrito.parquet')"
    # 2) grade de calor: solicitações por célula 500 m, ano e tema
    con.execute(f"""COPY (
        SELECT s.ano, s.tema, c.cx, c.cy,
               (c.cx * {CELL} + {CELL} / 2) AS x_utm, (c.cy * {CELL} + {CELL} / 2) AS y_utm,
               count(*) AS solicitacoes
        FROM {g} s JOIN {cd} c USING (lat, lon)
        GROUP BY ALL
    ) TO '{GOLD}/grade_{CELL}m_ano_tema.parquet' (FORMAT parquet, COMPRESSION zstd)""")
    # 3) distrito declarado x geográfico (qualidade) + preenchimento
    con.execute(f"""COPY (
        SELECT s.ano,
               count(*) AS com_coordenada,
               count(c.distrito_geo) AS dentro_de_algum_distrito,
               count(*) FILTER (WHERE s.distrito IS NOT NULL) AS com_distrito_declarado,
               count(*) FILTER (WHERE s.distrito IS NOT NULL AND s.distrito = c.distrito_geo) AS coincidem,
               count(*) FILTER (WHERE s.distrito IS NULL AND c.distrito_geo IS NOT NULL) AS distrito_recuperado
        FROM {g} s JOIN {cd} c USING (lat, lon)
        GROUP BY ALL ORDER BY ALL
    ) TO '{GOLD}/qualidade_distrito.parquet' (FORMAT parquet)""")
    # 4) distrito final por ano (declarado, senão geográfico)
    con.execute(f"""COPY (
        SELECT s.ano, coalesce(s.distrito, c.distrito_geo) AS distrito, count(*) AS solicitacoes,
               count(*) FILTER (WHERE s.distrito IS NULL AND c.distrito_geo IS NOT NULL) AS recuperadas_por_geo
        FROM {g} s LEFT JOIN {cd} c USING (lat, lon)
        WHERE coalesce(s.distrito, c.distrito_geo) IS NOT NULL
        GROUP BY ALL ORDER BY ALL
    ) TO '{GOLD}/distrito_final_ano.parquet' (FORMAT parquet, COMPRESSION zstd)""")
    q = con.execute(f"SELECT * FROM read_parquet('{GOLD}/qualidade_distrito.parquet')").pl()
    return {"pontos_distintos": con.execute(f"SELECT count(*) FROM {cd}").fetchone()[0],
            "pontos_fora_dos_distritos": con.execute(
                f"SELECT count(*) FROM {cd} WHERE distrito_geo IS NULL").fetchone()[0],
            "qualidade": q}
