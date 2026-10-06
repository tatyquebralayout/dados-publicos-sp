---
slug: primeira-versao
title: "v0.1: base SP156 completa e primeiros painéis"
authors: [projeto]
tags: [versao, sp156]
---

Primeira versão pública do projeto.

{/* truncate */}

## O que entrou
- **Base SP156 completa:** 46 períodos (2015T1 a 2026T2), **18.774.202 solicitações**.
- **94 camadas GeoSampa `sac_*`:** 143.461 solicitações de abril a setembro de 2020.
- **Seis painéis** e a documentação técnica.

## O que mudou nos dados em relação ao bruto
- **125.482 linhas duplicadas removidas** (junho/2017 e outubro/2018 apareciam em dois arquivos).
- **2021T1 recuperado:** 740 mil linhas vinham com as colunas em outra ordem. O mapeamento foi **inferido**; confirme antes de usar esse trimestre.
- **2021T2 lido de XLSX**, porque o CSV não existe na fonte.
- **Distritos:** parte das linhas de 2025T2 em diante traz o código numérico; foi traduzido para o nome.
- **Prazo:** só a partir de 2020, porque antes disso o campo da fonte não é a data de finalização.

## Limites conhecidos
- As camadas GeoSampa estão 5,5 anos sem atualização na fonte.
- Os mapas mostram contagens, não taxas por população.
- 54% das solicitações têm coordenada.
