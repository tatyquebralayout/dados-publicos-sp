# Dados Públicos de São Paulo (SP156 e GeoSampa)

Pipeline Python, documentação e painéis para dados abertos da Prefeitura de São Paulo:

- **Base SP156 completa:** 18.774.202 solicitações, 2015T1 a 2026T2 (CKAN do Portal de Dados Abertos).
- **94 camadas GeoSampa `sac_*`:** 143.461 solicitações, abril a setembro de 2020 (WFS).
- O projeto nasceu da camada [Reativação de um abrigo ou ponto que foi extinto](https://metadados.geosampa.prefeitura.sp.gov.br/geonetwork/srv/por/catalog.search#/metadata/5703aa4e-e3ca-4284-812a-0d1e2fde09bb).

**Site (painéis e documentação):** https://tatyquebralayout.github.io/reativacao-abrigos-geosampa/

## Estrutura
| Pasta | Conteúdo |
|---|---|
| `src/dados_publicos/` | pipeline: download, bronze, silver, gold, geo, qualidade, operação |
| `config/` | camadas (`layers.yaml`), catálogo WFS, códigos de distrito |
| `scripts/export_site_data.py` | gera os agregados JSON dos painéis (só agregados, sem endereços) |
| `website/` | site Docusaurus (painéis, catálogo, metodologia, guias) |
| `tests/` | testes do pipeline |
| `deploy/` | agendamento semanal (systemd/cron), não instalado automaticamente |
| `docs/metadata/` | metadado ISO 19139 original da camada de partida |

Os dados do pipeline (`data/`, 4,5 GB) **não são versionados**; reconstrua com o comando abaixo.

## Rodar
```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest
.venv/bin/dados-publicos update          # baixa, trata, valida e agrega
.venv/bin/python scripts/export_site_data.py
cd website && npm ci && npm start
```
Guia completo: [Executar o pipeline](https://tatyquebralayout.github.io/reativacao-abrigos-geosampa/docs/guias/executar-o-pipeline).

## Limites que importam
- As camadas GeoSampa `sac_*` estão **sem atualização desde 2021**; a série longa vem do CKAN.
- O **prazo de atendimento só é confiável de 2020 em diante**.
- O layout do **2021T1** foi inferido pelo conteúdo, sem confirmação da fonte.
- Os mapas mostram contagens, **não taxas por população**.
- Projeto independente, sem vínculo oficial com a Prefeitura de São Paulo.

## Licença e dados
Os dados vêm da Prefeitura de São Paulo (CKAN: Creative Commons CCZero; GeoSampa: sem restrições, conforme os metadados). O código deste repositório está sob a [licença MIT](LICENSE). Os dados seguem a licença da fonte.
