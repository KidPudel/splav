"""Splav in all six styles, Latin and Cyrillic together: specimens/splav.png."""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = lambda *p: os.path.join(ROOT, *p)
STYLES = ['Light', 'Regular', 'Bold', 'LightItalic', 'Italic', 'BoldItalic']
splav = lambda s, size=64: ImageFont.truetype(F('fonts', 'ttf', f'Splav-{s}.ttf'), size)

img = Image.new('RGB', (2600, 1420), 'white')
d = ImageDraw.Draw(img)
y = 20
for s in STYLES:
    d.text((30, y), 'In product design, I look for oddities* — я ищу странности (2026)', font=splav(s), fill='black')
    y += 100
y += 40
for s in ('Regular', 'Italic'):
    d.text((30, y), 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ', font=splav(s), fill='black')
    d.text((30, y + 100), 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя 0123456789', font=splav(s), fill='black')
    y += 220
d.text((30, y + 20), '«Съешь же ещё этих мягких французских булок, да выпей чаю!»', font=splav('Bold'), fill='black')
img.save(F('specimens', 'splav.png'))
print(F('specimens', 'splav.png'))
