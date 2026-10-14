# Sources

Every serif family on Google Fonts with Cyrillic was considered (67 families, October 2026). CJK families, small-caps and unicase cuts, duplicates and slab serifs were set aside first. The remaining candidates were rendered side by side (`specimens/sources-*.png`) and checked for Russian letter forms in the upright style and true cursive forms in the italic.

## Averaged (18)

Each Splav style averages the nearest weight that all 18 families have, then is fitted to the matching Averia Serif Libre style. Most sources have no Light, so the Light styles start from Regular and the fit makes them lighter.

| Splav | Sources | Fitted to Averia |
| --- | --- | --- |
| Light | Regular (400) | Light |
| Regular | Regular (400) | Regular |
| Bold | Bold (700) | Bold |
| Light Italic | Italic (400) | Light Italic |
| Italic | Italic (400) | Italic |
| Bold Italic | Bold Italic (700) | Bold Italic |

| Family | Designers (from the font files) |
| --- | --- |
| PT Serif | A. Korolkova, O. Umpeleva, V. Yefimov (ParaType) |
| Lora | Olga Karpushina, Alexei Vanyashin (Cyrillic), Cyreal |
| Literata | Veronika Burian, Jose Scaglione and others (TypeTogether) |
| Merriweather | Eben Sorkin |
| Source Serif 4 | Frank Grießhammer (Adobe) |
| Spectral | Jean-Baptiste Levée (Production Type) |
| IBM Plex Serif | Mike Abbink, Paul van der Laan, Pieter van Rosmalen |
| Noto Serif | Monotype Design Team |
| Roboto Serif | Greg Gazdowicz (Commercial Type) |
| EB Garamond | Georg Duffner, Octavio Pardo |
| Alegreya | Juan Pablo del Peral (Huerta Tipográfica) |
| Vollkorn | Friedrich Althausen |
| STIX Two Text | Ross Mills, John Hudson, Paul Hanslow (Tiro Typeworks) |
| Charis SIL | SIL International |
| Gentium Book Plus | SIL International |
| Libertinus Serif | Philipp H. Poll, Khaled Hosny |
| Piazzolla | Juan Pablo del Peral (Huerta Tipográfica) |
| Brygada 1918 | Mateusz Machalski, Borys Kosmynka, Przemek Hoffer |

## Left out

| Family | Why |
| --- | --- |
| Cormorant Garamond, Ledger, Bona Nova | Upright «Д», «Л», «л» in Bulgarian or old forms (Λ-shaped) |
| Prata, Oranienbaum, Playfair Display, Old Standard TT | Display or high-contrast Didone faces |
| Alice, Kurale, Gabriela | Strong individual quirks that would pull the average |

## Per letter

`build/report-<style>.json`, written by each build, list for every letter how many fonts were averaged and which were left out and why (different contour structure, a different form, or a far outlier).
