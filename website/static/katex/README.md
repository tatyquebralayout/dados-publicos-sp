# KaTeX servido pelo próprio site

Cópia de `katex.min.css` e das fontes `.woff2` do pacote [`katex`](https://katex.org) **0.16.47**, a mesma versão que o `rehype-katex` usa para gerar as fórmulas. Licença MIT, em `LICENSE`.

Fica aqui para o site não depender de um CDN externo. O CSS carrega sem bloquear a página (ver `headTags` em `docusaurus.config.js`). Só as fontes `.woff2` foram copiadas, porque todos os navegadores atuais leem esse formato.

Para atualizar, rode depois de `npm ci`, dentro de `website/`:

```bash
cp node_modules/katex/dist/katex.min.css static/katex/
cp node_modules/katex/dist/fonts/*.woff2 static/katex/fonts/
```

*English: self-hosted KaTeX CSS and woff2 fonts (v0.16.47, MIT), loaded without blocking rendering.*
