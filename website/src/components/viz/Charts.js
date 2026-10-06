import React, {useEffect, useRef, useState} from 'react';
import {fmt, fmtCompact, fmtYm, mesAbrev} from './data';

export function useWidth(def = 640) {
  const ref = useRef(null);
  const [w, setW] = useState(def);
  useEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    const set = (v) => { const r = Math.round(v); if (r > 0) setW(r); };
    set(el.getBoundingClientRect().width);
    const ro = new ResizeObserver((e) => set(e[0].contentRect.width));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, w];
}

/** Passo "bonito" (1, 2, 2,5, 5 × 10^k) e teto múltiplo do passo: 2,9 mi vira 3 mi com marcas de 1 mi. */
function niceScale(v, n = 4) {
  if (v <= 0) return {max: 1, step: 0.25};
  const raw = v / n;
  const p = 10 ** Math.floor(Math.log10(raw));
  const f = raw / p;
  const step = (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * p;
  return {max: step * Math.ceil(v / step - 1e-9), step};
}
const niceMax = (v) => niceScale(v).max;
const ticksOf = (v) => { const {max, step} = niceScale(v); return Array.from({length: Math.round(max / step) + 1}, (_, i) => i * step); };

const slot = (i) => `var(--series-${(i % 8) + 1})`;
/** Cor segue a entidade (chave), nunca o ranking: "Outros"/"Sem ..." ficam em cinza. */
export function colorFor(key, keys) {
  if (/^(outros|sem )/i.test(key) || key === 'SEM CANAL') return 'var(--series-other)';
  return slot(keys.filter((k) => !/^(outros|sem )/i.test(k) && k !== 'SEM CANAL').indexOf(key));
}

function Tip({x, y, children}) {
  return <div className="vtip" style={{left: x, top: y}}>{children}</div>;
}

export function Legend({keys, colors}) {
  return (
    <div className="vlegend" role="list">
      {keys.map((k) => <span role="listitem" key={k}><i style={{background: colors[k]}} />{k}</span>)}
    </div>
  );
}

/* ---------------------------------------------------------------- linha (1 série) */
const defaultTicks = (data, x) => {
  const out = [];
  data.forEach((d, i) => { if (String(d[x]).endsWith('-01')) out.push([i, String(d[x]).slice(0, 4)]); });
  return out;
};

export function LineChart({data, x, y, height = 260, yFmt = fmtCompact, xFmt = fmtYm, label, annotations = [],
  color = 'var(--series-1)', ticksFn = defaultTicks, peak: showPeak = true, yMax}) {
  const [ref, w] = useWidth();
  const [hi, setHi] = useState(null);
  const m = {l: 46, r: 14, t: 16, b: 26};
  const iw = w - m.l - m.r;
  const ih = height - m.t - m.b;
  const n = data.length;
  const ymax = yMax || niceMax(Math.max(...data.map((d) => d[y])));
  const yTicks = yMax ? [0, 1, 2, 3, 4].map((t) => (yMax * t) / 4) : ticksOf(Math.max(...data.map((d) => d[y])));
  const X = (i) => m.l + (n === 1 ? 0 : (i * iw) / (n - 1));
  const Y = (v) => m.t + ih - (v / ymax) * ih;
  const path = data.map((d, i) => `${i ? 'L' : 'M'}${X(i).toFixed(1)},${Y(d[y]).toFixed(1)}`).join('');
  const ticks = yTicks;
  const years = ticksFn(data, x);
  const step = w < 560 ? 2 : 1;
  const peak = data.reduce((b, d, i) => (d[y] > data[b][y] ? i : b), 0);
  const onMove = (e) => {
    const r = e.currentTarget.getBoundingClientRect();
    const px = e.clientX - r.left - m.l;
    setHi(Math.max(0, Math.min(n - 1, Math.round((px / iw) * (n - 1)))));
  };
  return (
    <div className="vchart" ref={ref}>
      <svg viewBox={`0 0 ${w} ${height}`} role="img" aria-label={label}
        onPointerMove={onMove} onPointerLeave={() => setHi(null)}>
        {ticks.map((t) => (
          <g key={t}>
            <line className={t === 0 ? 'vaxis' : 'vgrid'} x1={m.l} x2={w - m.r} y1={Y(t)} y2={Y(t)} />
            <text x={m.l - 6} y={Y(t) + 4} textAnchor="end">{yFmt(t)}</text>
          </g>
        ))}
        {years.filter((_, k) => k % step === 0).map(([i, yr]) => (
          <text key={yr} x={X(i)} y={height - 8} textAnchor="middle">{yr}</text>
        ))}
        {annotations.map((a) => {
          const i = data.findIndex((d) => d[x] === a.x);
          return i < 0 ? null : (
            <g key={a.x}>
              <line x1={X(i)} x2={X(i)} y1={m.t} y2={m.t + ih} stroke="var(--viz-axis)" strokeDasharray="3 3" />
              <text className="vlabel" x={X(i) + 4} y={m.t + 10}>{a.text}</text>
            </g>
          );
        })}
        <path d={path} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
        {showPeak && (
          <>
            <circle cx={X(peak)} cy={Y(data[peak][y])} r="4" fill={color} stroke="var(--viz-surface)" strokeWidth="2" />
            <text className="vlabel" x={X(peak)} y={Y(data[peak][y]) - 9} textAnchor={peak > n * 0.85 ? 'end' : 'middle'}>
              pico: {fmtCompact(data[peak][y])}
            </text>
          </>
        )}
        {hi != null && (
          <g>
            <line x1={X(hi)} x2={X(hi)} y1={m.t} y2={m.t + ih} stroke="var(--viz-axis)" />
            <circle cx={X(hi)} cy={Y(data[hi][y])} r="5" fill={color} stroke="var(--viz-surface)" strokeWidth="2" />
          </g>
        )}
      </svg>
      {hi != null && (
        <Tip x={Math.max(70, Math.min(w - 70, X(hi)))} y={Y(data[hi][y])}>
          <b>{xFmt(data[hi][x])}</b><br />{yFmt === fmtCompact ? fmt(data[hi][y]) : yFmt(data[hi][y])}
        </Tip>
      )}
    </div>
  );
}

/* ---------------------------------------------------------------- barras empilhadas */
export function StackedBars({rows, keys, percent = false, height = 300, colors, label, valueFmt = fmtCompact}) {
  const [ref, w] = useWidth();
  const [hi, setHi] = useState(null);
  const cmap = colors || Object.fromEntries(keys.map((k) => [k, colorFor(k, keys)]));
  const m = {l: 46, r: 8, t: 22, b: 26};
  const iw = w - m.l - m.r;
  const ih = height - m.t - m.b;
  const totals = rows.map((r) => keys.reduce((s, k) => s + (r.values[k] || 0), 0));
  const ymax = percent ? 100 : niceMax(Math.max(...totals));
  const band = iw / rows.length;
  const showTotals = !percent && band >= 52;
  const bw = Math.min(56, band * 0.72);
  const Y = (v) => m.t + ih - (v / ymax) * ih;
  const ticks = percent ? [0, 25, 50, 75, 100] : ticksOf(Math.max(...totals));
  return (
    <div className="vchart" ref={ref}>
      {keys.length > 1 && <Legend keys={keys} colors={cmap} />}
      <svg viewBox={`0 0 ${w} ${height}`} role="img" aria-label={label} onPointerLeave={() => setHi(null)}>
        {ticks.map((t) => (
          <g key={t}>
            <line className={t === 0 ? 'vaxis' : 'vgrid'} x1={m.l} x2={w - m.r} y1={Y(t)} y2={Y(t)} />
            <text x={m.l - 6} y={Y(t) + 4} textAnchor="end">{percent ? `${t}%` : valueFmt(t)}</text>
          </g>
        ))}
        {rows.map((r, i) => {
          const cx = m.l + band * i + band / 2;
          const tot = totals[i] || 1;
          let acc = 0;
          const segs = keys.filter((k) => (r.values[k] || 0) > 0);
          return (
            <g key={r.x} onPointerMove={() => setHi(i)} opacity={hi == null || hi === i ? 1 : 0.55}>
              <rect x={cx - band / 2} y={m.t} width={band} height={ih} fill="transparent" />
              {segs.map((k, si) => {
                const v = percent ? (r.values[k] / tot) * 100 : r.values[k];
                const y1 = Y(acc + v);
                const h = Y(acc) - y1;
                acc += v;
                return (
                  <rect key={k} x={cx - bw / 2} y={y1} width={bw} height={Math.max(0, h)} fill={cmap[k]}
                    stroke="var(--viz-surface)" strokeWidth="2" rx={si === segs.length - 1 ? 3 : 0} />
                );
              })}
              {showTotals && <text className="vlabel" x={cx} y={Y(tot) - 6} textAnchor="middle">{valueFmt(tot)}</text>}
              <text x={cx} y={height - 8} textAnchor="middle">{band < 34 && /^\d{4}$/.test(r.x) ? `'${String(r.x).slice(2)}` : r.x}</text>
            </g>
          );
        })}
      </svg>
      {hi != null && (
        <Tip x={Math.max(90, Math.min(w - 90, m.l + band * hi + band / 2))} y={m.t + 24}>
          <b>{rows[hi].x}</b>
          {keys.filter((k) => (rows[hi].values[k] || 0) > 0).map((k) => (
            <div key={k}><i style={{background: cmap[k]}} />{k}: {fmt(rows[hi].values[k])}{' '}
              <span style={{color: 'var(--viz-muted)'}}>({((rows[hi].values[k] / (totals[hi] || 1)) * 100).toFixed(1).replace('.', ',')}%)</span>
            </div>
          ))}
        </Tip>
      )}
    </div>
  );
}

/* ---------------------------------------------------------------- barras horizontais */
export function HBars({items, valueFmt = fmtCompact, color = 'var(--series-1)', label, rowH = 28, extra}) {
  const [ref, w] = useWidth();
  const [hi, setHi] = useState(null);
  const longest = Math.max(...items.map((d) => d.label.length));
  const labelW = Math.min(Math.round(w * 0.46), 250, Math.round(longest * 6.4 + 18));
  const valW = 70;
  const iw = Math.max(40, w - labelW - valW - 8);
  const max = Math.max(...items.map((d) => d.value)) || 1;
  const height = items.length * rowH + 6;
  const chars = Math.floor(labelW / 6.3);
  return (
    <div className="vchart" ref={ref}>
      <svg viewBox={`0 0 ${w} ${height}`} role="img" aria-label={label} onPointerLeave={() => setHi(null)}>
        <line className="vaxis" x1={labelW} x2={labelW} y1={0} y2={height} />
        {items.map((d, i) => {
          const y = i * rowH + 3;
          const bw = Math.max(2, (d.value / max) * iw);
          const t = d.label.length > chars ? `${d.label.slice(0, chars - 1)}…` : d.label;
          return (
            <g key={d.label + i} onPointerMove={() => setHi(i)} opacity={hi == null || hi === i ? 1 : 0.55}>
              <rect x={0} y={y} width={w} height={rowH} fill="transparent" />
              <text className="vlabel" x={labelW - 8} y={y + rowH / 2 + 4} textAnchor="end">{t}</text>
              <rect x={labelW} y={y + 5} width={bw} height={rowH - 12} rx="4" fill={d.color || color} />
              <text className="vlabel" x={labelW + bw + 6} y={y + rowH / 2 + 4}>{valueFmt(d.value)}</text>
            </g>
          );
        })}
      </svg>
      {hi != null && (
        <Tip x={Math.min(w - 110, labelW + 100)} y={hi * rowH + 3}>
          <b>{items[hi].label}</b><br />{fmt(items[hi].value)}{items[hi].sub ? <><br />{items[hi].sub}</> : null}
        </Tip>
      )}
      {extra}
    </div>
  );
}

/* ---------------------------------------------------------------- matriz de calor (ano × mês) */
export function HeatMatrix({cells, rowKeys, label}) {
  const [ref, w] = useWidth();
  const [hi, setHi] = useState(null);
  const lw = 40;
  const cw = (w - lw) / 12;
  const ch = Math.min(26, cw * 0.62);
  const height = rowKeys.length * ch + 24;
  const vals = cells.map((c) => c.v).sort((a, b) => a - b);
  const trueMax = vals[vals.length - 1];
  const max = vals[Math.floor(vals.length * 0.95)] || trueMax; // p95: um mês extremo não apaga o resto
  const byKey = Object.fromEntries(cells.map((c) => [`${c.row}-${c.col}`, c]));
  return (
    <div className="vchart" ref={ref}>
      <svg viewBox={`0 0 ${w} ${height}`} role="img" aria-label={label} onPointerLeave={() => setHi(null)}>
        {mesAbrev.map((mm, j) => <text key={mm} x={lw + cw * j + cw / 2} y={12} textAnchor="middle">{mm}</text>)}
        {rowKeys.map((r, i) => (
          <g key={r}>
            <text x={lw - 6} y={24 + i * ch + ch / 2 + 4} textAnchor="end">{r}</text>
            {Array.from({length: 12}, (_, j) => {
              const c = byKey[`${r}-${j + 1}`];
              const t = c ? Math.round(Math.min(1, c.v / max) * 100) : 0;
              return (
                <rect key={j} x={lw + cw * j + 1} y={24 + i * ch + 1} width={cw - 2} height={ch - 2} rx="3"
                  fill={c ? `color-mix(in oklab, var(--seq-100), var(--seq-700) ${t}%)` : 'transparent'}
                  stroke={c ? 'none' : 'var(--viz-grid)'} onPointerMove={() => c && setHi({c, i, j})} />
              );
            })}
          </g>
        ))}
      </svg>
      {hi && (
        <Tip x={Math.max(60, Math.min(w - 60, lw + cw * hi.j + cw / 2))} y={24 + hi.i * ch}>
          <b>{mesAbrev[hi.c.col - 1]}/{hi.c.row}</b><br />{fmt(hi.c.v)}
        </Tip>
      )}
      <div className="vscale"><span>menos</span><span className="vscale__bar" /><span>mais (a escala termina em {fmtCompact(max)}; meses acima disso têm a cor mais escura)</span></div>
    </div>
  );
}
