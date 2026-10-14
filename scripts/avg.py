"""Average glyph outlines across fonts, the way Averia was made (Splav).

Each glyph's contours are cleaned of overlaps, split into evenly spaced points
around their perimeter, matched across fonts (same contour structure, same
direction, best cyclic start), and averaged point by point.
"""
import json
import os
from collections import Counter

import numpy as np
import pathops
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, 'build')
MANIFEST_PATH = os.path.join(BUILD, 'manifest.json')
MANIFEST = json.load(open(MANIFEST_PATH)) if os.path.exists(MANIFEST_PATH) else {}

CORE = [
    'ptserif', 'lora', 'literata', 'merriweather', 'sourceserif4', 'spectral',
    'ibmplexserif', 'notoserif', 'robotoserif', 'ebgaramond', 'alegreya', 'vollkorn',
    'stixtwotext', 'charissil', 'gentiumbookplus', 'libertinusserif', 'piazzolla',
    'brygada1918',
]

N_POINTS = 320
_fonts = {}


def font(path):
    if path not in _fonts:
        _fonts[path] = TTFont(path)
    return _fonts[path]


class FlattenPen(BasePen):
    """Collects contours as dense polylines."""

    def __init__(self, glyphSet=None, steps=24):
        super().__init__(glyphSet)
        self.steps = steps
        self.contours = []
        self.current = []

    def _moveTo(self, p):
        self.current = [p]

    def _lineTo(self, p):
        self.current.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.current[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            mt = 1 - t
            self.current.append((
                mt**3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t**3 * p3[0],
                mt**3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t**3 * p3[1],
            ))

    def _qCurveToOne(self, p1, p2):
        p0 = self.current[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            mt = 1 - t
            self.current.append((
                mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0],
                mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1],
            ))

    def _closePath(self):
        if len(self.current) > 2:
            self.contours.append(np.array(self.current, dtype=float))
        self.current = []

    _endPath = _closePath


def signed_area(c):
    x, y = c[:, 0], c[:, 1]
    return 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)


def point_in(poly, p):
    x, y = poly[:, 0], poly[:, 1]
    x2, y2 = np.roll(x, -1), np.roll(y, -1)
    cond = (y > p[1]) != (y2 > p[1])
    with np.errstate(divide='ignore', invalid='ignore'):
        xint = x + (p[1] - y) * (x2 - x) / (y2 - y)
    return np.count_nonzero(cond & (p[0] < xint)) % 2 == 1


def resample(c, n=N_POINTS):
    closed = np.vstack([c, c[:1]])
    seg = np.sqrt((np.diff(closed, axis=0) ** 2).sum(1))
    cum = np.concatenate([[0], np.cumsum(seg)])
    total = cum[-1]
    t = np.linspace(0, total, n, endpoint=False)
    x = np.interp(t, cum, closed[:, 0])
    y = np.interp(t, cum, closed[:, 1])
    return np.stack([x, y], 1)


def glyph_shape(path, char):
    """Contours (outer first, then holes), each resampled, in 1000-unit em; plus advance."""
    f = font(path)
    cmap = f.getBestCmap()
    if ord(char) not in cmap:
        return None
    gname = cmap[ord(char)]
    gs = f.getGlyphSet()
    upm = f['head'].unitsPerEm
    p = pathops.Path()
    gs[gname].draw(p.getPen(glyphSet=gs))
    try:
        p.simplify(fix_winding=True)
    except Exception:
        pass
    pen = FlattenPen()
    p.draw(pen)
    scale = 1000 / upm
    contours = [c * scale for c in pen.contours if len(c) > 2]
    if not contours:
        return None
    outers, holes = [], []
    for i, c in enumerate(contours):
        depth = sum(point_in(o, c[len(c) // 2]) for j, o in enumerate(contours) if j != i)
        (holes if depth % 2 else outers).append(c)
    # Outer contours counterclockwise, holes clockwise.
    outers = [c if signed_area(c) > 0 else c[::-1] for c in outers]
    holes = [c if signed_area(c) < 0 else c[::-1] for c in holes]
    key = lambda c: (round(c[:, 0].mean() / 40), -c[:, 1].mean())
    outers.sort(key=key)
    holes.sort(key=key)
    adv = gs[gname].width * scale
    return {
        'sig': (len(outers), len(holes)),
        'contours': [resample(c) for c in outers + holes],
        'advance': adv,
    }


def best_shift(p, ref):
    """Cyclic shift of p that best matches ref (cross-correlation via FFT)."""
    pc = p[:, 0] + 1j * p[:, 1]
    rc = ref[:, 0] + 1j * ref[:, 1]
    corr = np.fft.ifft(np.fft.fft(pc) * np.conj(np.fft.fft(rc)))
    return int(np.argmax(corr.real))


def _align(cs, iterations=4):
    ref = np.median(np.stack(cs), axis=0)
    for _ in range(iterations):
        aligned = [np.roll(c, -best_shift(c - c.mean(0), ref - ref.mean(0)), axis=0) for c in cs]
        ref = np.mean(np.stack(aligned), axis=0)
    return aligned, ref


def _mean_of(group):
    n_contours = len(group[0]['contours'])
    per_font = [[] for _ in group]
    means = []
    for ci in range(n_contours):
        aligned, ref = _align([s['contours'][ci] for s in group])
        means.append(ref)
        for i, a in enumerate(aligned):
            per_font[i].append(a)
    return means, per_font


def _dist(a, b):
    return float(np.mean([np.sqrt(((x - y) ** 2).sum(1)).mean() for x, y in zip(a, b)]))


def average(shapes):
    """Point-wise mean of the shapes with the majority structure. Fonts that
    draw the letter in a different form (a second cluster) or far from the
    rest are left out, so the mean never blends two forms into mush."""
    sig = Counter(s['sig'] for s in shapes).most_common(1)[0][0]
    group = [s for s in shapes if s['sig'] == sig]
    dropped = [s.get('fam', '?') + '(structure)' for s in shapes if s['sig'] != sig]
    means, per_font = _mean_of(group)
    n = len(group)
    if n >= 6:
        D = np.array([[_dist(per_font[i], per_font[j]) for j in range(n)] for i in range(n)])
        best = None
        for a in range(n):
            for b in range(a + 1, n):
                lab = (D[:, b] < D[:, a]).astype(int)
                cost = np.where(lab, D[:, b], D[:, a]).sum()
                if best is None or cost < best[0]:
                    best = (cost, a, b, lab)
        _, a, b, lab = best
        sizes = (int((lab == 0).sum()), int((lab == 1).sum()))
        spread = np.mean([D[i, a] if lab[i] == 0 else D[i, b] for i in range(n)])
        if min(sizes) >= 3 and D[a, b] > 3.0 * spread:
            keep = 0 if sizes[0] >= sizes[1] else 1
            dropped += [group[i].get('fam', '?') + '(form)' for i in range(n) if lab[i] != keep]
            group = [group[i] for i in range(n) if lab[i] == keep]
            means, per_font = _mean_of(group)
    d = np.array([_dist(pf, means) for pf in per_font])
    far = d > 2.2 * np.median(d)
    if far.any() and (~far).sum() >= 4:
        dropped += [group[i].get('fam', '?') + '(outlier)' for i in np.nonzero(far)[0]]
        group = [g for g, f in zip(group, far) if not f]
        means, per_font = _mean_of(group)
    return {
        'sig': sig,
        'contours': means,
        'advance': float(np.mean([s['advance'] for s in group])),
        'used': len(group),
        'of': len(shapes),
        'dropped': dropped,
    }


def corpus_average(char, style, families=CORE):
    shapes = []
    for fam in families:
        path = MANIFEST.get(fam, {}).get(style)
        if not path:
            continue
        s = glyph_shape(path, char)
        if s:
            s['fam'] = fam
            shapes.append(s)
    return average(shapes) if shapes else None
