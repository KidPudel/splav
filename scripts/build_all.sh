#!/bin/sh
# Rebuild Splav from scratch: fonts, instances, calibration, all six styles.
set -e
cd "$(dirname "$0")/.."
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
[ -d build/corpus/averiaseriflibre ] || sh scripts/fetch_corpus.sh
.venv/bin/python scripts/prep.py
# corpus style -> Averia style, one fit per Splav style
.venv/bin/python scripts/calibrate.py roman400 roman300
.venv/bin/python scripts/calibrate.py roman400 roman400
.venv/bin/python scripts/calibrate.py roman700 roman700
.venv/bin/python scripts/calibrate.py italic400 italic300
.venv/bin/python scripts/calibrate.py italic400 italic400
.venv/bin/python scripts/calibrate.py italic700 italic700
# softness of the uprights, fitted on top of the fits above
.venv/bin/python scripts/calibrate_soft.py roman400 roman300
.venv/bin/python scripts/calibrate_soft.py roman400 roman400
.venv/bin/python scripts/calibrate_soft.py roman700 roman700
for style in light regular bold lightitalic italic bolditalic; do
  .venv/bin/python scripts/build.py $style
done
.venv/bin/python scripts/specimen_splav.py
