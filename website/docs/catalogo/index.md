---
title: Catálogo de dados
sidebar_position: 1
slug: /catalogo
description: Fontes, camadas e dicionário das tabelas tratadas
---

# Catálogo de dados

O catálogo é organizado por **fonte** e, dentro de cada uma, por **camada** do pipeline (ver [Arquitetura da informação](../metodologia/arquitetura-da-informacao.md)).

## Fontes

| Fonte | Endereço | Formato | Atualização | Licença |
|---|---|---|---|---|
| **SP156 (CKAN)** | [dados.prefeitura.sp.gov.br/dataset/dados-do-sp156](https://dados.prefeitura.sp.gov.br/dataset/dados-do-sp156) | CSV/XLSX trimestrais (semestrais até 2014) | trimestral | Creative Commons CCZero |
| **GeoSampa WFS** | `http://wfs.geosampa.prefeitura.sp.gov.br/geoserver/ows` | GeoJSON via WFS 2.0, EPSG:31983 | irregular (as camadas `sac_*` estão paradas desde 2021) | sem restrições (metadado) |
| **Metadados GeoSampa** | [metadados.geosampa.prefeitura.sp.gov.br](https://metadados.geosampa.prefeitura.sp.gov.br) | ISO 19115/19139 | n/d | n/d |

## Páginas do catálogo
- [Camadas do pipeline](./camadas.md): raw, bronze, silver, gold e onde estão no disco.
- [Dicionário SP156](./dicionario-sp156.md): colunas da tabela principal.
- [Camadas GeoSampa `sac_*`](./geosampa-sac.md): as 94 camadas e seu esquema.
- [Reativação de abrigos](./reativacao-abrigos.md): a camada que originou o projeto.

## Catálogo WFS completo
O WFS expõe **484 camadas** (lista em `config/catalog.csv`, gerada por `dados-publicos catalog`). Só a família `sac_*` e os polígonos de distrito foram tratados; as demais (zoneamento, redes, equipamentos) têm esquemas próprios e exigem uma entrada em `families:` por esquema.
