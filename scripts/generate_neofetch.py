"""Generate the profile card: a portrait of the logo mark next to live stats.

The mark on the left is sampled straight out of assets/source-logo.png and
re-drawn as a grid of cells, each one's opacity set by the luminance it
covers. Two reasons to draw cells rather than ASCII characters: the mark is
essentially a binary shape, so a density ramp over it comes out as uniform
character mush, and glyph art depends on the viewer having a font with those
glyphs while rects always render. The cells also echo the contribution grid
further down the README, so the two cards read as one system.

Stats come from the unauthenticated GitHub REST API -- no token needed, and
60 requests/hour is plenty for a daily cron. If the API is unreachable or
rate-limited the script leaves the existing card untouched and exits clean,
so a bad network day can never blank the README.
"""
import sys

import requests
from PIL import Image

from theme import (
    ACCENT,
    BORDER,
    CARD_W,
    CYAN,
    DIM,
    FAINT,
    FG,
    GREEN,
    MONO,
    ORANGE,
    PAD,
    PURPLE,
    card_border,
    card_shell,
    card_title,
    appear,
    defs_card,
    esc,
    fade_in,
    grow_w,
    lang_color,
    stat_block,
)

USERNAME = "n3xtpy"
OUT_PATH = "assets/neofetch-card.svg"
SRC_IMAGE = "assets/source-logo.png"

# --- portrait -------------------------------------------------------------
ART_CELLS = 46          # cells per side; the source is square
ART_SIZE = 258          # on-screen size of the whole portrait, in px
ART_GAP = 0.16          # share of a cell pitch left as gutter
INK_CUTOFF = 0.14       # normalised luminance below this is background

# --- panel ----------------------------------------------------------------
ART_X = PAD + 6
PANEL_X = ART_X + ART_SIZE + 46
PANEL_W = CARD_W - PAD - PANEL_X
VALUE_X = PANEL_X + 112   # info values share one column, so they line up

CONTENT_TOP = 74
INFO_LH = 21
LANG_LH = 25
BAR_W = 150
BAR_H = 6


def fetch_stats(username):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-readme-bot",
    }
    r = requests.get(f"https://api.github.com/users/{username}", headers=headers, timeout=15)
    r.raise_for_status()
    user = r.json()

    repos = requests.get(
        f"https://api.github.com/users/{username}/repos?per_page=100&sort=pushed",
        headers=headers,
        timeout=15,
    )
    repos.raise_for_status()
    repos = repos.json()
    repos = repos if isinstance(repos, list) else []

    stars = sum(repo.get("stargazers_count", 0) for repo in repos)
    forks = sum(repo.get("forks_count", 0) for repo in repos)

    langs = {}
    for repo in repos:
        lang = repo.get("language")
        if lang:
            langs[lang] = langs.get(lang, 0) + 1
    top_langs = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)[:4]

    return {
        "login": user.get("login", username),
        "name": user.get("name") or user.get("login", username),
        "public_repos": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "stars": stars,
        "forks": forks,
        "top_langs": top_langs,
        "lang_total": max(1, sum(count for _, count in top_langs)),
        "created": (user.get("created_at") or "")[:4],
        "location": user.get("location") or "",
    }


def crop_to_ink(im, margin=0.02):
    """Trim the dead border off the source so the mark fills its column.

    assets/source-logo.png is a 1022px square whose mark occupies only the
    middle half; sampled as-is, half the grid comes out blank.
    """
    bbox = im.point(lambda p: 255 if p >= 40 else 0).getbbox()
    if not bbox:
        return im
    pad = int(max(im.size) * margin)
    left, top, right, bottom = bbox
    return im.crop((
        max(0, left - pad),
        max(0, top - pad),
        min(im.size[0], right + pad),
        min(im.size[1], bottom + pad),
    ))


def sample_mark(path, cells=ART_CELLS):
    """[(col, row, intensity)] for every cell the mark actually covers.

    Luminance is stretched across the range the source actually uses, so the
    body of the mark comes out solid and only the antialiased edges land
    part-way down the scale -- which is what gives the portrait soft corners
    instead of a jagged stencil.
    """
    im = crop_to_ink(Image.open(path).convert("L")).resize((cells, cells), Image.LANCZOS)
    pixels = [im.getpixel((x, y)) for y in range(cells) for x in range(cells)]
    lo, hi = min(pixels), max(pixels)
    span = max(1, hi - lo)

    out = []
    for row in range(cells):
        for col in range(cells):
            level = (im.getpixel((col, row)) - lo) / span
            if level >= INK_CUTOFF:
                out.append((col, row, level))
    return out


def render_mark(cells, top):
    """The portrait: cells wash in on a diagonal, then hold."""
    pitch = ART_SIZE / ART_CELLS
    size = pitch * (1 - ART_GAP)
    span = 1.5
    denom = max(1, (ART_CELLS - 1) * 2)

    parts = []
    for col, row, level in cells:
        x = ART_X + col * pitch
        y = top + row * pitch
        begin = 0.15 + (col + row) / denom * span
        # Floor the opacity so faint edge cells still register as edges.
        opacity = 0.30 + 0.70 * level
        parts.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{size:.2f}" height="{size:.2f}" '
            f'rx="{size / 4:.2f}" fill="url(#markFill)" opacity="{opacity:.2f}">'
            f"{appear(f'{opacity:.2f}', begin, 0.5)}</rect>"
        )
    return "".join(parts), span + 0.5


def render_panel(stats, start_t):
    """Name, headline numbers, key/value rows, language bars. Returns SVG + bottom."""
    parts = []
    t = start_t

    # Identity.
    y = CONTENT_TOP + 30
    parts.append(f'''<g>
    {fade_in(t, 0.5, shift=8)}
    <text x="{PANEL_X}" y="{y}" fill="{FG}" font-family="{MONO}" font-size="25"
          font-weight="700" letter-spacing="-0.8">{esc(stats["login"])}</text>
    <text x="{PANEL_X}" y="{y + 21}" fill="{DIM}" font-family="{MONO}" font-size="12.5">github.com/{esc(stats["login"])}</text>
  </g>''')
    t += 0.2

    y += 39
    parts.append(
        f'<line x1="{PANEL_X}" y1="{y}" x2="{CARD_W - PAD}" y2="{y}" '
        f'stroke="{BORDER}" stroke-width="1"/>'
    )

    # Headline numbers -- the one place on the card that gets to be loud.
    # A zero gets the muted treatment: colour is for numbers worth reading.
    figures = [
        (stats["public_repos"], "repos", FG),
        (stats["stars"], "stars", ORANGE),
        (stats["followers"], "followers", ACCENT),
        (stats["forks"], "forks", PURPLE),
    ]
    figures = [(f"{n}", label, color if n else FAINT) for n, label, color in figures]
    step = PANEL_W / len(figures)
    y += 34
    for i, (value, label, color) in enumerate(figures):
        parts.append(stat_block(PANEL_X + i * step, y, value, label, color, begin=t + i * 0.1))
    t += len(figures) * 0.1 + 0.25

    y += 36
    parts.append(
        f'<line x1="{PANEL_X}" y1="{y}" x2="{CARD_W - PAD}" y2="{y}" '
        f'stroke="{BORDER}" stroke-width="1"/>'
    )

    # Key/value rows. Values share one x so the column reads as a table.
    rows = [
        ("os", "GitHub"),
        ("uptime", f"since {stats['created']}" if stats["created"] else "unknown"),
        ("shell", "bash + GitHub Actions"),
        ("following", str(stats["following"])),
    ]
    if stats["location"]:
        rows.append(("location", stats["location"]))

    y += 28
    for i, (label, value) in enumerate(rows):
        ry = y + i * INFO_LH
        parts.append(f'''<g>
    {fade_in(t + i * 0.07, 0.4)}
    <text x="{PANEL_X}" y="{ry}" fill="{DIM}" font-family="{MONO}" font-size="12.5">{esc(label)}</text>
    <text x="{VALUE_X}" y="{ry}" fill="{FG}" font-family="{MONO}" font-size="12.5">{esc(value)}</text>
  </g>''')
    t += len(rows) * 0.07 + 0.3
    y += (len(rows) - 1) * INFO_LH + 20

    parts.append(
        f'<line x1="{PANEL_X}" y1="{y}" x2="{CARD_W - PAD}" y2="{y}" '
        f'stroke="{BORDER}" stroke-width="1"/>'
    )

    # Languages, by repo count -- the byte-level breakdown gets its own card.
    y += 26
    parts.append(f'''<g>
    {fade_in(t, 0.4)}
    <text x="{PANEL_X}" y="{y}" fill="{GREEN}" font-family="{MONO}" font-size="12"
          font-weight="700" letter-spacing="1.4">STACK</text>
  </g>''')
    t += 0.2

    top = stats["top_langs"]
    bar_x = CARD_W - PAD - BAR_W - 44
    if not top:
        y += LANG_LH
        parts.append(
            f'<g>{fade_in(t, 0.4)}'
            f'<text x="{PANEL_X}" y="{y}" fill="{DIM}" font-family="{MONO}" font-size="12.5">'
            f"no public repos yet</text></g>"
        )
    else:
        total = stats["lang_total"]
        for i, (lang, count) in enumerate(top):
            y += LANG_LH
            pct = count / total
            color = lang_color(lang, i)
            begin = t + i * 0.1
            parts.append(f'''
  <g>
    <g>{fade_in(begin, 0.4)}
      <text x="{PANEL_X}" y="{y + 5}" fill="{FG}" font-family="{MONO}" font-size="12.5">{esc(lang)}</text>
      <text x="{CARD_W - PAD}" y="{y + 5}" fill="{DIM}" font-family="{MONO}" font-size="11.5"
            text-anchor="end">{pct * 100:.0f}%</text>
      <rect x="{bar_x}" y="{y - 3}" width="{BAR_W}" height="{BAR_H}" rx="{BAR_H / 2}"
            fill="{BORDER}"/>
    </g>
    <rect x="{bar_x}" y="{y - 3}" width="{BAR_W * pct:.2f}" height="{BAR_H}" rx="{BAR_H / 2}" fill="{color}">
      {grow_w(BAR_W * pct, begin + 0.15)}
    </rect>
  </g>''')
        t += len(top) * 0.1 + 0.85

    return "\n  ".join(parts), y + 16


def render_svg(stats, cells):
    panel, panel_bottom = render_panel(stats, 0.35)

    height = int(max(panel_bottom + 12, CONTENT_TOP + ART_SIZE + 30))
    art_top = CONTENT_TOP + (height - CONTENT_TOP - ART_SIZE) / 2 - 6
    mark, _ = render_mark(cells, art_top)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CARD_W} {height}"
     width="{CARD_W}" height="{height}" role="img" aria-label="profile card for {esc(stats['login'])}">
  <title>{esc(stats['login'])} — {stats['public_repos']} repos, {stats['stars']} stars, {stats['followers']} followers</title>
  <defs>
    {defs_card(CARD_W, height)}
    <!-- userSpaceOnUse, not the default: an objectBoundingBox gradient would
         restart inside every 5px cell and the whole mark would come out flat. -->
    <linearGradient id="markFill" gradientUnits="userSpaceOnUse"
                    x1="{ART_X}" y1="{art_top}"
                    x2="{ART_X + ART_SIZE}" y2="{art_top + ART_SIZE}">
      <stop offset="0%" stop-color="{CYAN}"/>
      <stop offset="55%" stop-color="{ACCENT}"/>
      <stop offset="100%" stop-color="{PURPLE}"/>
    </linearGradient>
  </defs>

  {card_shell(CARD_W, height)}
  {card_title(CARD_W, "profile", meta=f"~ $ neofetch {esc(stats['login'])}")}

  <g>{mark}</g>

  {panel}

  {card_border(CARD_W, height)}
</svg>
'''


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    try:
        stats = fetch_stats(username)
    except Exception as exc:  # network hiccup or rate limit
        print(f"skip: could not fetch stats for {username} ({exc}); keeping existing card")
        return 0

    cells = sample_mark(SRC_IMAGE)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(render_svg(stats, cells))
    print(f"wrote {OUT_PATH} ({len(cells)} mark cells)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
