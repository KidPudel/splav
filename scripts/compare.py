"""Compare averaged Latin glyphs with real Averia: overlay and overlap score."""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

import avg

ROOT = avg.ROOT
CHARS = sys.argv[1] if len(sys.argv) > 1 else 'aenohdpgsRHOB'
STYLE = sys.argv[2] if len(sys.argv) > 2 else 'roman400'
REF = avg.MANIFEST['averiaseriflibre'][STYLE]
EXTRA = sys.argv[3].split(',') if len(sys.argv) > 3 else []

CELL = 260
S = 0.22  # px per unit
BASE = 200


def raster(shape, size=(CELL, CELL)):
    img = Image.new('L', size, 0)
    d = ImageDraw.Draw(img)
    n_out = shape['sig'][0]
    pts = lambda c: [(20 + x * S, BASE - y * S) for x, y in c]
    for c in shape['contours'][:n_out]:
        d.polygon(pts(c), fill=255)
    for c in shape['contours'][n_out:]:
        d.polygon(pts(c), fill=0)
    return np.array(img) > 127


sheet = Image.new('RGB', (CELL * len(CHARS), CELL * 2 + 30), 'white')
scores = []
for i, ch in enumerate(CHARS):
    mean = avg.corpus_average(ch, STYLE, avg.CORE + EXTRA)
    ref = avg.glyph_shape(REF, ch)
    a, b = raster(mean), raster(ref)
    iou = (a & b).sum() / max((a | b).sum(), 1)
    scores.append(iou)
    # Top: ours in black. Bottom: overlay, ours grey, Averia outline red.
    top = Image.fromarray(np.where(a, 0, 255).astype('uint8')).convert('RGB')
    over = np.full((CELL, CELL, 3), 255, 'uint8')
    over[a] = (170, 170, 170)
    over[b & ~a] = (240, 150, 150)
    over[a & b] = (110, 110, 110)
    sheet.paste(top, (i * CELL, 0))
    sheet.paste(Image.fromarray(over), (i * CELL, CELL))
    ImageDraw.Draw(sheet).text((i * CELL + 10, CELL * 2 + 6), f'{ch} {iou:.2f} {mean["used"]}/{mean["of"]}', fill='black')
    print(ch, f'iou={iou:.3f}', f'used={mean["used"]}/{mean["of"]}', f'adv ours={mean["advance"]:.0f} averia={ref["advance"]:.0f}')
print('mean iou', np.mean(scores))
out = os.path.join(ROOT, 'specimens', f'latin-check-{STYLE}.png')
sheet.save(out)
print(out)
