"""Confere se o CKAN da Prefeitura publicou arquivo novo (ou republicado) do SP156.

Compara a lista de recursos de `package_show?id=dados-do-sp156` com config/sp156_resources.csv.
Não baixa nem grava dados: só imprime o resumo e, dentro do GitHub Actions, escreve
`novo=true|false` em $GITHUB_OUTPUT.

Uso: PYTHONPATH=src python scripts/checar_sp156.py
Precisa só de `requests` e `pyyaml`.
"""
import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dados_publicos import config, sp156  # noqa: E402


def main() -> int:
    cfg, _ = config.load()
    remoto = {r["periodo"]: r for r in sp156.listar(cfg)}
    with sp156.INDEX.open(encoding="utf-8") as fh:
        local = {r["periodo"]: r for r in csv.DictReader(fh)}

    novos = sorted(set(remoto) - set(local))
    sumidos = sorted(set(local) - set(remoto))
    # mesmo período, mas URL, extensão ou tamanho diferente = arquivo republicado pela Prefeitura
    mudados = sorted(p for p in set(remoto) & set(local)
                     if (remoto[p]["url"], remoto[p]["ext"], str(remoto[p]["size"]))
                     != (local[p]["url"], local[p]["ext"], str(local[p]["size"])))

    print(f"CKAN: {len(remoto)} arquivos | sp156_resources.csv: {len(local)} arquivos")
    print(f"novos: {novos or '-'}")
    print(f"republicados: {mudados or '-'}")
    if sumidos:
        print(f"AVISO: sumiram do CKAN (não dispara reconstrução): {sumidos}")
    novo = bool(novos or mudados)
    print(f"novo={str(novo).lower()}")

    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"novo={str(novo).lower()}\n")
            fh.write(f"periodos={','.join(novos + mudados)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
