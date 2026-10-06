import React, {useState} from 'react';

/** Cartão de gráfico: título, subtítulo, controles e alternância gráfico/tabela (acessibilidade). */
export default function ChartCard({title, sub, note, tools, table, children}) {
  const [showTable, setShowTable] = useState(false);
  return (
    <section className="vcard" aria-label={title}>
      <div className="vcard__head">
        <div>
          <h3 className="vcard__title">{title}</h3>
          {sub && <p className="vcard__sub">{sub}</p>}
        </div>
        <div className="vcard__tools">
          {tools}
          {table && (
            <button type="button" className="vbtn" aria-pressed={showTable} onClick={() => setShowTable(!showTable)}>
              {showTable ? 'Ver gráfico' : 'Ver tabela'}
            </button>
          )}
        </div>
      </div>
      {showTable && table ? (
        <div className="vcard__table">
          <table>
            <thead><tr>{table.columns.map((c) => <th key={c.key} style={{textAlign: c.num ? 'right' : 'left'}}>{c.label}</th>)}</tr></thead>
            <tbody>
              {table.rows.map((r, i) => (
                <tr key={i}>{table.columns.map((c) => (
                  <td key={c.key} style={{textAlign: c.num ? 'right' : 'left'}}>{c.fmt ? c.fmt(r[c.key], r) : r[c.key]}</td>))}
                </tr>))}
            </tbody>
          </table>
        </div>
      ) : children}
      {note && <p className="vcard__note">{note}</p>}
    </section>
  );
}

export function Kpis({items}) {
  return (
    <div className="kpis">
      {items.map((k) => (
        <div className="kpi" key={k.label}>
          <div className="kpi__label">{k.label}</div>
          <div className="kpi__value">{k.value}</div>
          {k.note && <div className="kpi__note">{k.note}</div>}
        </div>
      ))}
    </div>
  );
}
