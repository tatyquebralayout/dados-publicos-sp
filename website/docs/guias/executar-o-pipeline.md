---
title: Executar o pipeline
sidebar_position: 1
description: Do zero ao dado tratado, passo a passo
---

# Executar o pipeline

## Pré-requisitos
- Python 3.11 ou superior.
- ~10 GB livres em disco (a base completa ocupa 4,5 GB) e 6 GB de RAM livres.
- Acesso à internet para o CKAN e o GeoSampa.

## Instalação
```bash
git clone https://github.com/tatyquebralayout/reativacao-abrigos-geosampa.git
cd reativacao-abrigos-geosampa
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest          # 8 testes
```

## Rodando tudo
```bash
.venv/bin/dados-publicos update
```
O `update`:
1. consulta o CKAN e baixa **só os arquivos novos ou republicados** (retomável e com retentativa);
2. refaz a **bronze** dos períodos alterados;
3. refaz a **silver** inteira (~30 s);
4. roda as **regras de qualidade**; se alguma falhar, o pipeline para;
5. gera a **gold** e o cruzamento geográfico;
6. confere o **frescor** das fontes e imprime avisos.

Se a fonte estiver fora do ar, o `update` segue com os arquivos locais e avisa.

## Rodando por etapas
```bash
dados-publicos sp156-download   # baixa os CSV/XLSX
dados-publicos sp156-bronze     # --force reprocessa tudo
dados-publicos sp156-silver
dados-publicos sp156-quality
dados-publicos sp156-gold
dados-publicos geo              # distrito por coordenada e grade de 500 m
dados-publicos catalog          # atualiza o catálogo WFS
dados-publicos all sac          # 94 camadas GeoSampa + silver unificada
```
O primeiro `update` completo baixa cerca de 3,8 GB e leva alguns minutos; as execuções seguintes são incrementais.

## Verificando
```bash
dados-publicos freshness        # código de saída 2 = há avisos
```
