import React from 'react';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import Head from '@docusaurus/Head';
import {HomeKpis} from '../components/panels/Panels';

const personas = [
  {t: 'Quero ver os números', p: 'Painéis por pergunta: volume, temas, território, desempenho e qualidade.', to: '/painel', c: 'Abrir os painéis'},
  {t: 'Quero usar os dados', p: 'Catálogo com fontes, camadas (raw → gold), dicionário de colunas e limites conhecidos.', to: '/docs/catalogo', c: 'Ver o catálogo'},
  {t: 'Preciso confiar nos números', p: 'Anomalias encontradas na fonte, como foram tratadas e o que continua incerto.', to: '/docs/metodologia/anomalias-da-fonte', c: 'Ler a metodologia'},
  {t: 'Quero rodar ou contribuir', p: 'Guias para executar o pipeline, atualizar, publicar o site e propor mudanças.', to: '/docs/guias/executar-o-pipeline', c: 'Ver os guias'},
];

export default function Home() {
  return (
    <Layout description="Painéis com 18,8 milhões de solicitações do SP156 e mapas do GeoSampa, com pipeline aberto em Python e dados que você pode conferir.">
      <Head>
        <title>Dados públicos de São Paulo · Tatiana Barros</title>
        <meta property="og:title" content="Dados públicos de São Paulo · Tatiana Barros" />
        <meta name="twitter:title" content="Dados públicos de São Paulo · Tatiana Barros" />
      </Head>
      <header className="hero hero--home">
        <div className="container">
          <h1 className="hero__title">Dados Públicos de São Paulo</h1>
          <p className="hero__subtitle">
            A base completa do SP156 (2015–2026) e as camadas de solicitações do GeoSampa, tratadas num pipeline
            reproduzível, documentadas e abertas em painéis.
          </p>
          <div style={{display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 18}}>
            <Link className="button button--secondary button--lg" to="/painel">Explorar os painéis</Link>
            <Link className="button button--outline button--lg" style={{color: '#fff', borderColor: '#9ec5f4'}} to="/docs/intro">Ler a documentação</Link>
          </div>
        </div>
      </header>
      <main className="container margin-vert--lg">
        <HomeKpis />
        <h2>Por onde começar</h2>
        <div className="persona-grid">
          {personas.map((x) => (
            <div className="persona" key={x.t}>
              <h3>{x.t}</h3>
              <p>{x.p}</p>
              <Link to={x.to}>{x.c} →</Link>
            </div>
          ))}
        </div>
        <div className="callout-caveat">
          <b>Origem desta documentação.</b> O projeto começou pela camada GeoSampa{' '}
          <Link to="/painel/reativacao">"Reativação de um abrigo ou ponto que foi extinto"</Link> e cresceu para a base SP156 completa.
          Projeto independente, sem vínculo oficial com a Prefeitura de São Paulo.
        </div>
      </main>
    </Layout>
  );
}
