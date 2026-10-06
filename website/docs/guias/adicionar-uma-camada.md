---
title: Adicionar uma camada GeoSampa
sidebar_position: 4
description: Como incluir uma camada WFS nova no pipeline
---

# Adicionar uma camada GeoSampa

1. Atualize o catálogo e encontre a camada:
   ```bash
   dados-publicos catalog
   grep -i "ciclo" config/catalog.csv
   ```
2. **Se tiver o mesmo esquema das `sac_*`**, o padrão `^sac_` já a inclui. Basta rodar `dados-publicos all sac`.
3. **Se tiver outro esquema**, descreva-o em `config/layers.yaml`, em `layers:` (camada avulsa) ou em `families:` (padrão de nomes):
   ```yaml
   layers:
     minha_camada:
       typename: geoportal:minha_camada
       srid: 31983
       key: cd_identificador
       date_cols: [dt_abertura]
       text_cols: [nm_logradouro]
   ```
4. Rode e confira:
   ```bash
   dados-publicos all minha_camada
   ```
5. Se a camada não tiver `dt_abertura` ou `lat/lon` no mesmo formato, ajuste `transform.silver` e `quality.check`: hoje eles assumem o esquema `sac_*`.
