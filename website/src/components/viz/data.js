import React, {useEffect, useState} from 'react';
import useBaseUrl from '@docusaurus/useBaseUrl';

const cache = {};

/** Carrega /data/<name>.json (gerado por scripts/export_site_data.py). Vários nomes de uma vez. */
export function useDatas(names) {
  const base = useBaseUrl('/data/');
  const key = names.join('|');
  const [state, setState] = useState(() =>
    names.every((n) => cache[n]) ? {data: names.map((n) => cache[n])} : {});
  useEffect(() => {
    if (names.every((n) => cache[n])) {
      setState({data: names.map((n) => cache[n])});
      return undefined;
    }
    let off = false;
    Promise.all(names.map((n) => cache[n]
      ? Promise.resolve(cache[n])
      : fetch(`${base}${n}.json`).then((r) => {
        if (!r.ok) throw new Error(`${n}: HTTP ${r.status}`);
        return r.json();
      }).then((d) => { cache[n] = d; return d; })))
      .then((data) => !off && setState({data}))
      .catch((e) => !off && setState({error: String(e.message || e)}));
    return () => { off = true; };
  }, [key, base]);
  return state;
}

/** <Data name="mensal">{(mensal) => ...}</Data>  ou  <Data name={['a','b']}>{(a, b) => ...}</Data> */
export function Data({name, children}) {
  const names = Array.isArray(name) ? name : [name];
  const {data, error} = useDatas(names);
  if (error) return <div className="vstatus" role="alert">Não foi possível carregar os dados ({error}).</div>;
  if (!data) return <div className="vstatus" role="status">Carregando…</div>;
  return children(...data);
}

export const fmt = (n) => (n == null ? '–' : new Intl.NumberFormat('pt-BR').format(n));
export const fmt1 = (n) => (n == null ? '–' : new Intl.NumberFormat('pt-BR', {maximumFractionDigits: 1}).format(n));
export const fmtCompact = (n) => {
  if (n == null) return '–';
  const a = Math.abs(n);
  if (a >= 1e6) return `${(n / 1e6).toFixed(1).replace('.', ',')} mi`;
  if (a >= 1e3) return `${(n / 1e3).toFixed(a >= 1e4 ? 0 : 1).replace('.', ',')} mil`;
  return String(Math.round(n));
};
export const pct = (n) => (n == null ? '–' : `${fmt1(n)}%`);
const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
export const mesAbrev = MESES;
export const fmtYm = (ym) => { const [y, m] = ym.split('-'); return `${MESES[+m - 1]}/${y}`; };
