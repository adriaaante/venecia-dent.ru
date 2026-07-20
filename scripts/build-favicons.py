#!/usr/bin/env python3
"""Венеция — рендер PNG-логотипов и фавиконок из assets/img/logo.svg.

Запуск из корня репо:  python3 scripts/build-favicons.py
Требует: pip install cairosvg pillow

На выходе:
  assets/img/logo.png       — мастер 512x512 (прозрачный фон) для JSON-LD/OG
  assets/img/logo-mark.png  — знак для шапки 192x192
  assets/img/watermark.png  — знак для будущего портфолио 640x640
  assets/img/favicon-16.png / favicon-32.png / favicon-180.png
  assets/img/favicon.ico    — 16+32+48
"""
import io

import cairosvg
from PIL import Image

SVG = 'assets/img/logo.svg'
OUT = 'assets/img/'


def render(size: int) -> Image.Image:
    png = cairosvg.svg2png(url=SVG, output_width=size, output_height=size)
    return Image.open(io.BytesIO(png)).convert('RGBA')


render(512).save(OUT + 'logo.png')
render(192).save(OUT + 'logo-mark.png')
render(640).save(OUT + 'watermark.png')

for s in (16, 32, 180):
    render(s).save(OUT + f'favicon-{s}.png')

ico_sizes = [16, 32, 48]
imgs = [render(s) for s in ico_sizes]
imgs[0].save(OUT + 'favicon.ico', sizes=[(s, s) for s in ico_sizes],
             append_images=imgs[1:])
print('favicons done')
