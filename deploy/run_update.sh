#!/usr/bin/env bash
# Atualização incremental do SP156 + camadas derivadas. Sai com código != 0 se a qualidade falhar.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
LOG="logs/update_$(date +%Y%m%d_%H%M%S).log"
.venv/bin/dados-publicos update 2>&1 | tee "$LOG"
.venv/bin/dados-publicos prune --keep 2 --apply | tee -a "$LOG"
# frescor: código 2 = há avisos (não é falha do pipeline)
.venv/bin/dados-publicos freshness >> "$LOG" || [ $? -eq 2 ]
find logs -name 'update_*.log' -mtime +90 -delete
