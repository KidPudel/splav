#!/bin/sh
# Rebuild Splav from scratch: fonts, instances, calibration, both styles.
set -e
cd "$(dirname "$0")/.."
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
[ -d build/corpus/averiaseriflibre ] || sh scripts/fetch_corpus.sh
.venv/bin/python scripts/prep.py
.venv/bin/python scripts/calibrate.py roman400 roman300
.venv/bin/python scripts/calibrate.py italic700 italic700
.venv/bin/python scripts/build.py light
.venv/bin/python scripts/build.py bolditalic
.venv/bin/python scripts/specimen_splav.py
