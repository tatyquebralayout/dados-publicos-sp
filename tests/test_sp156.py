from datetime import date

import polars as pl
import pytest

from dados_publicos import ops, sp156, sp156_etl


def _setup(tmp_path, monkeypatch):
    for mod in (sp156_etl,):
        monkeypatch.setattr(mod, "RAW", tmp_path / "raw")
        monkeypatch.setattr(mod, "BRONZE", tmp_path / "bronze")
        monkeypatch.setattr(mod, "SILVER", tmp_path / "silver")
    (tmp_path / "raw").mkdir()


def test_aliases_e_colunas_ausentes(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    # esquema antigo: separador ;, cp1252, canal/parecer, sem "bairro"
    csv = ("Data de abertura;Canal;Tema;Assunto;Serviço;Logradouro;Numero;CEP;Subprefeitura;Distrito;"
           "Latitude;Longitude;Data do Parecer;Status da solicitação;Órgão\r\n"
           "2015-01-01 08:00:00;CENTRAL TELEFÔNICA;Rua e bairro;Asfalto;Tapa-buraco;RUA A;10;01000000;"
           "SE;SE;-23.55;-46.63;2015-01-01 00:00:00;FINALIZADA;SMSUB\r\n"
           ";;;;;;;;;;;;;;\r\n")  # linha vazia deve ser descartada
    (tmp_path / "raw" / "2015T1.csv").write_bytes(csv.encode("cp1252"))
    r = sp156_etl.bronze_period("2015T1")
    assert r["rows"] == 1 and r["faltando"] == ["bairro"]
    df = pl.read_parquet(tmp_path / "bronze" / "periodo=2015T1" / "part.parquet")
    assert df["canal"][0] == "CENTRAL TELEFÔNICA" and df["dt_finalizacao"][0].startswith("2015-01-01")


def test_layout_alternativo_2021T1(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    h = ("Data de Abertura;Data de Finalização;Meio de Comunicação;Tema;Assunto;Serviço;Status;Órgão;"
         "Logradouro;Número;CEP;Latitude;Longitude;Prefeitura Operacional;Distrito")
    normal = "06/01/2021;07/01/2021;CRM;Tema N;Ass N;Serv N;Finalizada;ORG N;Rua N;1;01000000;-23.5;-46.6;SE;SE"
    alt = ("Serv A;ORG A;02/02/2021;;;Tema A;16/02/2021;Ass A;PORTAL;Finalizada;Rua A;PENHA;CAMPO BELO;1132;04620011")
    (tmp_path / "raw" / "2021T1.csv").write_bytes(f"{h}\r\n{normal}\r\n{alt}\r\n".encode("cp1252"))
    sp156_etl.bronze_period("2021T1")
    df = pl.read_parquet(tmp_path / "bronze" / "periodo=2021T1" / "part.parquet").sort("tema")
    a = df.filter(pl.col("tema") == "Tema A").row(0, named=True)
    assert (a["dt_abertura"], a["canal"], a["servico"], a["distrito"], a["cep"], a["numero"]) == \
        ("02/02/2021", "PORTAL", "Serv A", "CAMPO BELO", "04620011", "1132")


def test_silver_dedup_sobreposicao_e_prazo(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    cols = sp156_etl.CANON + ["periodo"]

    def put(periodo, rows):
        d = tmp_path / "bronze" / f"periodo={periodo}"
        d.mkdir(parents=True)
        pl.DataFrame([dict(zip(cols, r)) for r in rows], schema={c: pl.String for c in cols}) \
            .write_parquet(d / "part.parquet")

    def row(ab, fim, p, lat="-23.55", lon="-46.63"):
        r = {c: None for c in cols}
        r.update(dt_abertura=ab, dt_finalizacao=fim, status="Finalizada", tema="T", lat=lat, lon=lon,
                 periodo=p)
        return [r[c] for c in cols]

    # junho aparece em 2017T2 (correto) e 2017T3 (repetido) -> só o de 2017T2 sobrevive
    put("2017T2", [row("2017-06-10 08:00:00", "2017-06-10 00:00:00", "2017T2")])
    put("2017T3", [row("2017-06-10 08:00:00", "2017-06-10 00:00:00", "2017T3"),
                   row("2017-07-01 09:00:00", "2017-07-03 00:00:00", "2017T3", lat="-10", lon="-10")])
    sp156_etl.silver()
    df = pl.read_parquet(tmp_path / "silver" / "**" / "*.parquet", hive_partitioning=True).sort("dt_abertura")
    assert df.height == 2
    assert df["prazo_dias"].to_list() == [0, 2]      # mesmo dia às 08h/00h não é negativo
    assert df["lat"].to_list() == [-23.55, None]      # fora do município -> coordenada anulada
    assert df["status"][0] == "FINALIZADA"


@pytest.mark.parametrize("p,fim", [("2026T2", date(2026, 6, 30)), ("2026T4", date(2026, 12, 31)),
                                   ("2012S1", date(2012, 6, 30))])
def test_fim_periodo(p, fim):
    assert ops._fim_periodo(p) == fim


def test_period_regex():
    assert sp156._period("Dados do SP156 - 2º TRI 2026") == (2026, "2026T2")
    assert sp156._period("Dados do SP156 - 1° SEM 2014") == (2014, "2014S1")
    assert sp156._period("Dicionário") is None
