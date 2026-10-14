"""Build the Cyrillic companion to Averia: shared shapes from Averia itself,
Cyrillic-only letters averaged across the corpus and calibrated to Averia.

Usage: build.py light|bolditalic
"""
import json
import os
import sys

import numpy as np
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

import avg
from calibrate_tools import offset

STYLE = sys.argv[1]
CONF = {
    'light': {'src': 'roman400', 'ref': 'roman300', 'weight': 300, 'italic': False, 'sub': 'Light', 'file': 'Light'},
    'bolditalic': {'src': 'italic700', 'ref': 'italic700', 'weight': 700, 'italic': True, 'sub': 'Bold Italic', 'file': 'BoldItalic'},
}[STYLE]
FAMILY = 'Splav'
REF = avg.MANIFEST['averiaseriflibre'][CONF['ref']]
CAL = json.load(open(os.path.join(avg.BUILD, f"calib-{CONF['src']}-{CONF['ref']}.json")))
UPM = 1000

# Cyrillic letters that share a shape with a Latin letter in Averia.
SHARED = {
    'А': 'A', 'В': 'B', 'Е': 'E', 'М': 'M', 'Н': 'H', 'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T', 'Х': 'X',
    'Ё': 'Ë', 'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'у': 'y', 'х': 'x', 'ё': 'ë',
}
UPPER = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
LOWER = UPPER.lower()


def transform(shape, p):
    out = []
    for c in shape['contours']:
        c = offset(c, p['d'])
        out.append(np.stack([c[:, 0] * p['sx'] + c[:, 1] * p['k'], c[:, 1] * p['sy']], 1))
    return out, shape['advance'] * p['sx']


def spline_glyph(contours):
    """Closed quadratic B-splines through evenly spaced control points (all
    off-curve), which keeps the averaged outline smooth."""
    pen = TTGlyphPen(None)
    for c in contours:
        closed = np.vstack([c, c[:1]])
        perim = np.sqrt((np.diff(closed, axis=0) ** 2).sum(1)).sum()
        n = max(24, int(perim / 11))
        pts = avg.resample(c, n)
        pen.qCurveTo(*[(round(x), round(y)) for x, y in pts], None)
        pen.closePath()
    return pen.glyph()


def averia_glyph(char):
    f = avg.font(REF)
    gs = f.getGlyphSet()
    name = f.getBestCmap()[ord(char)]
    scale = UPM / f['head'].unitsPerEm
    pen = TTGlyphPen(gs)
    gs[name].draw(TransformPen(pen, (scale, 0, 0, scale, 0, 0)))
    return pen.glyph(), gs[name].width * scale


glyphs = {'.notdef': TTGlyphPen(None).glyph(), 'space': TTGlyphPen(None).glyph()}
metrics = {'.notdef': (500, 0), 'space': (int(avg.glyph_shape(REF, ' ')['advance']) if avg.glyph_shape(REF, ' ') else 250, 0)}
cmap = {32: 'space'}
report = {}

for ch in UPPER + LOWER:
    gname = f'uni{ord(ch):04X}'
    if ch in SHARED:
        g, adv = averia_glyph(SHARED[ch])
        report[ch] = 'averia:' + SHARED[ch]
    else:
        mean = avg.corpus_average(ch, CONF['src'])
        contours, adv = transform(mean, CAL['upper' if ch in UPPER else 'lower'])
        g = spline_glyph(contours)
        report[ch] = f"avg {mean['used']}/{mean['of']}" + (f" dropped {','.join(mean.get('dropped', []))}" if mean.get('dropped') else '')
    g.recalcBounds(None)
    glyphs[gname] = g
    metrics[gname] = (round(adv), g.xMin if hasattr(g, 'xMin') else 0)
    cmap[ord(ch)] = gname

order = list(glyphs)
fb = FontBuilder(UPM, isTTF=True)
fb.setupGlyphOrder(order)
fb.setupCharacterMap(cmap)
fb.setupGlyf(glyphs)
fb.setupHorizontalMetrics(metrics)
fb.setupHorizontalHeader(ascent=890, descent=-227)
fb.setupNameTable({
    'familyName': FAMILY,
    'styleName': CONF['sub'],
    'copyright': 'Copyright 2026 Igor Kupchinenko. Cyrillic averaged from 18 SIL OFL serif families (see OFL.txt); Latin-shared shapes from Averia Serif Libre, Copyright (c) 2011 Dan Sayers.',
    'version': 'Version 0.1',
    'designer': 'Igor Kupchinenko',
    'description': 'Splav: a Cyrillic companion to Averia Serif Libre, made by averaging, like Averia.',
    'licenseDescription': 'This Font Software is licensed under the SIL Open Font License, Version 1.1.',
    'licenseInfoURL': 'https://openfontlicense.org',
})
fsSel = (0x01 if CONF['italic'] else 0) | (0x20 if CONF['weight'] >= 700 else 0) or 0x40
fb.setupOS2(usWeightClass=CONF['weight'], sTypoAscender=890, sTypoDescender=-227, usWinAscent=890, usWinDescent=227, fsSelection=fsSel, sxHeight=0, sCapHeight=0)
fb.setupPost(italicAngle=-6.9 if CONF['italic'] else 0)
out = os.path.join(avg.ROOT, 'fonts', 'ttf', f"{FAMILY}-{CONF['file']}.ttf")
fb.save(out)
woff2 = os.path.join(avg.ROOT, 'fonts', 'woff2', f"{FAMILY}-{CONF['file']}.woff2")
from fontTools.ttLib import TTFont as _T
_f = _T(out)
_f.flavor = 'woff2'
_f.save(woff2)
json.dump(report, open(os.path.join(avg.BUILD, f'report-{STYLE}.json'), 'w'), ensure_ascii=False, indent=1)
print(out)
for k, v in report.items():
    print(k, v)
