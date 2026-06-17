#!/usr/bin/env bash
# Sync split pipeline data from employer-discovery → employerflow (free, no APIs)
set -euo pipefail
DISCOVERY="${DISCOVERY_ROOT:-$HOME/Projects/employer-discovery}"
FLOW="$(cd "$(dirname "$0")/.." && pwd)"

echo "Syncing from $DISCOVERY → $FLOW/data"

for f in master_employers.csv job_signals.csv; do
  if [[ -f "$DISCOVERY/data/$f" ]]; then
    cp "$DISCOVERY/data/$f" "$FLOW/data/$f"
    echo "  ✓ $f"
  else
    echo "  ✗ missing $f — run: python scripts/migrate_split_data.py in employer-discovery"
    exit 1
  fi
done

wc -l "$FLOW/data/master_employers.csv" "$FLOW/data/job_signals.csv"
echo "Done. Reseed production: python scripts/reseed_from_pipeline.py (with DATABASE_URL set)"