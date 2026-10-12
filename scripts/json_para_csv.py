"""Converte os JSON agregados do site em CSV para download (página "Baixe os dados").

Lê website/static/data/*.json e escreve website/static/data/csv/<nome>.csv:
UTF-8 com BOM (o Excel em português abre os acentos certo), separador vírgula,
ponto como separador decimal, célula vazia para valor ausente. A saída é determinística:
mesma entrada, mesmos bytes.

Também escreve website/static/data/csv_indice.json com o número de linhas de cada CSV,
que a página "Baixe os dados" lê no build.

Uso: python scripts/json_para_csv.py
English: converts the site's aggregated JSON files into CSV downloads.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "website" / "static" / "data"
OUT = DATA / "csv"
INDICE = DATA / "csv_indice.json"

# Não tabulares: polígonos dos distritos (GeoJSON) e o próprio índice gerado aqui.
PULAR = {
    "distritos_geo": "GeoJSON com os polígonos dos distritos; não é tabela",
    "csv_indice": "índice gerado por este script",
}


def _cel(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return str(v)


def _plano(d: dict, prefixo: str = "") -> list[tuple[str, object]]:
    """Achata um dict em pares (indicador, valor); listas de escalares viram texto com ' | '."""
    out = []
    for k, v in d.items():
        chave = f"{prefixo}{k}"
        if isinstance(v, dict):
            out += _plano(v, chave + ".")
        elif isinstance(v, list) and all(not isinstance(x, (dict, list)) for x in v):
            out.append((chave, " | ".join(_cel(x) for x in v)))
        else:
            out.append((chave, v))
    return out


def _registros(lista: list[dict]) -> tuple[list[str], list[list]]:
    cols: list[str] = []
    for r in lista:
        for k in r:
            if k not in cols:
                cols.append(k)
    return cols, [[r.get(c) for c in cols] for r in lista]


def _escalares(d: dict) -> bool:
    return all(not isinstance(v, list) or all(not isinstance(x, (dict, list)) for x in v)
               for v in d.values())


def converter(nome: str, obj) -> dict[str, tuple[list[str], list[list]]]:
    """Devolve {nome_do_csv: (colunas, linhas)}. Vazio se o JSON não for tabular."""
    if nome == "distritos":
        # {"distrito", "total", "anos": {"2015": n, ...}} -> uma coluna por ano
        anos = sorted({a for r in obj for a in r["anos"]})
        cols = ["distrito", "total"] + [f"n_{a}" for a in anos]
        return {nome: (cols, [[r["distrito"], r["total"]] + [r["anos"].get(a, 0) for a in anos] for r in obj])}
    if nome == "grade":
        # células por tema: [lat, lon, n] -> formato longo, ordenado (o export não fixa a ordem)
        ordem = {t: i for i, t in enumerate(obj["temas"])}
        linhas = [[t, lat, lon, n] for t, cel in obj["celulas"].items() for lat, lon, n in cel]
        linhas.sort(key=lambda r: (ordem.get(r[0], len(ordem)), r[0], r[1], r[2]))
        return {nome: (["tema", "lat", "lon", "n"], linhas)}
    if nome == "reativacao":
        resumo = [[k, v] for k, v in obj.items() if not isinstance(v, (list, dict))]
        saida = {f"{nome}_resumo": (["indicador", "valor"], resumo)}
        for k in ("por_mes", "situacao", "canal"):
            saida[f"{nome}_{k}"] = _registros(obj[k])
        saida[f"{nome}_pontos"] = (["lat", "lon", "ym", "situacao"], [list(p) for p in obj["pontos"]])
        return saida
    if isinstance(obj, list) and obj and all(isinstance(r, dict) for r in obj) \
            and all(not isinstance(v, (dict, list)) for r in obj for v in r.values()):
        return {nome: _registros(obj)}
    if isinstance(obj, dict) and _escalares({k: v for k, v in obj.items() if not isinstance(v, dict)}):
        return {nome: (["indicador", "valor"], [list(p) for p in _plano(obj)])}
    return {}


def escrever(caminho: Path, cols: list[str], linhas: list[list]) -> None:
    with caminho.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(cols)
        w.writerows([[_cel(v) for v in r] for r in linhas])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    indice, gerados = {}, set()
    for p in sorted(DATA.glob("*.json")):
        nome = p.stem
        if nome in PULAR:
            print(f"pulado  {p.name}: {PULAR[nome]}")
            continue
        tabelas = converter(nome, json.loads(p.read_text(encoding="utf-8")))
        if not tabelas:
            print(f"pulado  {p.name}: estrutura não tabular")
            continue
        for csv_nome, (cols, linhas) in tabelas.items():
            escrever(OUT / f"{csv_nome}.csv", cols, linhas)
            gerados.add(f"{csv_nome}.csv")
            indice[csv_nome] = {"arquivo": f"{csv_nome}.csv", "origem": p.name, "linhas": len(linhas),
                                "colunas": cols}
            print(f"{csv_nome}.csv  {len(linhas)} linhas")
    for velho in OUT.glob("*.csv"):  # CSV de um JSON que deixou de existir
        if velho.name not in gerados:
            velho.unlink()
    INDICE.write_text(json.dumps(dict(sorted(indice.items())), ensure_ascii=False, indent=1) + "\n",
                      encoding="utf-8")


if __name__ == "__main__":
    main()
