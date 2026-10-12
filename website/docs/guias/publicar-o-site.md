---
title: Publicar o site
sidebar_position: 3
description: Do build local ao GitHub Pages
---

# Publicar o site

O site é um projeto [Docusaurus](https://docusaurus.io) em `website/`, publicado no **GitHub Pages** por um workflow do GitHub Actions a cada push na branch `main` que altere `website/`.

## Desenvolvimento local
```bash
cd website
npm ci
npm start          # http://localhost:3000/dados-publicos-sp/
npm run build      # gera website/build
npm run serve      # serve o build
```

## Plugins instalados
| Plugin | Para quê |
|---|---|
| `@docusaurus/faster` | build mais rápido (rspack e SWC) |
| `@docusaurus/theme-mermaid` | diagramas em Markdown |
| `@docusaurus/theme-live-codeblock` | blocos de código interativos |
| `@docusaurus/plugin-ideal-image` | imagens responsivas e otimizadas |
| `@docusaurus/plugin-pwa` | instalável e utilizável offline |
| `@docusaurus/plugin-client-redirects` | redirecionamentos (`/dashboard`, `/dados`) |
| `@easyops-cn/docusaurus-search-local` | busca local em português |
| `docusaurus-plugin-image-zoom` | zoom nas imagens |
| `remark-math` e `rehype-katex` | fórmulas em LaTeX |
| `@signalwire/docusaurus-plugin-llms-txt` | gera `llms.txt` para ferramentas de IA |
| `leaflet` | mapas dos painéis |

Ficaram de fora, de propósito, plugins que exigem credenciais ou serviços externos (Google Analytics, Algolia, Typesense, Matomo). Eles podem ser adicionados depois.

## Publicação no GitHub Pages
1. No repositório, em **Settings → Pages**, a fonte deve ser **GitHub Actions**.
2. O workflow `.github/workflows/deploy-site.yml` faz o build e publica.
3. Endereço: `https://tatyquebralayout.github.io/dados-publicos-sp/`.

Se o repositório mudar de nome, atualize `url`, `baseUrl` e `projectName` em `website/docusaurus.config.js`, e o `start_url`/`scope` de `website/static/manifest.json`.

## Mapas
Os mapas **não usam tiles de terceiros**. O contexto geográfico é o contorno dos 96 distritos, que já está nos dados do site. Isso evita chaves de API, dependência de provedores e envio de dados de navegação a terceiros, e os mapas funcionam offline (PWA). A contrapartida é não haver ruas nem pontos de referência: se isso for necessário, adicione um provedor de tiles em `website/src/components/viz/Maps.js`, respeitando a política de uso dele.
