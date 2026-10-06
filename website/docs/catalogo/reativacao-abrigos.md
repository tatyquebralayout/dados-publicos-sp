---
title: Reativação de abrigos
sidebar_position: 5
description: Ficha da camada GeoSampa que originou o projeto
---

# Reativação de um abrigo ou ponto que foi extinto

Ficha da camada, conforme o registro de metadados do GeoSampa e o que encontramos nos dados.

| Item | Valor |
|---|---|
| Registro | `5703aa4e-e3ca-4284-812a-0d1e2fde09bb` ([abrir no GeoNetwork](https://metadados.geosampa.prefeitura.sp.gov.br/geonetwork/srv/por/catalog.search#/metadata/5703aa4e-e3ca-4284-812a-0d1e2fde09bb)) |
| Padrão | ISO 19115:2003/19139, nível `dataset` |
| Camada WFS | `geoportal:sac_reativacao_abrigo_ponto_extinto` |
| Geometria | ponto, vetorial |
| Sistema de referência | SIRGAS 2000 / UTM 23S (EPSG:31983) |
| Responsável pelos dados | SMIT/CASP (Secretaria Municipal de Inovação e Tecnologia) |
| Responsável pelo metadado | SMUL/GEOINFO |
| Atualização declarada | trimestral |
| Restrições | sem restrições |
| Descrição | solicitações SP156 georreferenciadas dos últimos 6 meses do Portal de Dados Abertos |

## O que a camada contém de fato
- **45 solicitações**, abertas entre 2020-04-15 e 2020-09-30; carga em 2021-03-25.
- Todas do órgão SPTRANS.
- Situação: 39 finalizadas, 5 aguardando atendimento, 1 cancelada.
- Canal: 34 central telefônica, 11 portal online.
- O campo `cd_identificador_original_atendimento_cidadao` é 100% nulo.

O painel [Reativação de abrigos](/painel/reativacao) mostra a camada num mapa e a compara com as outras 93 camadas SP156.

## Como baixar
```bash
curl -G "http://wfs.geosampa.prefeitura.sp.gov.br/geoserver/ows" \
  --data-urlencode "service=WFS" --data-urlencode "version=2.0.0" \
  --data-urlencode "request=GetFeature" \
  --data-urlencode "typeNames=geoportal:sac_reativacao_abrigo_ponto_extinto" \
  --data-urlencode "outputFormat=application/json" -o reativacao.geojson
```
O registro de metadados **não traz link de download**; o WFS foi localizado no catálogo do GeoServer.
