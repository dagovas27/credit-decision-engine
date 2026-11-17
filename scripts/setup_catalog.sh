#!/usr/bin/env bash
# Create the Unity Catalog objects used by the project:
#   catalog `credit`, schemas bronze/silver/gold/ml, managed Volume credit.bronze.landing.
#
# Usage:
#   DRY_RUN=1 scripts/setup_catalog.sh   # print the commands only
#   scripts/setup_catalog.sh             # run them (needs an authenticated Databricks CLI)
#
# Authentication is not handled here: run `databricks auth login` yourself first.
set -euo pipefail

CATALOG="${CATALOG:-credit}"
SCHEMAS=(bronze silver gold ml)
VOLUME_SCHEMA="bronze"
VOLUME="landing"

run() {
  echo "+ $*"
  if [[ "${DRY_RUN:-0}" != "1" ]]; then
    "$@"
  fi
}

run databricks catalogs create "$CATALOG" --comment "Credit decision engine (Freddie Mac SFLLD)"
for schema in "${SCHEMAS[@]}"; do
  run databricks schemas create "$schema" "$CATALOG"
done
run databricks volumes create "$CATALOG" "$VOLUME_SCHEMA" "$VOLUME" MANAGED \
  --comment "Raw Freddie Mac files as delivered (pipe-delimited, no header)"
