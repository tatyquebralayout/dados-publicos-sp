import React, {useMemo, useState} from 'react';
import BrowserOnly from '@docusaurus/BrowserOnly';
import {Data, fmt, fmt1, fmtCompact, fmtYm, pct} from '../viz/data';
import ChartCard, {Kpis} from '../viz/Card';
import {HBars, HeatMatrix, LineChart, StackedBars, colorFor} from '../viz/Charts';

const MapFallback = () => <div className="vstatus">Carregando mapa…</div>;
const Lazy = ({children}) => <BrowserOnly fallback={<MapFallback />}>{() => children()}</BrowserOnly>;
const DistrictMap = (p) => <Lazy>{() => { const {DistrictMap: C} = require('../viz/Maps'); return <C {...p} />; }}</Lazy>;
const GridMap = (p) => <Lazy>{() => { const {GridMap: C} = require('../viz/Maps'); return <C {...p} />; }}</Lazy>;
const PointMap = (p) => <Lazy>{() => { const {PointMap: C} = require('../viz/Maps'); return <C {...p} />; }}</Lazy>;

const Select = ({value, onChange, options, label}) => (
  <label style={{fontSize: '0.8rem'}}>{label}{' '}
    <select value={value} onChange={(e) => onChange(e.target.value)}>
      {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  </label>
);

/** Agrupa em top-N chaves por total e dobra o resto em "Outros". */
function pivot(rows, xKey, kKey, vKey, topN, rename = (k) => k) {
  const tot = {};
  rows.forEach((r) => { const k = rename(r[kKey]); tot[k] = (tot[k] || 0) + r[vKey]; });
  const keys = Object.keys(tot).sort((a, b) => tot[b] - tot[a]).slice(0, topN);
  const hasOther = Object.keys(tot).length > topN;
  const by = {};
  rows.forEach((r) => {
    const k = rename(r[kKey]);
    const kk = keys.includes(k) ? k : 'Outros';
    by[r[xKey]] = by[r[xKey]] || {};
    by[r[xKey]][kk] = (by[r[xKey]][kk] || 0) + r[vKey];
  });
  return {
    keys: hasOther ? [...keys, 'Outros'] : keys,
    rows: Object.keys(by).sort().map((x) => ({x, values: by[x]})),
  };
}

const tableFromRows = (rows, keys) => ({
  columns: [{key: 'x', label: 'Ano'}, ...keys.map((k) => ({key: k, label: k, num: true, fmt: (v) => fmt(v || 0)}))],
  rows: rows.map((r) => ({x: r.x, ...r.values})),
});

/* =============================================================== home */
export function HomeKpis() {
  return (
    <Data name="overview">{(ov) => (
      <Kpis items={[
        {label: 'Solicitações SP156 tratadas', value: fmtCompact(ov.total), note: `${fmt(ov.total)} linhas · ${ov.periodos} períodos`},
        {label: 'Período coberto', value: `${ov.primeira.slice(0, 4)}–${ov.ultima.slice(0, 4)}`, note: `até ${ov.ultima.split('-').reverse().join('/')}`},
        {label: 'Com coordenada válida', value: pct(ov.pct_coordenada), note: 'dentro do município'},
        {label: 'Com distrito (declarado ou geográfico)', value: pct(ov.pct_distrito_final)},
        {label: 'Camadas GeoSampa tratadas', value: fmt(ov.sac_camadas), note: `${fmt(ov.sac_linhas)} linhas (abr–set/2020)`},
      ]} />
    )}</Data>
  );
}

/* =============================================================== visão geral */
export function VisaoGeralPanel() {
  const [status100, setStatus100] = useState(true);
  return (
    <Data name={['overview', 'mensal', 'anual', 'canal_ano', 'status_ano']}>
      {(ov, mensal, anual, canalAno, statusAno) => {
        const canais = pivot(canalAno, 'ano', 'canal', 'n', 6, (k) => (k === 'SEM CANAL' ? 'Sem canal' : k));
        const sit = pivot(statusAno, 'ano', 'situacao', 'n', 4);
        const cells = mensal.map((d) => ({row: d.ym.slice(0, 4), col: +d.ym.slice(5), v: d.n}));
        const anos = [...new Set(mensal.map((d) => d.ym.slice(0, 4)))];
        return (
          <>
            <Kpis items={[
              {label: 'Solicitações', value: fmtCompact(ov.total), note: fmt(ov.total)},
              {label: 'Finalizadas', value: pct(ov.pct_finalizada)},
              {label: 'Prazo mediano (2020+)', value: `${fmt1(ov.prazo_mediano_dias)} dia(s)`, note: 'antes de 2020 o campo não é a data de finalização'},
              {label: 'Serviços distintos', value: fmt(ov.servicos)},
              {label: 'Órgãos/origens distintos', value: fmt(ov.orgaos), note: 'inclui sistemas integrados'},
            ]} />

            <ChartCard
              title="Solicitações por mês"
              sub="Cada ponto é um mês de abertura. Passe o cursor para ver o valor exato."
              note="2026 cobre só até junho. Os saltos de 2020 e 2021 vêm do tema Cidadania e assistência social (ver Temas e serviços)."
              table={{columns: [{key: 'ym', label: 'Mês', fmt: fmtYm}, {key: 'n', label: 'Solicitações', num: true, fmt: fmt}], rows: mensal}}>
              <LineChart data={mensal} x="ym" y="n" label="Solicitações abertas por mês, de 2015 a 2026" />
            </ChartCard>

            <div className="grid2">
              <ChartCard
                title="Volume por ano e canal"
                sub="O canal aparece como publicado: a nomenclatura muda em 2020."
                note="Até 2019: CENTRAL TELEFÔNICA e PORTAL ONLINE. De 2020 em diante: CRM, PORTAL, MOBILE e INTEGRACAO. O glossário oficial não mapeia CRM/PORTAL/MOBILE, então os canais não foram fundidos entre eras."
                table={tableFromRows(canais.rows, canais.keys)}>
                <StackedBars rows={canais.rows} keys={canais.keys} label="Solicitações por ano, divididas por canal" />
              </ChartCard>

              <ChartCard
                title="Situação das solicitações"
                sub="Em aberto = aberto, aberta, em andamento ou em aprovação."
                tools={<button type="button" className="vbtn" aria-pressed={status100} onClick={() => setStatus100(!status100)}>{status100 ? '% do ano' : 'Volume'}</button>}
                table={tableFromRows(sit.rows, sit.keys)}>
                <StackedBars rows={sit.rows} keys={sit.keys} percent={status100} label="Situação das solicitações por ano" />
              </ChartCard>
            </div>

            <ChartCard
              title="Sazonalidade: ano × mês"
              sub="Cor mais escura = mais solicitações no mês."
              table={{columns: [{key: 'row', label: 'Ano'}, {key: 'col', label: 'Mês', num: true}, {key: 'v', label: 'Solicitações', num: true, fmt: fmt}], rows: cells}}>
              <HeatMatrix cells={cells} rowKeys={anos} label="Matriz de solicitações por ano e mês" />
            </ChartCard>

            <ChartCard title="Anos em números" table={{
              columns: [{key: 'ano', label: 'Ano'}, {key: 'n', label: 'Solicitações', num: true, fmt: fmt},
                {key: 'pct_coordenada', label: '% com coordenada', num: true, fmt: fmt1},
                {key: 'pct_finalizada', label: '% finalizadas', num: true, fmt: fmt1},
                {key: 'prazo_mediano', label: 'Prazo mediano (dias)', num: true, fmt: (v) => (v == null ? 'n/d' : fmt1(v))}],
              rows: anual}}
            sub="A tabela completa por ano. Use o botão ao lado para alternar." >
              <HBars items={anual.map((a) => ({label: String(a.ano), value: a.n, sub: `${fmt1(a.pct_coordenada)}% com coordenada`}))} label="Solicitações por ano" />
            </ChartCard>
          </>
        );
      }}
    </Data>
  );
}

/* =============================================================== temas e serviços */
export function TemasPanel() {
  const [n, setN] = useState('15');
  return (
    <Data name={['tema_ano', 'servicos_top']}>
      {(temaAno, servicos) => {
        const tp = pivot(temaAno, 'ano', 'tema', 'n', 7);
        const items = servicos.slice(0, +n).map((s) => ({
          label: s.servico, value: s.n, sub: `${s.tema} · ${s.desde === s.ate ? s.desde : `${s.desde}–${s.ate}`}`,
        }));
        return (
          <>
            <ChartCard title="Temas por ano" sub="Os 7 temas mais frequentes; o resto entra em Outros."
              note="Em 2020 e 2021, Cidadania e assistência social passa de 900 mil e 1,3 milhão de solicitações, puxada pelo serviço de consulta da Renda Básica Emergencial."
              table={tableFromRows(tp.rows, tp.keys)}>
              <StackedBars rows={tp.rows} keys={tp.keys} height={340} label="Solicitações por ano, divididas por tema" />
            </ChartCard>
            <ChartCard title="Serviços mais solicitados (2015–2026)"
              sub="Acumulado de todos os anos. O período de existência de cada serviço aparece ao passar o cursor."
              tools={<Select label="Mostrar" value={n} onChange={setN} options={[{value: '10', label: '10'}, {value: '15', label: '15'}, {value: '30', label: '30'}]} />}
              note="Vários dos serviços maiores são consultas (por exemplo, consultar benefício ou situação), e não pedidos de obra ou zeladoria."
              table={{columns: [{key: 'servico', label: 'Serviço'}, {key: 'tema', label: 'Tema'}, {key: 'n', label: 'Solicitações', num: true, fmt: fmt}, {key: 'desde', label: 'Desde'}, {key: 'ate', label: 'Até'}], rows: servicos}}>
              <HBars items={items} rowH={30} label="Serviços mais solicitados" />
            </ChartCard>
          </>
        );
      }}
    </Data>
  );
}

/* =============================================================== território */
export function TerritorioPanel() {
  const [ano, setAno] = useState('all');
  const [tema, setTema] = useState('Todos os temas');
  const [top, setTop] = useState('15');
  return (
    <Data name={['distritos', 'distritos_geo', 'grade', 'overview']}>
      {(distritos, geo, grade, ov) => {
        const val = (d) => (ano === 'all' ? d.total : d.anos[ano] || 0);
        const rank = [...distritos].sort((a, b) => val(b) - val(a)).slice(0, +top)
          .map((d) => ({label: d.distrito, value: val(d)}));
        const anos = ['all', ...Array.from({length: 12}, (_, i) => String(2015 + i))];
        return (
          <>
            <Kpis items={[
              {label: 'Com distrito identificado', value: pct(ov.pct_distrito_final), note: 'declarado, ou obtido pela coordenada'},
              {label: 'Distritos no mapa', value: '96'},
              {label: 'Célula do mapa de calor', value: '500 m', note: `células com menos de ${grade.k_min} solicitações são ocultadas`},
            ]} />
            <div className="callout-caveat">
              <b>Leia com cuidado:</b> os mapas mostram <b>contagens</b>, não taxas. Distritos mais populosos ou maiores acumulam mais
              solicitações. Não há normalização por população nesta versão.
            </div>
            <ChartCard title="Solicitações por distrito"
              sub="Cinco faixas por quantis (20% dos distritos em cada faixa)."
              tools={<Select label="Ano" value={ano} onChange={setAno} options={anos.map((a) => ({value: a, label: a === 'all' ? 'Todos' : a}))} />}
              note="O distrito vem da coluna da fonte; quando ela falta, é obtido cruzando a coordenada com os polígonos oficiais do GeoSampa. Cerca de 95% a 98% dos distritos declarados coincidem com o geográfico (as diferenças são pontos de borda)."
              table={{columns: [{key: 'distrito', label: 'Distrito'}, {key: 'v', label: 'Solicitações', num: true, fmt: fmt}], rows: [...distritos].sort((a, b) => val(b) - val(a)).map((d) => ({distrito: d.distrito, v: val(d)}))}}>
              <DistrictMap geo={geo} distritos={distritos} year={ano} />
            </ChartCard>
            <ChartCard title="Ranking de distritos"
              tools={<Select label="Mostrar" value={top} onChange={setTop} options={[{value: '10', label: 'Top 10'}, {value: '15', label: 'Top 15'}, {value: '25', label: 'Top 25'}]} />}>
              <HBars items={rank} label="Distritos com mais solicitações" />
            </ChartCard>
            <ChartCard title="Mapa de calor em células de 500 m"
              sub="Onde as solicitações com coordenada se concentram, de 2015 a 2026."
              tools={<Select label="Tema" value={tema} onChange={setTema} options={grade.temas.map((t) => ({value: t, label: t}))} />}>
              <GridMap grid={grade} tema={tema} geo={geo} />
            </ChartCard>
          </>
        );
      }}
    </Data>
  );
}

/* =============================================================== desempenho */
const METRICS = {
  n: {label: 'Volume', fmt: fmtCompact},
  pct_finalizada: {label: '% finalizadas', fmt: (v) => `${fmt1(v)}%`},
  prazo_mediano: {label: 'Prazo mediano (dias)', fmt: (v) => fmt1(v)},
  prazo_p90: {label: 'Prazo p90 (dias)', fmt: (v) => fmt1(v)},
};

export function DesempenhoPanel() {
  const [mo, setMo] = useState('n');
  const [mt, setMt] = useState('prazo_mediano');
  return (
    <Data name={['orgaos_top', 'tema_desempenho', 'prazo_faixas_ano']}>
      {(orgaos, temas, faixas) => {
        const m = METRICS[mo];
        const oi = [...orgaos].filter((o) => o[mo] != null).sort((a, b) => b[mo] - a[mo]).slice(0, 15)
          .map((o) => ({label: o.orgao, value: o[mo], sub: `${fmt(o.n)} solicitações · ${fmt1(o.pct_finalizada)}% finalizadas · prazo mediano ${fmt1(o.prazo_mediano)} d`}));
        const t = METRICS[mt];
        const ti = [...temas].slice(0, 15).sort((a, b) => b[mt] - a[mt])
          .map((x) => ({label: x.tema, value: x[mt], sub: `${fmt(x.n)} solicitações desde 2020`}));
        const fx = pivot(faixas, 'ano', 'faixa', 'n', 7);
        const ordem = ['0 (mesmo dia)', '1 dia', '2 a 3 dias', '4 a 7 dias', '8 a 15 dias', '16 a 30 dias', 'mais de 30 dias'];
        fx.keys = ordem.filter((k) => fx.keys.includes(k));
        const cmap = Object.fromEntries(fx.keys.map((k, i) => [k, `color-mix(in oklab, var(--seq-100), var(--seq-700) ${Math.round((i / (fx.keys.length - 1)) * 100)}%)`]));
        return (
          <>
            <div className="callout-caveat">
              <b>Prazo só vale a partir de 2020.</b> Antes disso, "Data do Parecer" não é a data de finalização (em 2015, 100% dos prazos são zero),
              então todas as métricas de prazo usam apenas 2020 em diante. Prazo = dias de calendário entre abertura e finalização.
            </div>
            <ChartCard title="Órgãos e origens com mais solicitações (2020+)"
              sub="Entre os 25 maiores por volume. Escolha a métrica para reordenar."
              tools={<Select label="Ordenar por" value={mo} onChange={setMo} options={Object.entries(METRICS).map(([v, x]) => ({value: v, label: x.label}))} />}
              note="Origens com prazo longo e baixa finalização, como INTEGRACAO-SGF, merecem investigação antes de qualquer conclusão: a natureza do serviço pode explicar a diferença."
              table={{columns: [{key: 'orgao', label: 'Órgão'}, {key: 'n', label: 'Solicitações', num: true, fmt: fmt}, {key: 'pct_finalizada', label: '% finalizadas', num: true, fmt: fmt1}, {key: 'prazo_mediano', label: 'Mediana (d)', num: true, fmt: fmt1}, {key: 'prazo_p90', label: 'p90 (d)', num: true, fmt: fmt1}], rows: orgaos}}>
              <HBars items={oi} valueFmt={m.fmt} rowH={30} label={`Órgãos por ${m.label}`} />
            </ChartCard>
            <ChartCard title="Temas: prazo e finalização (2020+)"
              sub="Os 15 temas mais frequentes."
              tools={<Select label="Métrica" value={mt} onChange={setMt} options={Object.entries(METRICS).map(([v, x]) => ({value: v, label: x.label}))} />}
              table={{columns: [{key: 'tema', label: 'Tema'}, {key: 'n', label: 'Solicitações', num: true, fmt: fmt}, {key: 'pct_finalizada', label: '% finalizadas', num: true, fmt: fmt1}, {key: 'prazo_mediano', label: 'Mediana (d)', num: true, fmt: fmt1}, {key: 'prazo_p90', label: 'p90 (d)', num: true, fmt: fmt1}], rows: temas}}>
              <HBars items={ti} valueFmt={t.fmt} color="var(--series-3)" label={`Temas por ${t.label}`} />
            </ChartCard>
            <ChartCard title="Quanto tempo leva? Faixas de prazo por ano"
              sub="Parcela das solicitações finalizadas em cada faixa. Mais escuro = mais demorado."
              table={tableFromRows(fx.rows, fx.keys)}>
              <StackedBars rows={fx.rows} keys={fx.keys} percent colors={cmap} label="Faixas de prazo por ano" />
            </ChartCard>
          </>
        );
      }}
    </Data>
  );
}

/* =============================================================== qualidade */
const ticksPeriodo = (data, x) => data.map((d, i) => [i, d[x].slice(0, 4)]).filter(([i]) => data[i][x].endsWith('T1') || data[i][x].endsWith('S1'));

export function QualidadePanel() {
  return (
    <Data name={['qualidade_periodo', 'qualidade_distrito', 'overview']}>
      {(qp, qd, ov) => {
        const dist = qd.map((r) => ({ano: String(r.ano), pct: (100 * r.coincidem) / r.com_distrito_declarado}));
        const cols = [
          {key: 'periodo', label: 'Período'}, {key: 'linhas', label: 'Linhas', num: true, fmt: fmt},
          {key: 'pct_com_coordenada', label: '% coordenada', num: true, fmt: fmt1},
          {key: 'pct_com_distrito', label: '% distrito', num: true, fmt: fmt1},
          {key: 'pct_com_finalizacao', label: '% finalização', num: true, fmt: fmt1},
          {key: 'finalizacao_antes_abertura', label: 'Final. antes da abertura', num: true, fmt: fmt},
        ];
        return (
          <>
            <Kpis items={[
              {label: 'Períodos validados', value: String(qp.length), note: 'regras de qualidade bloqueiam o pipeline se falharem'},
              {label: 'Linhas na silver', value: fmtCompact(ov.total), note: 'após remover 125.482 duplicadas entre arquivos'},
              {label: 'Com coordenada', value: pct(ov.pct_coordenada)},
            ]} />
            <div className="grid2">
              <ChartCard title="Cobertura de coordenada, por período" sub="% de solicitações com latitude/longitude válidas dentro do município."
                note="2022T3 não traz latitude/longitude na fonte. A queda em 2020–2021 coincide com o aumento de serviços de consulta (por exemplo, SMADS-CGB-Consultas), cujas linhas vêm sem endereço."
                table={{columns: cols, rows: qp}}>
                <LineChart data={qp} x="periodo" y="pct_com_coordenada" yMax={100} yFmt={(v) => `${Math.round(v)}%`} xFmt={(v) => v} ticksFn={ticksPeriodo} peak={false} label="Percentual de solicitações com coordenada por período" />
              </ChartCard>
              <ChartCard title="Cobertura de distrito, por período" sub="% com a coluna distrito preenchida na fonte (antes do cruzamento geográfico)."
                note="2017T4 traz Bairro no lugar de Distrito. Desde 2025T2 parte das linhas traz o código numérico do distrito, traduzido pelo campo cd_distrito_municipal do GeoSampa (coincidência de 100%)."
                table={{columns: cols, rows: qp}}>
                <LineChart data={qp} x="periodo" y="pct_com_distrito" yMax={100} color="var(--series-2)" yFmt={(v) => `${Math.round(v)}%`} xFmt={(v) => v} ticksFn={ticksPeriodo} peak={false} label="Percentual de solicitações com distrito por período" />
              </ChartCard>
              <ChartCard title="Cobertura de data de finalização, por período" sub="% com data de finalização preenchida."
                table={{columns: cols, rows: qp}}>
                <LineChart data={qp} x="periodo" y="pct_com_finalizacao" yMax={100} color="var(--series-3)" yFmt={(v) => `${Math.round(v)}%`} xFmt={(v) => v} ticksFn={ticksPeriodo} peak={false} label="Percentual de solicitações com data de finalização por período" />
              </ChartCard>
              <ChartCard title="Distrito declarado × geográfico" sub="% das linhas em que o distrito da fonte é o mesmo da coordenada."
                note="As divergências são vizinhos reais (Jaçanã/Tremembé, Sé/República, Santana/Pari): pontos de borda ou geocodificação no nível da rua, e não diferença de grafia."
                table={{columns: [{key: 'ano', label: 'Ano'}, {key: 'pct', label: '% coincidem', num: true, fmt: fmt1}], rows: dist}}>
                <LineChart data={dist} x="ano" y="pct" yMax={100} color="var(--series-7)" yFmt={(v) => `${Math.round(v)}%`} xFmt={(v) => v} ticksFn={(d, x) => d.map((r, i) => [i, r[x]])} peak={false} label="Percentual de coincidência entre distrito declarado e geográfico por ano" />
              </ChartCard>
            </div>
            <ChartCard title="Linhas por período" sub="Tamanho de cada arquivo trimestral após o tratamento. Use Ver tabela para todas as métricas de qualidade." table={{columns: cols, rows: qp}}>
              <LineChart data={qp} x="periodo" y="linhas" xFmt={(v) => v} ticksFn={ticksPeriodo} label="Linhas por período" />
            </ChartCard>
          </>
        );
      }}
    </Data>
  );
}

/* =============================================================== reativação de abrigos */
const SIT_COLOR = {FINALIZADA: '--series-1', 'AGUARDANDO ATENDIMENTO': '--series-2', CANCELADA: '--series-other'};

export function ReativacaoPanel() {
  return (
    <Data name={['reativacao', 'sac_camadas', 'distritos_geo']}>
      {(r, camadas, geo) => {
        const meses = r.por_mes.map((m) => ({x: fmtYm(m.ym), values: {Solicitações: m.n}}));
        const ALVO = 'sac_reativacao_abrigo_ponto_extinto';
        const pos = camadas.findIndex((c) => c.nome === ALVO) + 1;
        const cs = camadas.slice(0, 15).map((c) => ({label: c.titulo, value: c.n, sub: c.nome}));
        cs.push({label: `… ${camadas[pos - 1].titulo} (${pos}ª)`, value: camadas[pos - 1].n, sub: ALVO, color: 'var(--series-2)'});
        const fin = (r.situacao.find((s) => s.situacao === 'FINALIZADA') || {n: 0}).n;
        return (
          <>
            <Kpis items={[
              {label: 'Solicitações na camada', value: String(r.total), note: 'abril a setembro de 2020'},
              {label: 'Finalizadas', value: `${fin} (${Math.round((100 * fin) / r.total)}%)`},
              {label: 'Prazo mediano', value: `${fmt1(r.prazo_mediano_dias)} dias`, note: 'abertura até parecer (2020)'},
              {label: 'Posição entre as 94 camadas sac_*', value: `${pos}ª de 94`, note: 'por volume'},
            ]} />
            <div className="callout-caveat">
              <b>Camada desatualizada na fonte.</b> O metadado promete "últimos 6 meses", mas todas as camadas sac_* do GeoSampa têm carga de
              2021-03-25 e aberturas de abril a setembro de 2020. Por isso, este painel é um retrato de 2020, e não da situação atual.
            </div>
            <div className="grid2">
              <ChartCard title="Onde foram pedidas" sub="Cada ponto é uma solicitação georreferenciada (sem endereço).">
                <PointMap points={r.pontos} colors={SIT_COLOR} geo={geo} />
                <div className="vlegend">{Object.entries(SIT_COLOR).map(([k, v]) => <span key={k}><i style={{background: `var(${v})`}} />{k.toLowerCase()}</span>)}</div>
              </ChartCard>
              <div>
                <ChartCard title="Abertas por mês" table={tableFromRows(meses, ['Solicitações'])}>
                  <StackedBars rows={meses} keys={['Solicitações']} height={220} label="Solicitações de reativação por mês de abertura" />
                </ChartCard>
                <ChartCard title="Situação">
                  <HBars items={r.situacao.map((s) => ({label: s.situacao.toLowerCase(), value: s.n, color: `var(${SIT_COLOR[s.situacao] || '--series-other'})`}))} valueFmt={(v) => String(v)} rowH={26} label="Situação das solicitações" />
                </ChartCard>
                <ChartCard title="Canal de atendimento">
                  <HBars items={r.canal.map((s) => ({label: s.canal.toLowerCase(), value: s.n}))} valueFmt={(v) => String(v)} rowH={26} label="Canal das solicitações" />
                </ChartCard>
              </div>
            </div>
            <ChartCard title="Contexto: as 15 maiores camadas SP156 do GeoSampa"
              sub={`A camada de reativação (em laranja, na última linha) fica na ${pos}ª posição de ${camadas.length} por volume.`}
              table={{columns: [{key: 'titulo', label: 'Camada'}, {key: 'nome', label: 'Nome técnico'}, {key: 'n', label: 'Solicitações', num: true, fmt: fmt}], rows: camadas}}>
              <HBars items={cs} rowH={30} label="Maiores camadas SP156 do GeoSampa" />
            </ChartCard>
          </>
        );
      }}
    </Data>
  );
}
