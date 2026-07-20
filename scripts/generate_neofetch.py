"""Generate an animated neofetch-style info card SVG for the GitHub profile README.

Pulls public stats via the unauthenticated GitHub REST API (no token needed,
60 req/hr is plenty for a daily cron) and renders a terminal-style card with
a typing-reveal animation per line.
"""
import sys
import requests

USERNAME = "n3xt-agency"
OUT_PATH = "assets/neofetch-card.svg"

ASCII_GLYPH = [
    " ##      ##",
    " ###     ##",
    " ####    ##",
    " ## ##   ##",
    " ##  ##  ##",
    " ##   ## ##",
    " ##    ####",
    " ##     ###",
    " ##      ##",
]

BG = "#0d1117"
FG = "#c9d1d9"
ACCENT = "#58a6ff"
DIM = "#8b949e"


def fetch_stats(username):
    headers = {"Accept": "application/vnd.github+json"}
    r = requests.get(f"https://api.github.com/users/{username}", headers=headers, timeout=10)
    r.raise_for_status()
    user = r.json()

    repos = requests.get(
        f"https://api.github.com/users/{username}/repos?per_page=100",
        headers=headers, timeout=10,
    ).json()
    stars = sum(repo.get("stargazers_count", 0) for repo in repos) if isinstance(repos, list) else 0
    langs = {}
    if isinstance(repos, list):
        for repo in repos:
            lang = repo.get("language")
            if lang:
                langs[lang] = langs.get(lang, 0) + 1
    top_lang = max(langs, key=langs.get) if langs else "n/a"

    return {
        "login": user.get("login", username),
        "name": user.get("name") or user.get("login", username),
        "public_repos": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "stars": stars,
        "top_lang": top_lang,
        "created": (user.get("created_at") or "")[:4],
    }


def build_lines(stats):
    return [
        (f"{stats['login']}@github", ACCENT, True),
        ("-" * max(10, len(stats["login"]) + 7), DIM, False),
        (f"OS: GitHub", FG, False),
        (f"Uptime: since {stats['created']}", FG, False),
        (f"Repos: {stats['public_repos']}", FG, False),
        (f"Stars: {stats['stars']}", FG, False),
        (f"Followers: {stats['followers']}  Following: {stats['following']}", FG, False),
        (f"Top Lang: {stats['top_lang']}", FG, False),
    ]


def render_svg(stats):
    lines = build_lines(stats)
    line_h = 22
    top_pad = 40
    height = top_pad + line_h * len(lines) + 30
    glyph_x = 20
    text_x = 20 + 12 * 11 + 30

    glyph_tspans = "".join(
        f'<tspan x="{glyph_x}" dy="16">{row}</tspan>' for row in ASCII_GLYPH
    )

    text_elems = []
    delay = 0.0
    for i, (text, color, bold) in enumerate(lines):
        y = top_pad + i * line_h
        weight = "700" if bold else "400"
        dur = max(0.3, len(text) * 0.03)
        text_elems.append(f'''
        <text x="{text_x}" y="{y}" fill="{color}" font-family="'Fira Code', Consolas, monospace"
              font-size="14" font-weight="{weight}" clip-path="url(#reveal{i})">
          {text}
        </text>
        <clipPath id="reveal{i}">
          <rect x="{text_x}" y="{y - 14}" width="0" height="20">
            <animate attributeName="width" from="0" to="500" begin="{delay:.2f}s" dur="{dur:.2f}s"
                      fill="freeze" calcMode="linear"/>
          </rect>
        </clipPath>''')
        delay += dur + 0.05

    svg = f'''<svg viewBox="0 0 620 {height}" xmlns="http://www.w3.org/2000/svg" width="620" height="{height}">
  <style>
    text {{ font-family: 'Fira Code', Consolas, monospace; }}
    .cursor {{ animation: blink 1s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
  </style>
  <rect x="0" y="0" width="620" height="{height}" rx="10" fill="{BG}" stroke="#30363d"/>
  <text x="{glyph_x}" y="{top_pad - 4}" fill="{ACCENT}" font-size="14" font-family="monospace" xml:space="preserve">{glyph_tspans}</text>
  {''.join(text_elems)}
  <rect class="cursor" x="{text_x}" y="{top_pad + len(lines) * line_h - 12}" width="8" height="14" fill="{FG}">
    <animate attributeName="opacity" begin="{delay:.2f}s" from="0" to="1" dur="0.1s" fill="freeze"/>
  </rect>
</svg>'''
    return svg


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    stats = fetch_stats(username)
    svg = render_svg(stats)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
