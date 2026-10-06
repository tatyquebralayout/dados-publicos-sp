---
title: Camadas GeoSampa sac_*
sidebar_position: 4
description: As 94 camadas SP156 do GeoSampa e seu esquema comum
---

# Camadas GeoSampa `sac_*`

O GeoSampa publica as solicitações do SP156 **uma camada por serviço** (por exemplo, `sac_tapa_buraco`, `sac_remocao_entulho`). São **94 camadas** com o mesmo esquema, todas em EPSG:31983.

| Campo | Significado |
|---|---|
| `cd_identificador` | identificador na camada (chave usada na deduplicação) |
| `dt_abertura`, `dt_parecer` | datas de abertura e de parecer |
| `nm_logradouro`, `nr_logradouro` | endereço (não publicado no site) |
| `sg_orgao_responsavel` | órgão |
| `tx_situacao_solicitacao`, `tx_canal_atendimento` | situação e canal |
| `dc_tema`, `dc_assunto`, `dc_servico` | classificação |
| `dt_carga` | data da carga na camada |
| geometria | ponto (`ge_ponto`) |

Após o tratamento, as 94 camadas são unidas em **`data/silver/sac_todas`** (coluna `camada` indica a origem), com **143.461 linhas**.

:::caution[Camadas paradas]
Todas as camadas `sac_*` têm `dt_carga` de **2021-03-25** e aberturas de abril a setembro de 2020, embora o metadado diga "últimos 6 meses". Para uma série longa, use a base SP156 do CKAN. O comando `dados-publicos freshness` sinaliza essa defasagem.
:::

## Maiores camadas
Veja o gráfico no painel [Reativação de abrigos](/painel/reativacao). As três maiores são `sac_tapa_buraco` (41.687), `sac_remocao_grande_objeto` (21.676) e `sac_remocao_entulho` (12.941).

## Como a família é declarada
Em `config/layers.yaml`:
```yaml
families:
  sac:
    pattern: "^sac_"
    key: cd_identificador
    date_cols: [dt_abertura, dt_parecer]
    text_cols: [nm_logradouro, sg_orgao_responsavel, tx_situacao_solicitacao,
                tx_canal_atendimento, dc_tema, dc_assunto, dc_servico]
```
O padrão é aplicado sobre `config/catalog.csv`, de modo que uma camada nova do mesmo esquema entra sem mexer no código.
