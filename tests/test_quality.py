import polars as pl

from dados_publicos import config, quality, transform


def test_pipeline_e_qualidade(tmp_path, monkeypatch):
    import json
    _, layers = config.load()
    L = layers["sac_reativacao_abrigo_ponto_extinto"]
    for mod in (config, transform, quality):
        monkeypatch.setattr(mod, "DATA", tmp_path, raising=False)
    raw = tmp_path / "raw" / L.name / "r1"
    raw.mkdir(parents=True)
    feat = lambda i, x, y, ab, pa: {"geometry": {"type": "Point", "coordinates": [x, y]},
        "properties": {"cd_identificador": i, "dt_abertura": ab, "dt_parecer": pa,
        "nm_logradouro": "  Rua  A ", "sg_orgao_responsavel": "SPTRANS",
        "tx_situacao_solicitacao": "FINALIZADA", "tx_canal_atendimento": "PORTAL ONLINE",
        "dc_tema": "T", "dc_assunto": "A", "dc_servico": "S"}}
    fs = [feat(1, 330807.97, 7391540.07, "2020-07-01T13:00:00Z", "2020-07-03T13:00:00Z"),
          feat(1, 330807.97, 7391540.07, "2020-07-01T13:00:00Z", "2020-07-03T13:00:00Z")]
    (raw / "page_00000.json").write_text(json.dumps({"features": fs}))
    transform.bronze(L)
    p = transform.silver(L, "America/Sao_Paulo")
    df = pl.read_parquet(p)
    assert df.height == 1                       # dedupe pela chave
    assert df["nm_logradouro"][0] == "Rua A"    # espaços normalizados
    assert df["prazo_dias"][0] == 2.0
    assert quality.check(L) == []
    transform.gold(L)
