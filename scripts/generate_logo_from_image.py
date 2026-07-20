"""Turn assets/source-logo.png into an animated pixel-mosaic SVG.

Downsamples the source image to a coarse grid, then re-renders each cell as
an SVG rect that wipes in diagonally -- same visual language as the
contribution heatmap (assets/heatmap.svg), so the header and the graph read
as one system.
"""
import sys
from PIL import Image

SRC = "assets/source-logo.png"
OUT = "assets/logo.svg"
GRID = 16          # cells per side
CANVAS = 200        # output svg size (px)
THRESHOLD = 128      # luminance cutoff: below = mark color, above = bg


def load_grid(path, grid):
    im = Image.open(path).convert("L")
    im = im.resize((grid, grid), Image.LANCZOS)
    return [[im.getpixel((x, y)) for x in range(grid)] for y in range(grid)]


def render_svg(pixels, grid, canvas):
    cell = canvas / grid
    rects = []
    delay = 0.0
    step = 1.4 / (grid * grid)
    for y in range(grid):
        for x in range(grid):
            lum = pixels[y][x]
            if lum < THRESHOLD:
                continue  # dark source pixel = background, stays transparent
            px, py = x * cell, y * cell
            rects.append(f'''
      <rect x="{px:.2f}" y="{py:.2f}" width="{cell:.2f}" height="{cell:.2f}" fill="#ffffff" opacity="0">
        <animate attributeName="opacity" from="0" to="1" begin="{delay:.3f}s" dur="0.25s" fill="freeze"/>
      </rect>''')
            delay += step

    svg = f'''<svg viewBox="0 0 {canvas} {canvas}" xmlns="http://www.w3.org/2000/svg" width="120" height="120">
  <style>
    @keyframes pulse {{
      0%   {{ opacity: 1;   transform: scale(1); }}
      50%  {{ opacity: .82; transform: scale(1.03); }}
      100% {{ opacity: 1;   transform: scale(1); }}
    }}
    .mosaic {{ transform-origin: {canvas/2}px {canvas/2}px; animation: pulse 3s ease-in-out {delay + 0.3:.2f}s infinite; }}
  </style>
  <rect x="0" y="0" width="{canvas}" height="{canvas}" rx="18" fill="#111111"/>
  <g class="mosaic">{''.join(rects)}
  </g>
</svg>'''
    return svg


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else SRC
    pixels = load_grid(src, GRID)
    svg = render_svg(pixels, GRID, CANVAS)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
