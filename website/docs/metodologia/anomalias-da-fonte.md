---
title: Anomalias da fonte
sidebar_position: 2
description: O que encontramos de irregular nos arquivos do SP156 e do GeoSampa, e como cada caso foi tratado
---

# Anomalias da fonte

Os arquivos públicos do SP156 foram publicados ao longo de onze anos, por pessoas e sistemas diferentes. Isso deixou irregularidades que, se ignoradas, **distorcem os números**. Esta página registra cada uma, o que fizemos e o que ainda é incerto.

| # | Anomalia | Tratamento |
|---|---|---|
| 1 | 7 variantes de cabeçalho; `Canal`/`Meio de Comunicação`, `Data do Parecer`/`Data de Finalização`, `Subprefeitura`/`Prefeitura Operacional` | mapa de aliases → 16 colunas canônicas; coluna ausente vira nula e é registrada |
| 2 | Separador `,` em 2020 (com aspas) e `;` nos demais; UTF-8 com BOM em 2020, cp1252 no resto | detecção por arquivo, transcodificação em streaming |
| 3 | **2021T1 mistura dois layouts** no mesmo arquivo: 740.288 linhas, a partir da linha 275.427, têm as colunas em outra ordem | mapeamento posicional alternativo, **inferido pelo conteúdo** (ver aviso abaixo) |
| 4 | **2021T2 só existe em XLSX** (o recurso "CSV" do CKAN aponta para um `.xlsx`) | leitura da aba 1 com calamine; o CSV é preferido quando existe |
| 5 | Linhas totalmente vazias (2025T1: 305.671; 2016T3: 56.676) | descartadas na bronze. O 2025T1 **não** está truncado: os 90 dias do trimestre aparecem |
| 6 | **Meses repetidos entre arquivos**: junho/2017 (2017T2 e T3) e outubro/2018 (2018T3 e T4) | silver mantém só linhas cujo trimestre bate com o período do arquivo. 125.482 linhas descartadas |
| 7 | Finalização "antes" da abertura por falta de hora (00:00:00) | prazo em dias de calendário. Sobram casos reais em 15 períodos (1 a 457 por período; máximo 2019T4 com 457, cerca de 0,17%). O `prazo_dias` desses fica nulo |
| 8 | 2022T3 sem latitude/longitude; 2024T2 sem `Serviço`; 2017T4 sem `Distrito` (traz `Bairro`) | colunas nulas, aparecem em `qualidade_periodo` |
| 9 | Só 54% das solicitações têm coordenada (10,2 M) | coordenada fora do município é anulada |
| 10 | Não há protocolo/ID no arquivo | **sem deduplicação por chave**; só se remove a sobreposição do item 6 |
| 11 | **Código no lugar do nome do distrito** (2025T2 em diante: 1, 814, 1.247 e 1.250 linhas por trimestre) | tradução por `cd_distrito_municipal` do GeoSampa (coincidência de 100%); sem isso haveria 191 distritos |
| 12 | **"Data do Parecer" não é a data de finalização antes de 2020** (2015: 100% dos prazos são zero; 2017: mediana de 28 dias) | coluna `prazo_confiavel`: o prazo só é usado de 2020 em diante |
| 13 | **Temas de teste do sistema** misturados às demandas reais ("tema001 - teste", "TESTE SEI", "Teste Técnico Metasix", "Teste permissionamento do órgão", "teste", "tema002"): 4.714 solicitações (4.695 de 2020 em diante e 19 de 2018 e 2019) | excluídos de todos os agregados do site pelo padrão `teste` ou `tema0NN` no nome do tema |

:::caution[Confirme antes de usar o 2021T1]
A ordem das colunas do layout alternativo do 2021T1 foi **deduzida do conteúdo** (datas, canal, status e CEP caem em posições coerentes), sem confirmação da fonte. Se a sua análise depender desse trimestre, confirme o layout com a Prefeitura. As duas colunas sempre vazias nesse layout foram tratadas como coordenadas ausentes.
:::

## O que não tem solução nos dados
- **Não há protocolo ou ID** nos arquivos: não é possível deduplicar por chave nem acompanhar uma solicitação entre períodos.
- **O glossário oficial não mapeia os canais novos** (`CRM`, `PORTAL`, `MOBILE`, `INTEGRACAO`) para os antigos (`CENTRAL TELEFÔNICA`, `PORTAL ONLINE`, `APLICATIVO`). Por isso os canais **não foram fundidos** entre eras.
- A coluna **`subprefeitura`** tem dois significados: subprefeitura até 2019 e "prefeitura operacional" depois. Não compare entre eras.
- Só **54% das solicitações têm coordenada** válida; o restante depende do distrito declarado.
- Os campos de **satisfação** (2015–2019) foram descartados da silver: cobertura parcial e esquema instável.

## Como cada regra é verificada
Ver [Regras de qualidade](../referencia/regras-de-qualidade.md) e o painel [Qualidade dos dados](/painel/qualidade).
