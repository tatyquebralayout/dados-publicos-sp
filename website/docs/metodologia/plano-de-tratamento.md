---
title: Plano de tratamento
sidebar_position: 1
description: Fontes, arquitetura em camadas, decisões, roadmap e operação do pipeline
---

# Plano de tratamento de dados

Estado em 2026-10-06. Todas as fases foram executadas ou avaliadas (ver §3). Esta página é a fonte única do plano; ela substitui o antigo `docs/PLANO_TRATAMENTO.md`.

## 1. Fontes

| Fonte | O que é | Volume tratado |
|---|---|---|
| GeoSampa WFS (`geoportal:sac_*`) | 94 camadas SP156 georreferenciadas (registro `5703aa4e-…`: "Reativação de um abrigo ou ponto que foi extinto" é uma delas). EPSG:31983 | 143.461 linhas, abr–set/2020 |
| GeoSampa WFS (`distrito_municipal`) | 96 polígonos de distrito (referência geográfica) | 96 |
| CKAN Portal de Dados Abertos (`dados-do-sp156`) | **Base SP156 completa**, CSV/XLSX trimestrais, 2015T1 a 2026T2 | **18.774.202 linhas**, 46 períodos, 3,8 GB brutos |

O catálogo WFS tem 484 camadas (`config/catalog.csv`). Só a família `sac_*` e os distritos foram tratados; as outras têm esquemas próprios.

**As camadas GeoSampa `sac_*` estão desatualizadas na fonte.** Todas trazem `dt_carga` = 2021-03-25 e aberturas de abril a setembro de 2020, apesar de o metadado dizer "últimos 6 meses". A base de longo prazo vem do CKAN. O comando `freshness` sinaliza isso a cada execução.

## 2. Arquitetura

```
GeoSampa WFS ─► raw/<camada>/<run>/page_*.json ─► bronze ─► silver ─► gold   (sac_*: 94 camadas → sac_todas)
CKAN SP156   ─► raw/sp156/<periodo>.csv|xlsx   ─► bronze/sp156/periodo=…  (texto, esquema canônico)
                                               ─► silver/sp156/ano=/mes=   (tipada, validada)
                                               ─► gold/sp156/*.parquet     (agregados, qualidade, grade)
distrito_municipal ─► geo.build(): point-in-polygon sobre coordenadas distintas ─► distrito_geo + grade 500 m
```

| Camada | Conteúdo | Tamanho |
|---|---|---|
| raw | arquivos originais, imutáveis | 3,8 GB |
| bronze | Parquet zstd, 16 colunas canônicas em texto, uma partição por período | 336 MB |
| silver | datas/números tipados, coordenadas validadas, particionada por `ano/mes` | 426 MB |
| gold | mensal×tema×canal, distrito×ano, órgão×ano, grade 500 m, qualidade | 3 MB |

Consulta típica na silver (18,7 M de linhas): 0,03–0,04 s com DuckDB. Memória de pico: ~1 GB na bronze (reprocessamento completo: 1 min 47 s, pois o leitor tolerante a aspas roda sem paralelismo) e na geo; ~4–5 GB na silver (`memory_limit` de 3 GB, que o DuckDB ultrapassa um pouco).

### Decisões
- **Parquet + DuckDB/Polars, sem Spark.** 18,7 M de linhas e 426 MB cabem folgadamente numa máquina.
- **Bronze em texto puro.** Nada é perdido por erro de conversão; a tipagem acontece na silver, onde falhas são mensuráveis.
- **Sem geopandas.** Pontos e point-in-polygon ficam com a extensão `spatial` do DuckDB, e `pyproj` reprojeta as camadas GeoSampa.
- **Prazo em dias de calendário** (`prazo_dias` = data de finalização − data de abertura). Os arquivos antigos têm hora e os novos só data, e comparar com hora gerava falsos negativos.
- **Prazo só é confiável a partir de 2020** (`prazo_confiavel`). Antes disso "Data do Parecer" não é a data de finalização: em 2015, 100% dos prazos são zero e em 2017 a mediana é de 28 dias. As métricas de prazo do site usam só 2020 em diante.

## 3. Roadmap e status

| Fase | Entrega | Status |
|---|---|---|
| 0 | Pipeline ponta a ponta numa camada | ✅ |
| 1 | Família `sac_*` (94 camadas), silver unificada `sac_todas` | ✅ 143.461 linhas, ~11 s |
| 2 | `catalog`: 484 camadas em `config/catalog.csv` | ✅ |
| 3 | Particionamento Hive + paralelismo | ✅ silver SP156 por `ano/mes`, `sac_todas` por `ano_mes`; camadas em paralelo (`--workers`), download com 2 conexões. **Não medido:** ingestão do catálogo inteiro (484 camadas), por não haver esquema pronto para as demais. |
| 4 | SP156 completo, 2015+ | ✅ 46 períodos, 18,77 M linhas, 7 variantes de esquema tratadas (§4) |
| 5 | Geoespacial | ✅ distrito por ponto, grade 500 m, recuperação de distrito ausente (§5). H3 e subprefeituras ficaram de fora. |
| 6 | Operação | ✅ `update` (incremental e idempotente), `freshness`, `prune`, `deploy/` (systemd/cron, **não instalado**) |
| 7 | Armazenamento em objeto + Iceberg/Delta | ⏸ **Avaliada, não implementada** (§6) |

## 4. Anomalias da fonte
Catalogadas e tratadas em [Anomalias da fonte](./anomalias-da-fonte.md). As quatro com maior efeito nos números: 2021T1 com dois layouts, meses repetidos entre arquivos, 2021T2 só em XLSX e prazo confiável apenas de 2020 em diante.

## 5. Geoespacial (fase 5)
- 3,38 M de coordenadas distintas cruzadas com os 96 distritos em ~13 s; 4.220 pontos caem fora de qualquer distrito (borda do município).
- **O distrito declarado coincide com o geográfico em ~95–98% dos casos.** As divergências são vizinhos reais (Jaçanã/Tremembé, Sé/República, Santana/Pari), isto é, pontos de borda ou geocodificação no nível da rua, e não diferença de grafia.
- **O cruzamento recupera o distrito ausente**: ~134 mil linhas de 2017, ~48 mil de 2022, 21 mil de 2024. O resultado está em `gold/sp156/distrito_final_ano.parquet` (distrito declarado, senão o geográfico).
- `grade_500m_ano_tema.parquet`: solicitações por célula de 500 m (UTM 23S: `x_utm`, `y_utm`) × ano × tema, pronta para mapa de calor.

- **O código do distrito é traduzido.** Desde 2025T2 parte das linhas traz o código numérico (1 a 96) em vez do nome. O código coincide em 100% dos casos com `cd_distrito_municipal` da camada oficial `distrito_municipal`, e `config/distritos.csv` faz a tradução. Sem isso haveria 191 "distritos" em vez de 96.

## 6. Fase 7 — por que não foi implementada
O critério do plano era "se passar de ~100 GB". O volume real é **3,8 GB brutos / 0,4 GB tratados**, 250 vezes abaixo. Object storage com catálogo Iceberg/Delta acrescentaria custo e complexidade sem ganho. **Gatilhos para revisitar:** > 100 GB de silver, mais de uma máquina escrevendo, ou necessidade de *time travel*/auditoria de versões. O caminho de migração é curto: o DuckDB já lê/escreve `s3://` via `httpfs`, e as camadas já são Parquet particionado em Hive.

## 7. Operação
```bash
.venv/bin/dados-publicos update                  # baixa só o novo, refaz bronze/silver/gold/geo, checa qualidade
.venv/bin/dados-publicos freshness               # código 2 = há avisos (fonte atrasada, período novo, arquivo republicado)
.venv/bin/dados-publicos prune --keep 2          # dry-run; --apply apaga execuções antigas do raw GeoSampa
.venv/bin/dados-publicos catalog                 # atualiza o catálogo WFS
.venv/bin/dados-publicos all sac --workers 4     # família sac_* + sac_todas
.venv/bin/dados-publicos sp156-download|sp156-bronze|sp156-silver|sp156-quality|sp156-gold|geo
.venv/bin/pytest                                 # 8 testes
```
- `update` tolera a indisponibilidade da fonte (usa o `raw/` local e avisa); o CKAN já derrubou conexões durante este trabalho, e os acessos agora têm retentativa.
- `deploy/` tem o script, a unit e o timer do systemd (semanal). **Nada foi instalado**; as instruções estão em `deploy/README.md`.
- `bronze` é incremental (só reprocessa o período cujo arquivo é mais novo); `silver` é refeita inteira (~30 s) e apaga o destino antes, para não deixar arquivos órfãos.

## 8. Pendências
- Confirmar com a Prefeitura o layout do 2021T1 ([anomalia 3](./anomalias-da-fonte.md)).
- 2012–2014 (publicados por semestre, com o sufixo `.xlsx.csv`) ficaram de fora (`from_year: 2015` em `config/layers.yaml`).
- Famílias GeoSampa além de `sac_*` (zoneamento, redes, equipamentos) exigem uma entrada em `families:` por esquema.
- Subprefeituras e H3 não foram feitos. A coluna `subprefeitura` do SP156 tem dois significados (subprefeitura até 2019, "prefeitura operacional" depois) e não deve ser comparada entre eras.
- Retenção de `raw/sp156` não existe, por ser a fonte primária.
