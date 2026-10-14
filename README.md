# Splav

**Splav** (Сплав, "alloy") is a Cyrillic companion to [Averia Serif Libre](https://fonts.google.com/specimen/Averia+Serif+Libre), made the way Averia was made: by averaging.

Averia's designer, Dan Sayers, split the outline of every letter in every font into hundreds of points and averaged them. Corners that sit in slightly different places in each font melt into soft, rounded shapes, which is where Averia's character comes from. Averia has no Cyrillic. Splav adds it with the same method, so the softness comes from the averaging, not from imitation.

The name is about the method and the material: many fonts melted into one, and the type alloy («типографский сплав») metal type was cast from.

![Splav next to Averia](specimens/splav.png)

**[Try it in the browser](https://kidpudel.github.io/splav/)** · **[Download](https://github.com/KidPudel/splav/releases/latest)**

## Status

Version 0.1. Two styles, Cyrillic only (А–я, Ё ё):

| Style | Pairs with | Files |
| --- | --- | --- |
| Light | Averia Serif Libre Light | `fonts/ttf/Splav-Light.ttf`, `fonts/woff2/Splav-Light.woff2` |
| Bold Italic | Averia Serif Libre Bold Italic | `fonts/ttf/Splav-BoldItalic.ttf`, `fonts/woff2/Splav-BoldItalic.woff2` |

There is no kerning, no Latin, digits or punctuation yet: use Splav next to Averia, which supplies those.

## Use on the web

Load Averia from Google Fonts and Splav from jsDelivr, then list Averia first. Averia has no Cyrillic, so the browser takes the Cyrillic letters from Splav:

```html
<link href="https://fonts.googleapis.com/css2?family=Averia+Serif+Libre:ital,wght@0,300;1,700&display=swap" rel="stylesheet">
```

```css
@font-face {
  font-family: 'Splav';
  src: url('https://cdn.jsdelivr.net/gh/KidPudel/splav@v0.1.0/fonts/woff2/Splav-Light.woff2') format('woff2');
  font-weight: 300;
}

@font-face {
  font-family: 'Splav';
  src: url('https://cdn.jsdelivr.net/gh/KidPudel/splav@v0.1.0/fonts/woff2/Splav-BoldItalic.woff2') format('woff2');
  font-weight: 700;
  font-style: italic;
}

body {
  font-family: 'Averia Serif Libre', 'Splav', serif;
  font-weight: 300;
}
```

On the desktop, install the `.ttf` files from the [download](https://github.com/KidPudel/splav/releases/latest) and set Cyrillic text in Splav, Latin in Averia Serif Libre.

## How it is made

1. **Sources.** 18 open-licence text serifs with well-made Cyrillic, chosen from every serif with Cyrillic on Google Fonts. Fonts with Bulgarian or old letter forms in their upright style, and display faces, were left out, so the average is not pulled towards shapes Russian readers would find wrong. See [SOURCES.md](SOURCES.md) and the sheets in `specimens/`.
2. **The method, checked on Latin first.** The same averaging applied to the sources' Latin letters reproduces Averia's look and overlaps the real Averia by 73–83% before fitting and 81–86% after (`specimens/latin-check-roman400.png`). That fit (width, height, weight, slant) is then applied to the Cyrillic.
3. **Averaging** (`scripts/avg.py`). Each glyph is cleaned of overlaps, every contour is resampled into 320 evenly spaced points, contours are matched across fonts (same structure, same direction, best cyclic start), and the points are averaged. Fonts that draw a letter in a different form (for example the two italic «в») are left out of that letter, as are far outliers, so two forms never blend into mush.
4. **Shared shapes.** Letters that look the same as Latin (А В Е М Н О Р С Т Х, а е о р с у х, Ё ё) use Averia's own outlines, as Cyrillic extensions usually do.
5. **Outlines** are written as smooth quadratic splines and exported as TTF and WOFF2 (`scripts/build.py`).

## Rebuild

```sh
sh scripts/build_all.sh
```

It creates a Python environment in `.venv`, downloads the sources into `build/` (about 55 MB, not kept in the repository), makes static instances, fits the averages to Averia, builds both styles and renders `specimens/splav.png`.

## Licence

Splav is free and open: [SIL Open Font License 1.1](OFL.txt), with no Reserved Font Name. It includes Averia Serif Libre's outlines and is derived from 18 OFL fonts, all credited in `OFL.txt`. It does not use any of their reserved names, including "Averia".

Made by Igor Kupchinenko, 2026.
