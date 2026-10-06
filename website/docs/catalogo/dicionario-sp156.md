---
title: Dicionário SP156
sidebar_position: 3
description: Colunas da tabela silver do SP156
---

# Dicionário SP156 (silver)

Tabela `data/silver/sp156/`, particionada por `ano` e `mes` (mês de abertura). **18.774.202 linhas.**

| Coluna | Tipo | Significado | Observações |
|---|---|---|---|
| `periodo` | texto | Arquivo de origem (`2015T1` … `2026T2`) | rastreabilidade |
| `dt_abertura` | timestamp | Abertura da solicitação | antes de 2020 tem hora; depois só data |
| `dt_finalizacao` | timestamp | Finalização (a partir de 2020) ou "Data do Parecer" (antes) | **antes de 2020 não é a finalização real** |
| `prazo_dias` | inteiro | Dias de calendário entre abertura e finalização | nulo se finalização anterior à abertura |
| `prazo_confiavel` | booleano | Verdadeiro de 2020 em diante | **filtre por ele antes de analisar prazo** |
| `canal` | texto | Canal como publicado | nomenclatura muda em 2020; ver [anomalias](../metodologia/anomalias-da-fonte.md) |
| `tema`, `assunto`, `servico` | texto | Classificação do pedido | 42 temas e 1.751 serviços ao longo dos anos |
| `status` | texto | Situação como publicada, em maiúsculas | `FINALIZADA`, `ABERTO`, `ABERTA`, `EM ANDAMENTO`, `CANCELADA`, `RELACIONADA`… |
| `orgao` | texto | Órgão ou sistema de origem | inclui sistemas integrados (INTEGRAÇÃO-…) |
| `logradouro`, `numero`, `cep`, `bairro` | texto, inteiro | Endereço informado | **não publicados no site**; `bairro` só existe em alguns períodos |
| `subprefeitura` | texto | Subprefeitura (até 2019) ou prefeitura operacional (depois) | não comparar entre eras |
| `distrito` | texto | Nome do distrito (96 valores) | códigos numéricos de 2025T2+ são traduzidos |
| `lat`, `lon` | decimal | Coordenada em WGS84 | nula se ausente ou fora do município; só 54% preenchidas |
| `ano`, `mes` | inteiro | Partição de abertura | |

## Tabelas gold (`data/gold/sp156/`)

| Arquivo | Granularidade |
|---|---|
| `mensal_tema_canal.parquet` | ano, mês, tema, canal, situação |
| `distrito_ano.parquet` | ano, subprefeitura, distrito, tema |
| `orgao_ano.parquet` | ano, órgão |
| `grade_500m_ano_tema.parquet` | célula de 500 m, ano, tema |
| `distrito_final_ano.parquet` | distrito (declarado ou geográfico) por ano |
| `qualidade_periodo.parquet` | período |
| `qualidade_distrito.parquet` | ano |

Os valores de `cx` e `cy` na grade são índices de células de 500 m em UTM 23S (EPSG:31983); `x_utm` e `y_utm` são o centro da célula.
