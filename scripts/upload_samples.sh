#!/usr/bin/env bash
# Upload Freddie Mac sample vintages to the landing Volume, split by file type:
#   <volume>/freddie_mac/origination/sample_orig_YYYY.txt
#   <volume>/freddie_mac/performance/sample_perf_YYYY.txt
#
# Usage:
#   DRY_RUN=1 scripts/upload_samples.sh 2005 2006 2007 2019   # print the commands only
#   scripts/upload_samples.sh 2005 2006 2007 2019             # upload
#
# Existing files are never overwritten: `databricks fs cp` fails if the target exists.
set -euo pipefail

DATA_DIR="${DATA_DIR:-$HOME/Documents/data/freddie_mac}"
VOLUME_PATH="${VOLUME_PATH:-dbfs:/Volumes/credit/bronze/landing/freddie_mac}"

if [[ $# -eq 0 ]]; then
  echo "usage: $0 YEAR [YEAR ...]" >&2
  exit 2
fi

run() {
  echo "+ $*"
  if [[ "${DRY_RUN:-0}" != "1" ]]; then
    "$@"
  fi
}

# Check every local file before touching the Volume, so a typo does not leave a half upload.
for year in "$@"; do
  for kind in orig perf; do
    file="$DATA_DIR/sample_$year/sample_${kind}_$year.txt"
    [[ -f "$file" ]] || { echo "missing: $file" >&2; exit 1; }
  done
done

run databricks fs mkdir "$VOLUME_PATH/origination"
run databricks fs mkdir "$VOLUME_PATH/performance"
for year in "$@"; do
  run databricks fs cp "$DATA_DIR/sample_$year/sample_orig_$year.txt" "$VOLUME_PATH/origination/"
  run databricks fs cp "$DATA_DIR/sample_$year/sample_perf_$year.txt" "$VOLUME_PATH/performance/"
done
run databricks fs ls "$VOLUME_PATH/origination"
run databricks fs ls "$VOLUME_PATH/performance"
