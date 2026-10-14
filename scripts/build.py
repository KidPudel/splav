"""Build Splav: Averia Serif Libre with Cyrillic. Everything Averia has
(Latin, digits, punctuation, kerning) is kept as it is; Cyrillic letters that
share a shape with Latin reuse Averia's glyphs, and the Cyrillic-only letters
are averaged across the corpus and fitted to Averia.

Usage: build.py light|regular|bold|lightitalic|italic|bolditalic
"""
import json
import os
import sys

import numpy as np
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

import avg
import soften
from calibrate_tools import offset

STYLE = sys.argv[1]
# Each style averages the nearest weight the sources share (most have no
# Light) and is fitted to the matching style of Averia. The upright averages
# come out crisper than Averia, so they get the fitted softness (soften.py);
# the italic averages already match it.
CONF = {
    'light': {'src': 'roman400', 'ref': 'roman300', 'weight': 300, 'italic': False, 'sub': 'Light', 'file': 'Light'},
    'regular': {'src': 'roman400', 'ref': 'roman400', 'weight': 400, 'italic': False, 'sub': 'Regular', 'file': 'Regular'},
    'bold': {'src': 'roman700', 'ref': 'roman700', 'weight': 700, 'italic': False, 'sub': 'Bold', 'file': 'Bold'},
    'lightitalic': {'src': 'italic400', 'ref': 'italic300', 'weight': 300, 'italic': True, 'sub': 'Light Italic', 'file': 'LightItalic'},
    'italic': {'src': 'italic400', 'ref': 'italic400', 'weight': 400, 'italic': True, 'sub': 'Italic', 'file': 'Italic'},
    'bolditalic': {'src': 'italic700', 'ref': 'italic700', 'weight': 700, 'italic': True, 'sub': 'Bold Italic', 'file': 'BoldItalic'},
}[STYLE]
SOFT = not CONF['italic']
FAMILY = 'Splav'
VERSION = 0.3
REF = avg.MANIFEST['averiaseriflibre'][CONF['ref']]
CAL = json.load(open(os.path.join(avg.BUILD, f"calib-{CONF['src']}-{CONF['ref']}.json")))
AVERIA = TTFont(os.path.join(avg.BUILD, 'corpus', 'averiaseriflibre', f"AveriaSerifLibre-{CONF['file']}.ttf"))
UPM = AVERIA['head'].unitsPerEm
SCALE = UPM / 1000  # averages are in a 1000-unit em

# Cyrillic letters that share a shape with a Latin letter in Averia.
SHARED = {
    'А': 'A', 'В': 'B', 'Е': 'E', 'М': 'M', 'Н': 'H', 'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T', 'Х': 'X',
    'Ё': 'Ë', 'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'у': 'y', 'х': 'x', 'ё': 'ë',
}
UPPER = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
LOWER = UPPER.lower()


def transform(shape, p, d):
    out = []
    for c in shape['contours']:
        c = offset(c, d)
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
        pts = avg.resample(c, n) * SCALE
        pen.qCurveTo(*[(round(x), round(y)) for x, y in pts], None)
        pen.closePath()
    return pen.glyph()


# Everything from Averia, unchanged.
src_cmap = AVERIA.getBestCmap()
src_gs = AVERIA.getGlyphSet()
order = list(AVERIA.getGlyphOrder())
glyphs, metrics, advances = {}, {}, {}
for name in order:
    pen = TTGlyphPen(src_gs)
    src_gs[name].draw(pen)
    glyphs[name] = pen.glyph()
    metrics[name] = AVERIA['hmtx'][name]
cmap = dict(src_cmap)
report = {}

for ch in UPPER + LOWER:
    gname = f'uni{ord(ch):04X}'
    if ch in SHARED:
        base = src_cmap[ord(SHARED[ch])]
        pen = TTGlyphPen(src_gs)
        pen.addComponent(base, (1, 0, 0, 1, 0, 0))
        g = pen.glyph()
        advances[gname] = metrics[base][0]
        report[ch] = 'averia:' + SHARED[ch]
    else:
        mean = avg.corpus_average(ch, CONF['src'])
        p = CAL['upper' if ch in UPPER else 'lower']
        contours, adv = transform(mean, p, p['soft']['d'] if SOFT else p['d'])
        if SOFT:
            contours, _ = soften.soften(contours, mean['sig'][0], p['soft']['sigma'], p['soft']['t'])
        g = spline_glyph(contours)
        advances[gname] = round(adv * SCALE)
        report[ch] = f"avg {mean['used']}/{mean['of']}" + (f" dropped {','.join(mean.get('dropped', []))}" if mean.get('dropped') else '')
    glyphs[gname] = g
    order.append(gname)
    cmap[ord(ch)] = gname

# № (numero sign, common in Russian text, missing from Averia): Averia's N
# followed by its º.
n_name, o_name = src_cmap[ord('N')], src_cmap[ord('º')]
pen = TTGlyphPen(src_gs)
pen.addComponent(n_name, (1, 0, 0, 1, 0, 0))
pen.addComponent(o_name, (1, 0, 0, 1, metrics[n_name][0], 0))
glyphs['uni2116'] = pen.glyph()
advances['uni2116'] = metrics[n_name][0] + metrics[o_name][0]
order.append('uni2116')
cmap[0x2116] = 'uni2116'

fb = FontBuilder(UPM, isTTF=True)
fb.setupGlyphOrder(order)
fb.setupCharacterMap(cmap)
fb.setupGlyf(glyphs)
glyf = fb.font['glyf']
for name, adv in advances.items():
    glyf[name].recalcBounds(glyf)
    metrics[name] = (adv, getattr(glyf[name], 'xMin', 0))
fb.setupHorizontalMetrics(metrics)
# Vertical metrics, PANOSE and gasp exactly as in Averia, so lines set the same.
ah, ao = AVERIA['hhea'], AVERIA['OS/2']
fb.setupHorizontalHeader(ascent=ah.ascent, descent=ah.descent, lineGap=ah.lineGap)

# Bold, Italic and Bold Italic are style-linked under the family name; any
# other weight (Light) gets its own legacy family, with the shared one in
# the typographic names (16/17), so apps group and select styles correctly.
RIBBI = CONF['sub'] in ('Regular', 'Italic', 'Bold', 'Bold Italic')
legacy_family = FAMILY if RIBBI else f"{FAMILY} {CONF['sub'].replace(' Italic', '')}"
legacy_style = CONF['sub'] if RIBBI else ('Italic' if CONF['italic'] else 'Regular')
ps_name = f"{FAMILY}-{CONF['file']}"
names = {
    'copyright': 'Copyright 2026 Igor Kupchinenko. Cyrillic averaged from 18 SIL OFL serif families (see OFL.txt). Latin, figures, punctuation and kerning from Averia Serif Libre, Copyright (c) 2011, Dan Sayers (i@iotic.com).',
    'familyName': legacy_family,
    'styleName': legacy_style,
    'uniqueFontIdentifier': f"{VERSION:.3f};NONE;{ps_name}",
    'fullName': f"{FAMILY} {CONF['sub']}",
    'version': f"Version {VERSION:.3f}",
    'psName': ps_name,
    'designer': 'Igor Kupchinenko',
    'description': 'Splav: Averia Serif Libre with Cyrillic, made by averaging, like Averia.',
    'licenseDescription': 'This Font Software is licensed under the SIL Open Font License, Version 1.1.',
    'licenseInfoURL': 'https://openfontlicense.org',
}
if not RIBBI:
    names['typographicFamily'] = FAMILY
    names['typographicSubfamily'] = CONF['sub']
fb.setupNameTable(names)
bold = CONF['weight'] >= 700
fsSel = (0x01 if CONF['italic'] else 0) | (0x20 if bold else 0) or 0x40
fb.setupOS2(
    version=4, achVendID='NONE', fsType=0,  # OFL: installable embedding
    usWeightClass=CONF['weight'], fsSelection=fsSel,
    sTypoAscender=ao.sTypoAscender, sTypoDescender=ao.sTypoDescender, sTypoLineGap=ao.sTypoLineGap,
    usWinAscent=ao.usWinAscent, usWinDescent=ao.usWinDescent,
    sxHeight=glyf[src_cmap[ord('x')]].yMax, sCapHeight=glyf[src_cmap[ord('H')]].yMax,
    panose=ao.panose,
)
fb.font['OS/2'].recalcUnicodeRanges(fb.font)
fb.font['OS/2'].recalcCodePageRanges(fb.font)
fb.setupPost(italicAngle=round(AVERIA['post'].italicAngle, 1))
fb.font['head'].fontRevision = VERSION
fb.font['head'].macStyle = (0x01 if bold else 0) | (0x02 if CONF['italic'] else 0)
fb.font['gasp'] = AVERIA['gasp']

# Kerning: Averia's pairs (its kern subtables add up), plus the same pairs
# for Cyrillic letters that are Averia's Latin shapes.
pairs = {}
for sub in AVERIA['kern'].kernTables:
    for pair, v in sub.kernTable.items():
        pairs[pair] = pairs.get(pair, 0) + v
alias = {}
for ch, lat in SHARED.items():
    alias.setdefault(src_cmap[ord(lat)], []).append(f'uni{ord(ch):04X}')
for (a, b), v in list(pairs.items()):
    for a2 in [a] + alias.get(a, []):
        for b2 in [b] + alias.get(b, []):
            pairs.setdefault((a2, b2), v)
fea = 'feature kern {\n' + ''.join(f'  pos {a} {b} {v};\n' for (a, b), v in sorted(pairs.items()) if v) + '} kern;\n'
addOpenTypeFeaturesFromString(fb.font, fea)

out = os.path.join(avg.ROOT, 'fonts', 'ttf', f"{FAMILY}-{CONF['file']}.ttf")
fb.save(out)
woff2 = os.path.join(avg.ROOT, 'fonts', 'woff2', f"{FAMILY}-{CONF['file']}.woff2")
web = TTFont(out)
web.flavor = 'woff2'
web.save(woff2)
json.dump(report, open(os.path.join(avg.BUILD, f'report-{STYLE}.json'), 'w'), ensure_ascii=False, indent=1)
print(out, f'{len(order)} glyphs, {len(pairs)} kerning pairs')
