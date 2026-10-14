"""Splav next to Averia Serif Libre: specimens/splav.png."""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = lambda *p: os.path.join(ROOT, *p)
L = ImageFont.truetype(F('fonts', 'ttf', 'Splav-Light.ttf'), 64)
B = ImageFont.truetype(F('fonts', 'ttf', 'Splav-BoldItalic.ttf'), 64)
AL = ImageFont.truetype(F('build', 'corpus', 'averiaseriflibre', 'AveriaSerifLibre-Light.ttf'), 64)
AB = ImageFont.truetype(F('build', 'corpus', 'averiaseriflibre', 'AveriaSerifLibre-BoldItalic.ttf'), 64)

img = Image.new('RGB', (2600, 900), 'white')
d = ImageDraw.Draw(img)
d.text((30, 20), 'In product design, I look for', font=AL, fill='black')
d.text((1000, 20), 'oddities', font=AB, fill='black')
d.text((30, 120), 'В продуктовом дизайне я ищу', font=L, fill='black')
d.text((1000, 120), 'странности', font=B, fill='black')
d.text((30, 240), 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ', font=L, fill='black')
d.text((30, 340), 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя', font=L, fill='black')
d.text((30, 460), 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ', font=B, fill='black')
d.text((30, 560), 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя', font=B, fill='black')
d.text((30, 680), 'взаимодействия сам собираю то что проектирую', font=B, fill='black')
d.text((30, 780), 'Съешь же ещё этих мягких французских булок', font=L, fill='black')
img.save(F('specimens', 'splav.png'))
print(F('specimens', 'splav.png'))
