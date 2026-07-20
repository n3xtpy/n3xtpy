"""Generate an animated neofetch-style terminal card SVG for the GitHub
profile README: real ASCII-art portrait (density-ramp technique, same as
the blog's photo pipeline) + a stats panel, inside a terminal-chrome window.

Stats come from the unauthenticated GitHub REST API (no token, 60 req/hr is
plenty for a daily cron). Portrait comes from assets/source-logo.png.
"""
import sys
import requests
from PIL import Image

USERNAME = "n3xtpy"
OUT_PATH = "assets/neofetch-card.svg"
SRC_IMAGE = "assets/source-logo.png"

RAMP = " .`:-=+*cs#%@"
ART_COLS = 44
ART_ROWS = 44
BG_CUTOFF = 40  # luminance below this = background, rendered as space

BG = "#0d1117"
CHROME = "#161b22"
BORDER = "#30363d"
FG = "#c9d1d9"
ACCENT = "#58a6ff"
DIM = "#8b949e"
DOTS = ["#ff5f56", "#ffbd2e", "#27c93f"]


def fetch_stats(username):
    headers = {"Accept": "application/vnd.github+json"}
    r = requests.get(f"https://api.github.com/users/{username}", headers=headers, timeout=10)
    r.raise_for_status()
    user = r.json()

    repos = requests.get(
        f"https://api.github.com/users/{username}/repos?per_page=100",
        headers=headers, timeout=10,
    ).json()
    repos = repos if isinstance(repos, list) else []
    stars = sum(repo.get("stargazers_count", 0) for repo in repos)
    langs = {}
    for repo in repos:
        lang = repo.get("language")
        if lang:
            langs[lang] = langs.get(lang, 0) + 1
    top_langs = sorted(langs, key=langs.get, reverse=True)[:5]

    return {
        "login": user.get("login", username),
        "public_repos": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "stars": stars,
        "top_langs": top_langs,
        "created": (user.get("created_at") or "")[:4],
    }


def build_ascii_art(path, cols, rows):
    im = Image.open(path).convert("L").resize((cols, rows), Image.LANCZOS)
    ramp_max = len(RAMP) - 1
    lines = []
    for y in range(rows):
        row = []
        for x in range(cols):
            lum = im.getpixel((x, y))
            if lum < BG_CUTOFF:
                row.append(" ")
            else:
                row.append(RAMP[int((lum / 255) * ramp_max)])
        lines.append("".join(row))
    return lines


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_fields(stats):
    lang_rows = [(f"  {lang}", FG, False) for lang in stats["top_langs"]] or [("  n/a", DIM, False)]
    return [
        (f"{stats['login']}@github", ACCENT, True),
        ("-" * max(10, len(stats["login"]) + 7), DIM, False),
        ("OS: GitHub", FG, False),
        (f"Uptime: since {stats['created']}", FG, False),
        (f"Repos: {stats['public_repos']}", FG, False),
        (f"Stars: {stats['stars']}", FG, False),
        (f"Followers: {stats['followers']}  Following: {stats['following']}", FG, False),
        ("", FG, False),
        ("Stack:", ACCENT, True),
        *lang_rows,
    ]


def render_svg(stats, art_lines):
    art_font = 6.2
    art_line_h = 7.6
    art_char_w = 3.7
    art_x = 24
    art_y = 74
    art_h = art_line_h * len(art_lines)

    field_line_h = 20
    field_x = art_x + art_char_w * ART_COLS + 40
    field_top = 74
    fields = build_fields(stats)
    field_h = field_line_h * len(fields)

    body_h = max(art_h, field_h)
    height = int(field_top + body_h + 40)
    width = int(field_x + 420)

    art_tspans = "".join(
        f'<tspan x="{art_x}" dy="{art_line_h if i else 0}">{esc(line)}</tspan>'
        for i, line in enumerate(art_lines)
    )

    field_elems = []
    delay = 0.15
    for i, (text, color, bold) in enumerate(fields):
        if not text:
            continue
        y = field_top + i * field_line_h
        weight = "700" if bold else "400"
        dur = max(0.25, len(text) * 0.025)
        field_elems.append(f'''
      <text x="{field_x}" y="{y}" fill="{color}" font-family="'Fira Code', Consolas, monospace"
            font-size="13" font-weight="{weight}" clip-path="url(#reveal{i})">{esc(text)}</text>
      <clipPath id="reveal{i}">
        <rect x="{field_x}" y="{y - 13}" width="0" height="18">
          <animate attributeName="width" from="0" to="420" begin="{delay:.2f}s" dur="{dur:.2f}s" fill="freeze" calcMode="linear"/>
        </rect>
      </clipPath>''')
        delay += dur + 0.04

    svg = f'''<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <style>
    text {{ font-family: 'Fira Code', Consolas, monospace; }}
    .cursor {{ animation: blink 1s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
  </style>
  <rect x="0" y="0" width="{width}" height="{height}" rx="10" fill="{BG}" stroke="{BORDER}"/>
  <rect x="0" y="0" width="{width}" height="34" rx="10" fill="{CHROME}"/>
  <rect x="0" y="24" width="{width}" height="10" fill="{CHROME}"/>
  <circle cx="20" cy="17" r="6" fill="{DOTS[0]}"/>
  <circle cx="40" cy="17" r="6" fill="{DOTS[1]}"/>
  <circle cx="60" cy="17" r="6" fill="{DOTS[2]}"/>
  <text x="{width/2}" y="21" fill="{DIM}" font-size="12" text-anchor="middle">{stats['login']}@github: ~ $ neofetch</text>

  <text x="{art_x}" y="{art_y}" fill="{FG}" font-size="{art_font}" xml:space="preserve">{art_tspans}</text>
  {''.join(field_elems)}

  <rect class="cursor" x="{field_x}" y="{field_top + len(fields) * field_line_h - 10}" width="7" height="12" fill="{FG}">
    <animate attributeName="opacity" begin="{delay:.2f}s" from="0" to="1" dur="0.1s" fill="freeze"/>
  </rect>
</svg>'''
    return svg


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    stats = fetch_stats(username)
    art_lines = build_ascii_art(SRC_IMAGE, ART_COLS, ART_ROWS)
    svg = render_svg(stats, art_lines)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
