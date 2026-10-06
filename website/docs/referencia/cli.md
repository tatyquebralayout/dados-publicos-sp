---
title: Comandos (CLI)
sidebar_position: 1
description: Todos os comandos do dados-publicos
---

# Comandos

`dados-publicos <comando> [camada] [opções]`

| Comando | O que faz |
|---|---|
| `update` | rotina completa e incremental do SP156 (baixa, bronze, silver, qualidade, gold, geo, frescor) |
| `freshness` | compara o CKAN com o local; sai com código 2 se houver avisos |
| `prune` | lista execuções antigas do raw GeoSampa (`--keep N`, `--apply` para apagar) |
| `catalog` | lê o `GetCapabilities` do WFS e grava `config/catalog.csv` |
| `ingest`, `bronze`, `silver`, `gold`, `check`, `all` | etapas para camadas GeoSampa (uma camada, uma família ou todas) |
| `unify <família>` | silver unificada da família (por exemplo `sac_todas`) |
| `sp156-download` | baixa os arquivos do CKAN |
| `sp156-bronze` | bronze do SP156 (`--force` reprocessa todos os períodos) |
| `sp156-silver` | silver do SP156 |
| `sp156-quality` | regras de qualidade por período |
| `sp156-gold` | agregados |
| `geo` | distrito por coordenada, grade de 500 m, qualidade do distrito |

## Opções
| Opção | Efeito |
|---|---|
| `--workers N` | camadas GeoSampa em paralelo (padrão 4) |
| `--force` | reprocessa a bronze mesmo que esteja atualizada |
| `--keep N` | `prune`: execuções a manter por camada (padrão 2) |
| `--apply` | `prune`: apaga de verdade (o padrão é simular) |

## Scripts
| Script | Efeito |
|---|---|
| `scripts/export_site_data.py` | gera `website/static/data/*.json` (só agregados) |
| `deploy/run_update.sh` | `update` + `prune` + `freshness`, com log em `logs/` |
