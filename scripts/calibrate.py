"""Find the transform (width, height, weight, slant) that makes the corpus
average of Latin letters match Averia, so the same transform can be applied to
the averaged Cyrillic.

Usage: calibrate.py <corpus style> <averia style>
"""
import itertools
import json
import os
import pickle
import sys

import numpy as np
from PIL import Image, ImageDraw

import avg

SRC, REF_STYLE = sys.argv[1], sys.argv[2]
LOWER = 'aenohdpgsxkmbuvrc'
UPPER = 'HOREBNDCMPSTUX'
REF = avg.MANIFEST['averiaseriflibre'][REF_STYLE]
CACHE = os.path.join(avg.BUILD, f'cache-{SRC}.pkl')

cache = pickle.load(open(CACHE, 'rb')) if os.path.exists(CACHE) else {}
for ch in LOWER + UPPER:
    if ch not in cache:
        cache[ch] = avg.corpus_average(ch, SRC)
pickle.dump(cache, open(CACHE, 'wb'))
refs = {ch: avg.glyph_shape(REF, ch) for ch in LOWER + UPPER}

S, W, H, BX, BY = 0.2, 300, 300, 40, 230


from calibrate_tools import offset


def transform(shape, sx, sy, d, k):
    out = []
    for c in shape['contours']:
        c = offset(c, d)
        out.append(np.stack([c[:, 0] * sx + c[:, 1] * k, c[:, 1] * sy], 1))
    return {**shape, 'contours': out, 'advance': shape['advance'] * sx}


def raster(shape):
    img = Image.new('L', (W, H), 0)
    dr = ImageDraw.Draw(img)
    n = shape['sig'][0]
    pts = lambda c: [(BX + x * S, BY - y * S) for x, y in c]
    for c in shape['contours'][:n]:
        dr.polygon(pts(c), fill=255)
    for c in shape['contours'][n:]:
        dr.polygon(pts(c), fill=0)
    return np.array(img) > 127


ref_r = {ch: raster(refs[ch]) for ch in refs}


def score(chars, sx, sy, d, k):
    s = []
    for ch in chars:
        a = raster(transform(cache[ch], sx, sy, d, k))
        b = ref_r[ch]
        s.append((a & b).sum() / max((a | b).sum(), 1))
    return float(np.mean(s))


def search(chars):
    best = (score(chars, 1, 1, 0, 0), 1, 1, 0, 0)
    slants = [0] if 'italic' not in SRC else [-0.06, -0.03, 0, 0.03, 0.06]
    for sx, sy, d, k in itertools.product(np.arange(0.94, 1.08, 0.02), np.arange(0.94, 1.1, 0.02), range(-36, 25, 6), slants):
        sc = score(chars, sx, sy, d, k)
        if sc > best[0]:
            best = (sc, sx, sy, d, k)
    # Refine around the best.
    _, bx, by, bd, bk = best
    for sx, sy, d, k in itertools.product(np.arange(bx - 0.015, bx + 0.016, 0.005), np.arange(by - 0.015, by + 0.016, 0.005), range(bd - 4, bd + 5, 2), [bk - 0.01, bk, bk + 0.01] if slants != [0] else [0]):
        sc = score(chars, sx, sy, d, k)
        if sc > best[0]:
            best = (sc, sx, sy, d, k)
    return best


result = {}
for name, chars in (('lower', LOWER), ('upper', UPPER)):
    base = score(chars, 1, 1, 0, 0)
    sc, sx, sy, d, k = search(chars)
    result[name] = {'sx': round(float(sx), 4), 'sy': round(float(sy), 4), 'd': int(d), 'k': round(float(k), 4), 'iou': round(sc, 4), 'iou_before': round(base, 4)}
    print(name, result[name])
json.dump(result, open(os.path.join(avg.BUILD, f'calib-{SRC}-{REF_STYLE}.json'), 'w'), indent=1)
