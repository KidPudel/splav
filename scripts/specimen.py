"""Specimen sheet of every corpus font's Cyrillic, upright 400 and bold italic 700."""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
manifest = json.load(open(os.path.join(ROOT, 'build', 'manifest.json')))

ROMAN = 'В продуктовом дизайне я ищу странности. Ж Д Л Ф Щ Ы Э Ю Я  б в г д ж з к л ф ц щ ы ю я'
ITALIC = 'взаимодействия, сам собираю то, что проектирую  б в г д и й к л м н п т ц ш щ'
LABEL = ImageFont.truetype(manifest['ptserif']['roman400'], 22)

SIZE = 44
ROW = 128
W = 2400
fams = [f for f in sys.argv[1:]] or sorted(manifest)
img = Image.new('RGB', (W, ROW * len(fams) + 20), 'white')
d = ImageDraw.Draw(img)
for i, fam in enumerate(fams):
    y = 10 + i * ROW
    d.text((20, y + 6), fam, font=LABEL, fill=(150, 60, 60))
    entry = manifest[fam]
    if 'roman400' in entry:
        d.text((300, y), ROMAN, font=ImageFont.truetype(entry['roman400'], SIZE), fill='black')
    if 'italic700' in entry:
        d.text((300, y + 58), ITALIC, font=ImageFont.truetype(entry['italic700'], SIZE), fill='black')
    d.line((0, y + ROW - 6, W, y + ROW - 6), fill=(225, 225, 225))
out = os.path.join(ROOT, 'specimens', 'sources.png')
img.save(out)
print(out, img.size)
