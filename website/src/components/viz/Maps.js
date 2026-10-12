import React, {useEffect, useMemo, useRef, useState} from 'react';
import 'leaflet/dist/leaflet.css';
import {fmt, fmtCompact} from './data';

const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
function useTheme() {
  const [t, setT] = useState('light');
  useEffect(() => {
    const read = () => setT(document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light');
    read();
    const mo = new MutationObserver(read);
    mo.observe(document.documentElement, {attributes: true, attributeFilter: ['data-theme']});
    return () => mo.disconnect();
  }, []);
  return t;
}

/** Cria o mapa Leaflet uma vez (import dinâmico: Leaflet toca em `window`). Sem tiles de terceiros:
 *  o contexto geográfico vem do contorno dos distritos (nada é requisitado de fora). */
function useLeaflet(ref) {
  const [ctx, setCtx] = useState(null);
  useEffect(() => {
    let map; let off = false;
    import('leaflet').then((mod) => {
      if (off || !ref.current) return;
      const L = mod.default || mod;
      map = L.map(ref.current, {scrollWheelZoom: false, attributionControl: true, zoomSnap: 0.25}).setView([-23.6, -46.63], 10);
      map.attributionControl.setPrefix('<a href="https://leafletjs.com">Leaflet</a>');
      map.attributionControl.addAttribution('Dados: Prefeitura de São Paulo / GeoSampa');
      map.on('focus', () => map.scrollWheelZoom.enable());
      map.on('blur', () => map.scrollWheelZoom.disable());
      setCtx({L, map});
    });
    return () => { off = true; if (map) map.remove(); setCtx(null); };
  }, []);
  return ctx;
}

/** Contorno dos distritos como referência visual (não interativo). */
function useOutline(ctx, geo, theme) {
  useEffect(() => {
    if (!ctx || !geo) return undefined;
    const layer = ctx.L.geoJSON(geo, {interactive: false, style: {fill: false, color: css('--viz-axis'), weight: 1}}).addTo(ctx.map);
    return () => layer.remove();
  }, [ctx, geo, theme]);
}

function quantileBreaks(values, qs) {
  const v = [...values].sort((a, b) => a - b);
  return qs.map((q) => v[Math.min(v.length - 1, Math.floor(q * v.length))]);
}
const classOf = (x, br) => br.filter((b) => x > b).length;
const RAMP = ['--seq-100', '--seq-200', '--seq-300', '--seq-500', '--seq-700'];

function ScaleLegend({breaks, unit = ''}) {
  const edges = [0, ...breaks];
  return (
    <div className="vlegend" aria-label="Legenda do mapa">
      {RAMP.map((v, i) => (
        <span key={v}><i style={{background: `var(${v})`}} />
          {i === 0 ? `até ${fmtCompact(breaks[0])}` : i === RAMP.length - 1 ? `acima de ${fmtCompact(breaks[breaks.length - 1])}` : `${fmtCompact(edges[i])} a ${fmtCompact(breaks[i])}`}{unit}
        </span>
      ))}
    </div>
  );
}

/* ---------------------------------------------------------------- coroplético por distrito */
export function DistrictMap({geo, distritos, year}) {
  const ref = useRef(null);
  const theme = useTheme();
  const ctx = useLeaflet(ref);
  const values = useMemo(() => {
    const m = {};
    distritos.forEach((d) => { m[d.distrito] = year === 'all' ? d.total : d.anos[year] || 0; });
    return m;
  }, [distritos, year]);
  const breaks = useMemo(() => quantileBreaks(Object.values(values).filter((x) => x > 0), [0.2, 0.4, 0.6, 0.8]), [values]);
  useEffect(() => {
    if (!ctx) return undefined;
    const {L, map} = ctx;
    const layer = L.geoJSON(geo, {
      style: (f) => {
        const v = values[f.properties.nome] || 0;
        return {fillColor: css(RAMP[classOf(v, breaks)]), fillOpacity: 0.88, color: css('--viz-surface'), weight: 1};
      },
      onEachFeature: (f, l) => {
        const v = values[f.properties.nome] || 0;
        l.bindTooltip(`<b>${f.properties.nome}</b><br>${fmt(v)} solicitações`, {sticky: true});
        l.on('mouseover', () => l.setStyle({weight: 2.5, color: css('--viz-ink')}));
        l.on('mouseout', () => layer.resetStyle(l));
      },
    }).addTo(map);
    map.fitBounds(layer.getBounds(), {padding: [10, 10]});
    return () => layer.remove();
  }, [ctx, geo, values, breaks, theme]);
  return (
    <>
      <div className="vmap" ref={ref} role="application" aria-label="Mapa de solicitações por distrito" tabIndex={0} />
      <ScaleLegend breaks={breaks} />
    </>
  );
}

/* ---------------------------------------------------------------- grade de calor 500 m */
export function GridMap({grid, tema, geo}) {
  const ref = useRef(null);
  const theme = useTheme();
  const ctx = useLeaflet(ref);
  useOutline(ctx, geo, theme);
  // grade.json: "pontos" [[lat, lon], ...] e "n" {tema: [n por ponto]}, 0 = célula oculta
  const cells = useMemo(() => {
    const ns = grid.n[tema] || [];
    const out = [];
    grid.pontos.forEach(([lat, lon], i) => { if (ns[i]) out.push([lat, lon, ns[i]]); });
    return out;
  }, [grid, tema]);
  const breaks = useMemo(() => quantileBreaks(cells.map((c) => c[2]), [0.4, 0.7, 0.9, 0.98]), [cells]);
  useEffect(() => {
    if (!ctx) return undefined;
    const {L, map} = ctx;
    const dLat = 0.5 / 111.32 / 2; // meia célula de 500 m, em graus
    const dLon = dLat / Math.cos((23.55 * Math.PI) / 180);
    const renderer = L.canvas({padding: 0.5});
    const group = L.layerGroup().addTo(map);
    cells.forEach(([lat, lon, n]) => {
      const r = L.rectangle([[lat - dLat, lon - dLon], [lat + dLat, lon + dLon]], {
        renderer, stroke: false, fillColor: css(RAMP[classOf(n, breaks)]), fillOpacity: 0.82,
      }).addTo(group);
      r.on('mouseover', (e) => e.target.bindTooltip(`${fmt(n)} solicitações`).openTooltip(e.latlng));
    });
    map.setView([-23.6, -46.63], 10);
    return () => group.remove();
  }, [ctx, cells, breaks, theme]);
  return (
    <>
      <div className="vmap" ref={ref} role="application" aria-label="Mapa de calor em células de 500 metros" tabIndex={0} />
      <ScaleLegend breaks={breaks} />
    </>
  );
}

/* ---------------------------------------------------------------- pontos (camada pequena) */
export function PointMap({points, colors, geo}) {
  const ref = useRef(null);
  const theme = useTheme();
  const ctx = useLeaflet(ref);
  useOutline(ctx, geo, theme);
  useEffect(() => {
    if (!ctx) return undefined;
    const {L, map} = ctx;
    const group = L.layerGroup().addTo(map);
    points.forEach(([lat, lon, ym, situacao]) => {
      L.circleMarker([lat, lon], {
        radius: 7, weight: 2, color: css('--viz-surface'), fillOpacity: 0.95, fillColor: css(colors[situacao] || '--series-other'),
      }).bindTooltip(`${situacao}<br>aberta em ${ym}`).addTo(group);
    });
    map.fitBounds(L.latLngBounds(points.map((p) => [p[0], p[1]])), {padding: [40, 40], maxZoom: 12});
    return () => group.remove();
  }, [ctx, points, theme]);
  return <div className="vmap" ref={ref} role="application" aria-label="Mapa das solicitações de reativação" tabIndex={0} />;
}
