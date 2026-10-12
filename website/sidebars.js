/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docs: [
    'intro',
    'catalogo/baixe-os-dados',
    {
      type: 'category', label: 'Catálogo de dados', link: {type: 'doc', id: 'catalogo/index'},
      items: ['catalogo/camadas', 'catalogo/dicionario-sp156', 'catalogo/geosampa-sac', 'catalogo/reativacao-abrigos'],
    },
    {
      type: 'category', label: 'Metodologia', collapsed: false,
      items: ['metodologia/plano-de-tratamento', 'metodologia/anomalias-da-fonte', 'metodologia/arquitetura-da-informacao'],
    },
    {
      type: 'category', label: 'Guias', collapsed: false,
      items: ['guias/executar-o-pipeline', 'guias/atualizar-e-agendar', 'guias/publicar-o-site', 'guias/adicionar-uma-camada'],
    },
    {
      type: 'category', label: 'Referência',
      items: ['referencia/cli', 'referencia/regras-de-qualidade', 'referencia/json-do-site'],
    },
  ],
};
export default sidebars;
