// @ts-check
import {themes as prismThemes} from 'prism-react-renderer';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

const repo = 'https://github.com/tatyquebralayout/reativacao-abrigos-geosampa';

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Dados Públicos de São Paulo',
  tagline: 'SP156 e GeoSampa: 18,8 milhões de solicitações tratadas, documentadas e abertas em painéis',
  favicon: 'img/logo.svg',

  future: {
    v4: true,
    faster: true, // rspack + SWC (@docusaurus/faster)
  },

  url: 'https://tatyquebralayout.github.io',
  baseUrl: '/reativacao-abrigos-geosampa/',
  organizationName: 'tatyquebralayout',
  projectName: 'reativacao-abrigos-geosampa',
  trailingSlash: false,

  onBrokenLinks: 'throw',
  markdown: {
    mermaid: true,
    hooks: {onBrokenMarkdownLinks: 'warn'},
  },

  i18n: {defaultLocale: 'pt-BR', locales: ['pt-BR']},

  stylesheets: [
    {
      href: 'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css',
      type: 'text/css',
      crossorigin: 'anonymous',
    },
  ],

  themes: [
    '@docusaurus/theme-mermaid',
    '@docusaurus/theme-live-codeblock',
    [
      '@easyops-cn/docusaurus-search-local',
      /** @type {import('@easyops-cn/docusaurus-search-local').PluginOptions} */
      ({
        hashed: true,
        language: ['pt'],
        indexDocs: true,
        indexBlog: true,
        indexPages: true,
        docsRouteBasePath: '/docs',
        highlightSearchTermsOnTargetPage: true,
        explicitSearchResultPath: true,
      }),
    ],
  ],

  plugins: [
    '@docusaurus/plugin-ideal-image',
    'docusaurus-plugin-image-zoom',
    [
      '@docusaurus/plugin-client-redirects',
      {
        redirects: [
          {from: '/dashboard', to: '/painel'},
          {from: '/dados', to: '/docs/catalogo'},
        ],
      },
    ],
    [
      '@docusaurus/plugin-pwa',
      {
        debug: false,
        offlineModeActivationStrategies: ['appInstalled', 'standalone', 'queryString'],
        pwaHead: [
          {tagName: 'link', rel: 'icon', href: 'img/logo.svg'},
          {tagName: 'link', rel: 'manifest', href: 'manifest.json'},
          {tagName: 'meta', name: 'theme-color', content: '#2a78d6'},
        ],
      },
    ],
    ['@signalwire/docusaurus-plugin-llms-txt', {}],
  ],

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: './sidebars.js',
          editUrl: `${repo}/tree/main/website/`,
          remarkPlugins: [remarkMath],
          rehypePlugins: [rehypeKatex],
          showLastUpdateTime: false,
        },
        blog: {
          path: 'blog',
          routeBasePath: 'notas',
          blogTitle: 'Notas de versão dos dados',
          blogDescription: 'O que mudou em cada atualização da base',
          showReadingTime: true,
          feedOptions: {type: ['rss', 'atom'], xslt: true},
          editUrl: `${repo}/tree/main/website/`,
          remarkPlugins: [remarkMath],
          rehypePlugins: [rehypeKatex],
        },
        theme: {customCss: './src/css/custom.css'},
        sitemap: {changefreq: 'weekly', priority: 0.5},
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      image: 'img/social-card.svg',
      colorMode: {respectPrefersColorScheme: true},
      zoom: {selector: '.markdown img', background: {light: 'rgb(255,255,255)', dark: 'rgb(26,26,25)'}},
      navbar: {
        title: 'Dados Públicos SP',
        logo: {alt: 'Dados Públicos SP', src: 'img/logo.svg'},
        items: [
          {
            type: 'dropdown',
            label: 'Painéis',
            to: '/painel',
            items: [
              {label: 'Visão geral', to: '/painel/visao-geral'},
              {label: 'Temas e serviços', to: '/painel/temas'},
              {label: 'Território', to: '/painel/territorio'},
              {label: 'Desempenho', to: '/painel/desempenho'},
              {label: 'Qualidade dos dados', to: '/painel/qualidade'},
              {label: 'Reativação de abrigos', to: '/painel/reativacao'},
            ],
          },
          {type: 'docSidebar', sidebarId: 'docs', position: 'left', label: 'Documentação'},
          {to: '/notas', label: 'Notas de versão', position: 'left'},
          {href: repo, label: 'GitHub', position: 'right'},
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Painéis',
            items: [
              {label: 'Visão geral', to: '/painel/visao-geral'},
              {label: 'Território', to: '/painel/territorio'},
              {label: 'Qualidade dos dados', to: '/painel/qualidade'},
            ],
          },
          {
            title: 'Documentação',
            items: [
              {label: 'Catálogo de dados', to: '/docs/catalogo'},
              {label: 'Metodologia', to: '/docs/metodologia/plano-de-tratamento'},
              {label: 'Guias', to: '/docs/guias/executar-o-pipeline'},
            ],
          },
          {
            title: 'Fontes oficiais',
            items: [
              {label: 'Portal de Dados Abertos (SP156)', href: 'https://dados.prefeitura.sp.gov.br/dataset/dados-do-sp156'},
              {label: 'GeoSampa', href: 'https://geosampa.prefeitura.sp.gov.br'},
              {label: 'Metadados GeoSampa', href: 'https://metadados.geosampa.prefeitura.sp.gov.br'},
              {label: 'Repositório', href: repo},
            ],
          },
        ],
        copyright:
          'Dados: Prefeitura do Município de São Paulo (licença CC0 no CKAN; GeoSampa sem restrições). ' +
          'Projeto independente, sem vínculo oficial com a Prefeitura.',
      },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
        additionalLanguages: ['bash', 'python', 'sql', 'yaml', 'json'],
      },
      liveCodeBlock: {playgroundPosition: 'bottom'},
      mermaid: {theme: {light: 'neutral', dark: 'dark'}},
      tableOfContents: {minHeadingLevel: 2, maxHeadingLevel: 4},
    }),
};

export default config;
