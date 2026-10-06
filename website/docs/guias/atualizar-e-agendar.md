---
title: Atualizar e agendar
sidebar_position: 2
description: Rodar a atualização toda semana e regenerar os números do site
---

# Atualizar e agendar

A Prefeitura publica o SP156 por **trimestre**. Uma execução **semanal** do `update` é suficiente: ele só baixa o que mudou.

## Agendamento semanal
Os arquivos estão em `deploy/` e **não são instalados automaticamente**.
```bash
mkdir -p ~/.config/systemd/user
cp deploy/dados-publicos.{service,timer} ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now dados-publicos.timer
```
Alternativa com cron: `0 3 * * 1 /caminho/do/projeto/deploy/run_update.sh`.

## Regenerar o site depois de atualizar
```bash
.venv/bin/python scripts/export_site_data.py      # gera website/static/data/*.json
cd website && npm run build
```
O exportador lê a silver e a gold e grava **só agregados**. Depois de rodá-lo, faça `git commit` dos JSONs alterados e o GitHub Actions publica o site (ver [Publicar o site](./publicar-o-site.md)).

:::caution[Textos com números]
Alguns textos das páginas citam números (por exemplo, "18,8 milhões" ou "72ª posição"). Eles **não** são atualizados automaticamente; revise-os após cada atualização trimestral.
:::

## O que o frescor avisa
- períodos novos na fonte que ainda não foram baixados;
- arquivos republicados (o tamanho mudou);
- último período local com mais de 150 dias de atraso;
- camadas GeoSampa sem atualização (hoje: carga de 2021-03-25).
