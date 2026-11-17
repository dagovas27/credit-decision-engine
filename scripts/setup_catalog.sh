#!/usr/bin/env bash
# Create the Unity Catalog objects used by the project inside an existing catalog:
#   schemas bronze/silver/gold/ml and the managed Volume <catalog>.bronze.landing.
#
# The catalog itself is NOT created here. On Databricks Free Edition the API cannot create
# catalogs ("Metastore storage root URL does not exist"); create it once in the UI with
# Default Storage (see README). This script only checks that it exists.
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

echo "+ databricks catalogs get $CATALOG"
if [[ "${DRY_RUN:-0}" != "1" ]] && ! databricks catalogs get "$CATALOG" >/dev/null; then
  echo "Catalog '$CATALOG' not found. Create it in the UI (Catalog Explorer > Create catalog," >&2
  echo "Default Storage) and run this script again." >&2
  exit 1
fi

for schema in "${SCHEMAS[@]}"; do
  run databricks schemas create "$schema" "$CATALOG"
done
run databricks volumes create "$CATALOG" "$VOLUME_SCHEMA" "$VOLUME" MANAGED \
  --comment "Raw Freddie Mac files as delivered (pipe-delimited, no header)"
