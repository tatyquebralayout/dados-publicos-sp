---
title: Arquivos de dados do site
sidebar_position: 3
description: Os JSONs agregados que alimentam os painéis
---

# Arquivos de dados do site

Gerados por `scripts/export_site_data.py` em `website/static/data/` e servidos em `/data/<nome>.json`. **Só agregados.**

| Arquivo | Conteúdo | Usado em |
|---|---|---|
| `overview.json` | totais, cobertura, frescor | home, visão geral |
| `mensal.json`, `anual.json` | série mensal e anual | visão geral |
| `canal_ano.json`, `status_ano.json` | canal e situação por ano | visão geral |
| `tema_ano.json`, `servicos_top.json` | temas por ano, 30 maiores serviços | temas e serviços |
| `distritos.json`, `distritos_geo.json` | total por distrito e ano, polígonos simplificados | território |
| `grade.json` | células de 500 m por tema, mínimo de 5 solicitações | território |
| `orgaos_top.json`, `tema_desempenho.json`, `prazo_faixas_ano.json` | desempenho, só 2020 em diante | desempenho |
| `qualidade_periodo.json`, `qualidade_distrito.json` | cobertura e coincidência de distrito | qualidade |
| `sac_camadas.json`, `reativacao.json` | camadas GeoSampa e a camada de reativação (sem endereço) | reativação |

## Privacidade
- Nenhum arquivo contém logradouro, número, CEP ou linha individual do SP156.
- `grade.json` oculta células com menos de 5 solicitações.
- `reativacao.json` traz as 45 coordenadas da camada GeoSampa, **sem endereço**, e o mês de abertura.
