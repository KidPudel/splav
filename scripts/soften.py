"""The softness of a large average.

Averia averaged 725 fonts; Splav's sources are the few dozen serifs with
Cyrillic, which agree with each other far more, so their average keeps crisp
serifs and high contrast. Averaging a shape with many slightly shifted copies
of itself and keeping what most of them cover is a Gaussian blur followed by
a threshold: corners and serifs round off and thin strokes fill out. How far
(sigma, in font units) and where to cut (threshold) are fitted on Latin, so
the averaged Latin matches real Averia (calibrate_soft.py).
"""
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter
from skimage.measure import find_contours

import avg

SCALE = 0.5  # pixels per font unit while softening


def field(contours, n_outer, sigma, scale=SCALE):
    """Coverage of the shape blurred by sigma, with the grid's origin."""
    pts = np.vstack(contours)
    pad = 3 * sigma + 8
    x0, y1 = pts[:, 0].min() - pad, pts[:, 1].max() + pad
    w = int((pts[:, 0].max() + pad - x0) * scale) + 1
    h = int((y1 - pts[:, 1].min() + pad) * scale) + 1
    img = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(img)
    tr = lambda c: [((x - x0) * scale, (y1 - y) * scale) for x, y in c]
    for c in contours[:n_outer]:
        d.polygon(tr(c), fill=255)
    for c in contours[n_outer:]:
        d.polygon(tr(c), fill=0)
    f = np.asarray(img, dtype=float) / 255
    if sigma > 0:
        f = gaussian_filter(f, sigma * scale)
    return f, x0, y1


def soften(contours, n_outer, sigma, threshold):
    """Softened outline: outer contours first (counterclockwise), then holes."""
    if sigma <= 0:
        return contours, n_outer
    f, x0, y1 = field(contours, n_outer, sigma)
    found = [np.stack([x0 + c[:, 1] / SCALE, y1 - c[:, 0] / SCALE], 1)[:-1]
             for c in find_contours(np.pad(f, 1), threshold)]
    # find_contours ran on the padded grid: undo the one-pixel shift.
    found = [c - [1 / SCALE, -1 / SCALE] for c in found if len(c) > 8]
    found = [c for c in found if abs(avg.signed_area(c)) > 400]
    outers, holes = [], []
    for i, c in enumerate(found):
        depth = sum(avg.point_in(o, c[0]) for j, o in enumerate(found) if j != i)
        (holes if depth % 2 else outers).append(c)
    outers = [c if avg.signed_area(c) > 0 else c[::-1] for c in outers]
    holes = [c if avg.signed_area(c) < 0 else c[::-1] for c in holes]
    return outers + holes, len(outers)
