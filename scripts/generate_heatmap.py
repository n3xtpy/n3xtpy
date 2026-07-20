"""Scrape the public GitHub contributions calendar and re-render it as an
animated SVG (staggered fade-in per cell) using GitHub's own green palette.

No token needed: github.com/users/<username>/contributions is a public,
unauthenticated endpoint that returns the calendar as SVG. Parsed with a
regex instead of bs4 to keep the dependency footprint to just `requests`.
"""
import sys
import re
import requests

USERNAME = "n3xt-agency"
OUT_PATH = "assets/heatmap.svg"

# GitHub's contribution-level palette (light theme green ramp)
LEVEL_COLORS = {
    "0": "#161b22",
    "1": "#0e4429",
    "2": "#006d32",
    "3": "#26a641",
    "4": "#39d353",
}

CELL = 11
GAP = 3


CELL_RE = re.compile(
    r'<(?:td|rect)\b[^>]*\bdata-date="(?P<date>[^"]+)"[^>]*?(?:data-level="(?P<level>\d)")?[^>]*>',
)
LEVEL_CLASS_RE = re.compile(r"level-(\d)")


def fetch_calendar(username):
    url = f"https://github.com/users/{username}/contributions"
    r = requests.get(url, timeout=15, headers={"User-Agent": "profile-readme-bot"})
    r.raise_for_status()
    html = r.text
    days = []
    for m in CELL_RE.finditer(html):
        date = m.group("date")
        level = m.group("level")
        if level is None:
            tag = m.group(0)
            lm = LEVEL_CLASS_RE.search(tag)
            level = lm.group(1) if lm else "0"
        days.append({"date": date, "level": str(level)})
    return days


def render_svg(days):
    if not days:
        # fallback empty calendar so the workflow never breaks the README
        days = [{"date": "", "level": "0"}] * (53 * 7)

    weeks = [days[i:i + 7] for i in range(0, len(days), 7)]
    width = GAP + len(weeks) * (CELL + GAP)
    height = GAP + 7 * (CELL + GAP)

    rects = []
    delay = 0.0
    step = min(0.01, 1.2 / max(1, len(days)))
    for w, week in enumerate(weeks):
        for d, day in enumerate(week):
            x = GAP + w * (CELL + GAP)
            y = GAP + d * (CELL + GAP)
            color = LEVEL_COLORS.get(day["level"], LEVEL_COLORS["0"])
            title = f"<title>{day['date']}: level {day['level']}</title>" if day["date"] else ""
            rects.append(f'''
      <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}" opacity="0">
        {title}
        <animate attributeName="opacity" from="0" to="1" begin="{delay:.3f}s" dur="0.4s" fill="freeze"/>
      </rect>''')
            delay += step

    svg = f'''<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="#0d1117"/>
  {''.join(rects)}
</svg>'''
    return svg


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    days = fetch_calendar(username)
    svg = render_svg(days)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH} ({len(days)} days)")


if __name__ == "__main__":
    main()
