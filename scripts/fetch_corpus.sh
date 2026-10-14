#!/bin/sh
# Download the source fonts from the Google Fonts repository into build/corpus.
# The core 18 are averaged; the rest are kept for comparison (see SOURCES.md),
# and Averia Serif Libre is the reference the averages are fitted to.
set -e
cd "$(dirname "$0")/.."
mkdir -p build/corpus
FAMILIES="ptserif lora literata merriweather sourceserif4 spectral ibmplexserif notoserif robotoserif ebgaramond alegreya vollkorn stixtwotext charissil gentiumbookplus libertinusserif piazzolla brygada1918 cormorantgaramond ledger bonanova prata oranienbaum playfairdisplay oldstandardtt alice kurale gabriela averiaseriflibre"
for fam in $FAMILIES; do
  for dir in ofl/$fam apache/$fam; do
    files=$(curl -s "https://api.github.com/repos/google/fonts/contents/$dir" | python3 -c 'import json,sys
try:
    print("\n".join(f["name"] for f in json.load(sys.stdin) if f["name"].endswith(".ttf")))
except Exception:
    pass')
    [ -n "$files" ] && break
  done
  mkdir -p "build/corpus/$fam"
  echo "$files" | while read -r f; do
    [ -z "$f" ] && continue
    [ -f "build/corpus/$fam/$f" ] && continue
    enc=$(printf %s "$f" | sed 's/\[/%5B/g; s/\]/%5D/g; s/,/%2C/g')
    curl -sgL "https://raw.githubusercontent.com/google/fonts/main/$dir/$enc" -o "build/corpus/$fam/$f"
  done
  echo "$fam"
done
