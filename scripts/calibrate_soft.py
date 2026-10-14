"""Fit the softness (soften.py) on Latin: the blur, threshold and weight that
make the corpus average of Latin letters match Averia most closely, on top of
the width/height/slant fit from calibrate.py. Written into the same calib file.

Usage: calibrate_soft.py <corpus style> <averia style>
"""
import itertools
import json
import os
import pickle
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

import avg
from calibrate_tools import offset

SRC, REF_STYLE = sys.argv[1], sys.argv[2]
REF = avg.MANIFEST['averiaseriflibre'][REF_STYLE]
CALIB = os.path.join(avg.BUILD, f'calib-{SRC}-{REF_STYLE}.json')
CAL = json.load(open(CALIB))
cache = pickle.load(open(os.path.join(avg.BUILD, f'cache-{SRC}.pkl'), 'rb'))
CHARS = {'lower': 'aenohdpgsxkmbuvrc', 'upper': 'HOREBNDCMPSTUX'}

S, X0, Y1, W, H = 0.4, -150, 1100, 640, 640  # fixed grid, 0.4 px per unit


def coverage(contours, n_outer):
    img = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(img)
    tr = lambda c: [((x - X0) * S, (Y1 - y) * S) for x, y in c]
    for c in contours[:n_outer]:
        d.polygon(tr(c), fill=255)
    for c in contours[n_outer:]:
        d.polygon(tr(c), fill=0)
    return np.asarray(img, dtype=float) / 255


def shaped(shape, p, d):
    out = []
    for c in shape['contours']:
        c = offset(c, d)
        out.append(np.stack([c[:, 0] * p['sx'] + c[:, 1] * p['k'], c[:, 1] * p['sy']], 1))
    return out


refs = {}
for ch in CHARS['lower'] + CHARS['upper']:
    r = avg.glyph_shape(REF, ch)
    refs[ch] = coverage(r['contours'], r['sig'][0]) > 0.5

result = dict(CAL)
for case, chars in CHARS.items():
    p = CAL[case]
    base = {}
    for dd in range(-36, 37, 4):
        for ch in chars:
            base[ch, dd] = coverage(shaped(cache[ch], p, p['d'] + dd), cache[ch]['sig'][0])

    def score(sigma, t, dd):
        s = []
        for ch in chars:
            f = base[ch, dd]
            a = (gaussian_filter(f, sigma * S) if sigma else f) > t
            b = refs[ch]
            s.append((a & b).sum() / max((a | b).sum(), 1))
        return float(np.mean(s))

    before = score(0, 0.5, 0)
    best = (before, 0, 0.5, 0)
    for sigma, t, dd in itertools.product([0, 4, 8, 12, 16, 20, 25, 30], [0.5, 0.45, 0.4, 0.35, 0.3, 0.25], range(-36, 37, 4)):
        sc = score(sigma, t, dd)
        if sc > best[0]:
            best = (sc, sigma, t, dd)
    sc, sigma, t, dd = best
    result[case] = {**p, 'soft': {'sigma': sigma, 't': t, 'd': p['d'] + dd, 'iou': round(sc, 4), 'iou_before': round(before, 4)}}
    print(case, result[case]['soft'])
json.dump(result, open(CALIB, 'w'), indent=1)
