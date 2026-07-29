"""Generate the animated neofetch-style terminal card for the profile README.

Real ASCII-art portrait (luminance density ramp over assets/source-logo.png)
next to a live stats panel, inside terminal chrome: the art wipes in row by
row, the stats type themselves out, the language bars grow, and a CRT
scanline layer drifts over the whole thing forever.

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
    BG,
    BORDER,
    CYAN,
    DIM,
    FG,
    GREEN,
    MONO,
    ORANGE,
    PURPLE,
    cursor,
    defs_border_gradient,
    defs_glow,
    esc,
    grid_pattern,
    lang_color,
    scanlines,
    type_reveal,
    window_chrome,
)

USERNAME = "n3xtpy"
OUT_PATH = "assets/neofetch-card.svg"
SRC_IMAGE = "assets/source-logo.png"

RAMP = " .`:-=+*cs#%@"
BG_CUTOFF = 40  # luminance below this is background, rendered as a space

# A monospace cell is about twice as tall as it is wide, so a square source
# image needs twice as many columns as rows to come out square on screen.
ART_FONT = 6.0
ART_CHAR_W = ART_FONT * 0.6
ART_LINE_H = 7.0
ART_ROWS = 38
ART_COLS = ART_ROWS * 2
ART_X = 30
ART_W = ART_COLS * ART_CHAR_W

WIDTH = 880  # matches header.svg and langs.svg so the README columns line up
CHROME_H = 36
FIELD_X = ART_X + ART_W + 46
PANEL_W = WIDTH - FIELD_X - 36
FIELD_LINE_H = 21
FIELD_TOP = 86

BAR_X_OFFSET = 140
BAR_W = 200
BAR_H = 7


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
    top_langs = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)[:5]

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


def crop_to_ink(im, margin=0.03):
    """Trim the dead border off the source so the portrait fills its column.

    assets/source-logo.png is a 1022px square whose mark occupies only the
    middle half; sampled as-is, half the ASCII grid comes out blank.
    """
    bbox = im.point(lambda p: 255 if p >= BG_CUTOFF else 0).getbbox()
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


def build_ascii_art(path, cols, rows):
    im = crop_to_ink(Image.open(path).convert("L")).resize((cols, rows), Image.LANCZOS)
    ramp_max = len(RAMP) - 1
    lines = []
    for y in range(rows):
        row = []
        for x in range(cols):
            lum = im.getpixel((x, y))
            row.append(" " if lum < BG_CUTOFF else RAMP[int((lum / 255) * ramp_max)])
        lines.append("".join(row).rstrip())

    # Drop fully blank bands so the portrait can be centred on its own ink
    # rather than on the source image's padding.
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return lines


def build_fields(stats):
    """(label, value, label_color, value_color) rows for the info panel."""
    host = f"{stats['login']}@github"
    rows = [
        (host, "", ACCENT, FG),
        ("-" * max(14, len(host)), "", BORDER, FG),
        ("OS", "GitHub", ACCENT, FG),
        ("Uptime", f"since {stats['created']}" if stats["created"] else "unknown", ACCENT, FG),
        ("Shell", "bash + GitHub Actions", ACCENT, FG),
        ("Repos", str(stats["public_repos"]), ACCENT, FG),
        ("Stars", f"{stats['stars']}", ACCENT, ORANGE),
        ("Forks", str(stats["forks"]), ACCENT, FG),
        # Separate rows: runs of spaces collapse in SVG text without
        # xml:space="preserve", so "37   Following: 12" would render as one gap.
        ("Followers", str(stats["followers"]), ACCENT, FG),
        ("Following", str(stats["following"]), ACCENT, FG),
    ]
    if stats["location"]:
        rows.append(("Location", stats["location"], ACCENT, FG))
    return rows


def render_art(art_lines, art_top):
    """One <text> per row, each behind its own left-to-right wipe."""
    clips, elems = [], []
    for i, line in enumerate(art_lines):
        if not line:
            continue
        y = art_top + i * ART_LINE_H
        begin = 0.12 + i * 0.03
        width = ART_CHAR_W * len(line) + 4
        clips.append(type_reveal(f"artClip{i}", ART_X, y - ART_FONT, width, ART_LINE_H + 2, begin, 0.22))
        elems.append(
            f'<text x="{ART_X}" y="{y:.1f}" fill="url(#artFill)" font-family="{MONO}" '
            f'font-size="{ART_FONT}" clip-path="url(#artClip{i})" '
            f'xml:space="preserve">{esc(line)}</text>'
        )
    return "".join(clips), "\n  ".join(elems)


def render_fields(stats, start_t, field_x=FIELD_X):
    """Typed key/value rows, then the language bars, then the cursor."""
    fields = build_fields(stats)
    clips, elems = [], []
    t = start_t
    y = FIELD_TOP

    for i, (label, value, lcolor, vcolor) in enumerate(fields):
        text = label if not value else f"{label}: {value}"
        dur = max(0.22, len(text) * 0.022)
        clips.append(type_reveal(f"fClip{i}", field_x, y - 14, PANEL_W, 20, t, dur))
        weight = "700" if i == 0 else "400"
        size = 15 if i == 0 else 13
        if value:
            body = (
                f'<tspan fill="{lcolor}" font-weight="700">{esc(label)}</tspan>'
                f'<tspan fill="{DIM}">: </tspan>'
                f'<tspan fill="{vcolor}">{esc(value)}</tspan>'
            )
        else:
            body = f'<tspan fill="{lcolor}">{esc(label)}</tspan>'
        elems.append(
            f'<text x="{field_x}" y="{y:.1f}" font-family="{MONO}" font-size="{size}" '
            f'font-weight="{weight}" clip-path="url(#fClip{i})">{body}</text>'
        )
        t += dur * 0.55 + 0.05
        y += FIELD_LINE_H

    # Language section: a label, then one growing bar per language.
    y += 10
    clips.append(type_reveal("langHead", field_x, y - 14, PANEL_W, 20, t, 0.3))
    elems.append(
        f'<text x="{field_x}" y="{y:.1f}" font-family="{MONO}" font-size="13" font-weight="700" '
        f'fill="{ACCENT}" clip-path="url(#langHead)">Stack</text>'
    )
    t += 0.35

    top = stats["top_langs"]
    if not top:
        y += FIELD_LINE_H
        elems.append(
            f'<text x="{field_x}" y="{y:.1f}" font-family="{MONO}" font-size="13" '
            f'fill="{DIM}" opacity="0">n/a'
            f'<animate attributeName="opacity" values="0;1" begin="{t:.2f}s" dur="0.3s" fill="freeze"/>'
            f"</text>"
        )
    else:
        total = stats["lang_total"]
        bar_x = field_x + BAR_X_OFFSET
        for i, (lang, count) in enumerate(top):
            y += 24
            pct = count / total
            color = lang_color(lang, i)
            begin = t + i * 0.13
            elems.append(f'''
  <text x="{field_x}" y="{y + 5:.1f}" font-family="{MONO}" font-size="12.5" fill="{FG}" opacity="0">{esc(lang)}
    <animate attributeName="opacity" values="0;1" begin="{begin:.2f}s" dur="0.35s" fill="freeze"/>
  </text>
  <rect x="{bar_x}" y="{y - 4:.1f}" width="{BAR_W}" height="{BAR_H}" rx="{BAR_H / 2}" fill="{BORDER}" opacity="0">
    <animate attributeName="opacity" values="0;0.55" begin="{begin:.2f}s" dur="0.35s" fill="freeze"/>
  </rect>
  <rect x="{bar_x}" y="{y - 4:.1f}" width="0" height="{BAR_H}" rx="{BAR_H / 2}" fill="{color}">
    <animate attributeName="width" from="0" to="{BAR_W * pct:.1f}" begin="{begin:.2f}s"
             dur="0.85s" fill="freeze" calcMode="spline" keySplines="0.16 1 0.3 1"/>
  </rect>
  <text x="{bar_x + BAR_W + 12}" y="{y + 4:.1f}" font-family="{MONO}" font-size="11.5" fill="{DIM}" opacity="0">{pct * 100:.0f}%
    <animate attributeName="opacity" values="0;1" begin="{begin + 0.5:.2f}s" dur="0.35s" fill="freeze"/>
  </text>''')
        t += len(top) * 0.13 + 0.9

    y += 26
    elems.append(cursor(field_x, y - 12, begin=t))
    return "".join(clips), "\n  ".join(elems), y + 12


def render_svg(stats, art_lines):
    # The panel drives the card's height, so lay it out first, then centre the
    # portrait against whatever vertical space that produced.
    #
    # Start the panel typing while the portrait is still wiping in, so the two
    # halves read as one boot sequence rather than two queued animations.
    art_done = 0.12 + len(art_lines) * 0.03 + 0.22
    field_clips, field_elems, field_bottom = render_fields(stats, art_done * 0.45)

    art_h = len(art_lines) * ART_LINE_H
    height = int(max(field_bottom, CHROME_H + art_h + 48) + 10)
    width = WIDTH

    art_top = CHROME_H + (height - CHROME_H - art_h) / 2 + ART_FONT
    art_clips, art_elems = render_art(art_lines, art_top)

    scan_defs, scan_body = scanlines(width, height, opacity=0.05)
    title = f"{stats['login']}@github: ~ $ neofetch"

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"
     width="{width}" height="{height}" role="img" aria-label="neofetch card for {esc(stats['login'])}">
  <title>{esc(stats['login'])} — {stats['public_repos']} repos, {stats['stars']} stars, {stats['followers']} followers</title>
  <defs>
    {defs_border_gradient("edge", (ACCENT, PURPLE, GREEN))}
    {defs_glow("artglow", 1.6)}
    {grid_pattern("grid", 24)}
    {scan_defs}
    <linearGradient id="artFill" x1="0" y1="0" x2="0.4" y2="1">
      <stop offset="0%" stop-color="{CYAN}"/>
      <stop offset="50%" stop-color="{ACCENT}"/>
      <stop offset="100%" stop-color="{PURPLE}"/>
      <animate attributeName="x1" values="0;0.5;0" dur="8s" repeatCount="indefinite"/>
    </linearGradient>
    {art_clips}
    {field_clips}
  </defs>

  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" fill="{BG}"/>
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" fill="url(#grid)"/>
  {window_chrome(width, title)}

  <g filter="url(#artglow)">
  {art_elems}
  </g>

  {field_elems}

  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12"
        fill="none" stroke="url(#edge)" stroke-width="1.5" opacity="0.9"/>
  {scan_body}
</svg>
'''


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    try:
        stats = fetch_stats(username)
    except Exception as exc:  # network hiccup or rate limit
        print(f"skip: could not fetch stats for {username} ({exc}); keeping existing card")
        return 0

    art_lines = build_ascii_art(SRC_IMAGE, ART_COLS, ART_ROWS)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(render_svg(stats, art_lines))
    print(f"wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
