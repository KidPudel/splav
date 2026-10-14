"""Make static instances of every corpus family: roman 300, 400 and 700,
italic 300, 400 and 700 (300 is only needed for Averia, the reference)."""
import glob
import json
import os

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(ROOT, 'build', 'corpus')
OUT = os.path.join(ROOT, 'build', 'instances')
os.makedirs(OUT, exist_ok=True)

STATIC_NAMES = {
    ('roman', 300): ['Light'],
    ('roman', 400): ['Regular', 'Web-Regular'],
    ('roman', 700): ['Bold', 'Web-Bold'],
    ('italic', 300): ['LightItalic'],
    ('italic', 400): ['Italic', 'Web-Italic'],
    ('italic', 700): ['BoldItalic', 'Web-BoldItalic'],
}


def is_italic_file(name):
    return 'Italic' in name


def make_instance(path, wght, out_path):
    font = TTFont(path)
    if 'fvar' not in font:
        font.save(out_path)
        return True
    axes = {a.axisTag: a for a in font['fvar'].axes}
    if wght < axes['wght'].minValue or wght > axes['wght'].maxValue:
        return False
    loc = {'wght': wght}
    for tag, axis in axes.items():
        if tag == 'wght':
            continue
        if tag == 'wdth':
            loc[tag] = 100
        elif tag == 'GRAD':
            loc[tag] = 0
        else:
            loc[tag] = axis.defaultValue
    inst = instantiateVariableFont(font, loc, inplace=False)
    inst.save(out_path)
    return True


manifest = {}
for fam_dir in sorted(glob.glob(os.path.join(CORPUS, '*'))):
    fam = os.path.basename(fam_dir)
    files = sorted(glob.glob(os.path.join(fam_dir, '*.ttf')))
    entry = {}
    for (style, wght), names in STATIC_NAMES.items():
        key = f'{style}{wght}'
        out_path = os.path.join(OUT, f'{fam}-{key}.ttf')
        done = False
        # Variable font first.
        for f in files:
            base = os.path.basename(f)
            if '[' not in base or is_italic_file(base) != (style == 'italic'):
                continue
            done = make_instance(f, wght, out_path)
            break
        if not done:
            for f in files:
                base = os.path.basename(f)
                if '[' in base:
                    continue
                suffix = base.rsplit('-', 1)[-1].replace('.ttf', '')
                web = base.split('-', 1)[-1].replace('.ttf', '')
                if suffix in names or web in names:
                    TTFont(f).save(out_path)
                    done = True
                    break
        if done:
            entry[key] = out_path
    manifest[fam] = entry
    print(fam, sorted(entry))

json.dump(manifest, open(os.path.join(ROOT, 'build', 'manifest.json'), 'w'), indent=1)
