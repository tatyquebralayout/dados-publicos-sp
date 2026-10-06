---
title: Regras de qualidade
sidebar_position: 2
description: O que é validado e o que bloqueia o pipeline
---

# Regras de qualidade

## Bloqueiam o `update` (SP156)
| Regra | Por quê |
|---|---|
| Todos os períodos da bronze existem na silver | evita perda silenciosa de um arquivo |
| Nenhuma abertura antes do primeiro dia do trimestre do arquivo | detecta arquivo trocado ou misturado |
| Cada período tem pelo menos 100 mil linhas | detecta arquivo truncado ou vazio |
| Menos de 1% das linhas com finalização anterior à abertura | detecta troca de colunas |

## Aplicadas na silver
| Regra | Efeito |
|---|---|
| Data de abertura ilegível | a linha é descartada (hoje, nenhuma) |
| Mês repetido em dois arquivos | só a cópia do arquivo do próprio trimestre é mantida |
| Coordenada fora do bbox do município | `lat` e `lon` viram nulos |
| Código numérico de distrito | traduzido para o nome |
| Prazo antes de 2020 | `prazo_confiavel = false` |

## Regras das camadas `sac_*`
Tabela não vazia, chave `cd_identificador` única e não nula, pontos dentro do município, `dt_parecer` não anterior a `dt_abertura` e `dt_abertura` legível. Falha em uma camada não derruba o lote; ela aparece no resumo.

## Onde ver os resultados
O painel [Qualidade dos dados](/painel/qualidade) mostra a cobertura por período, e `gold/sp156/qualidade_periodo.parquet` traz os números brutos.

## O que as regras **não** garantem
Que os dados estejam *corretos*, apenas que estão *consistentes*. Por exemplo, o layout alternativo do 2021T1 passa nas regras, mas foi inferido. Veja as [anomalias da fonte](../metodologia/anomalias-da-fonte.md).
