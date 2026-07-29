"""Generate the full-width language-breakdown strip for the profile README.

One stacked bar whose segments grow in sequence, then a row of legend chips
that fade in behind them. Deliberately a different read from the vertical
mini-bars on the neofetch card: this one is about proportion across the whole
account, not the top five in a list.

Language weight is measured in bytes of source, summed across every public
repo via the per-repo /languages endpoint -- far more honest than counting
repos, where a one-file experiment weighs the same as a real project. That
costs one request per repo, so the repo list is capped and the whole thing
degrades to leaving the existing strip in place if the API says no.
"""
import os
import sys

import requests

from theme import (
    ACCENT,
    BG,
    BORDER,
    DIM,
    FG,
    GREEN,
    MONO,
    PURPLE,
    defs_border_gradient,
    esc,
    lang_color,
    window_chrome,
)

USERNAME = "n3xtpy"
OUT_PATH = "assets/langs.svg"

WIDTH = 880
PAD = 26
BAR_Y = 74
BAR_H = 20
MAX_REPOS = 40      # keeps us inside the 60 req/hr unauthenticated budget
MAX_SHOWN = 7       # everything past this collapses into "other"

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "profile-readme-bot"}


def fetch_languages(username):
    """{language: bytes} summed over the user's most recently pushed repos."""
    r = requests.get(
        f"https://api.github.com/users/{username}/repos?per_page=100&sort=pushed",
        headers=HEADERS,
        timeout=15,
    )
    r.raise_for_status()
    repos = r.json()
    repos = repos if isinstance(repos, list) else []
    repos = [repo for repo in repos if not repo.get("fork")][:MAX_REPOS]

    totals = {}
    for repo in repos:
        url = repo.get("languages_url")
        if not url:
            continue
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            for lang, size in resp.json().items():
                totals[lang] = totals.get(lang, 0) + size
        except Exception:
            continue  # one bad repo shouldn't sink the whole strip
    return totals


def top_slice(totals, limit=MAX_SHOWN):
    """Sorted (language, share) pairs, with the tail folded into 'other'."""
    total = sum(totals.values())
    if not total:
        return []
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    head, tail = ranked[:limit], ranked[limit:]
    out = [(lang, size / total) for lang, size in head]
    if tail:
        out.append(("other", sum(size for _, size in tail) / total))
    return out


CHIP_FONT = 12.5
CHIP_CHAR_W = CHIP_FONT * 0.6   # monospace advance
CHIP_DOT_W = 18                 # swatch plus its gap
CHIP_GAP = 26                   # space between adjacent chips
CHIP_ROW_H = 26


def chip_width(lang, share):
    """On-screen width of one legend chip, used to wrap the legend rows."""
    pct = f"{share * 100:.1f}%"
    return CHIP_DOT_W + (len(lang) + 1 + len(pct)) * CHIP_CHAR_W + 8


def render_svg(langs):
    bar_w = WIDTH - 2 * PAD
    chips_y = BAR_Y + BAR_H + 38

    segments, chips = [], []
    x = float(PAD)
    chip_x = float(PAD)
    chip_row = 0
    for i, (lang, share) in enumerate(langs):
        seg_w = bar_w * share
        color = lang_color(lang, i) if lang != "other" else BORDER
        begin = 0.35 + i * 0.16

        # x is fixed; only the width animates, so segments unroll left to right.
        segments.append(f'''
    <rect x="{x:.2f}" y="{BAR_Y}" width="0" height="{BAR_H}" fill="{color}">
      <title>{esc(lang)} — {share * 100:.1f}%</title>
      <animate attributeName="width" from="0" to="{seg_w:.2f}" begin="{begin:.2f}s"
               dur="0.9s" fill="freeze" calcMode="spline" keySplines="0.16 1 0.3 1"/>
    </rect>''')

        # Wrap to the next row rather than running off the edge of the card.
        w = chip_width(lang, share)
        if chip_x > PAD and chip_x + w > WIDTH - PAD:
            chip_row += 1
            chip_x = float(PAD)
        cy = chips_y + chip_row * CHIP_ROW_H

        chips.append(f'''
    <g opacity="0">
      <animate attributeName="opacity" values="0;1" begin="{begin + 0.45:.2f}s" dur="0.45s" fill="freeze"/>
      <circle cx="{chip_x + 6}" cy="{cy - 4}" r="5" fill="{color}"/>
      <text x="{chip_x + CHIP_DOT_W}" y="{cy}" font-family="{MONO}" font-size="{CHIP_FONT}" fill="{FG}">{esc(lang)}</text>
      <text x="{chip_x + CHIP_DOT_W + (len(lang) + 1) * CHIP_CHAR_W}" y="{cy}" font-family="{MONO}" font-size="{CHIP_FONT}" fill="{DIM}">{share * 100:.1f}%</text>
    </g>''')

        x += seg_w
        chip_x += w + CHIP_GAP

    height = chips_y + chip_row * CHIP_ROW_H + 30
    done = 0.35 + len(langs) * 0.16 + 0.9

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}"
     width="{WIDTH}" height="{height}" role="img" aria-label="language breakdown by bytes of source">
  <title>Language breakdown by bytes of source across public repositories</title>
  <defs>
    {defs_border_gradient("edge", (PURPLE, ACCENT, GREEN))}
    <linearGradient id="sheen" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset="50%" stop-color="#ffffff" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="barClip">
      <rect x="{PAD}" y="{BAR_Y}" width="{bar_w}" height="{BAR_H}" rx="{BAR_H / 2}"/>
    </clipPath>
  </defs>

  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="12" fill="{BG}"/>
  {window_chrome(WIDTH, "~/stack $ cloc --by-lang")}

  <rect x="{PAD}" y="{BAR_Y}" width="{bar_w}" height="{BAR_H}" rx="{BAR_H / 2}" fill="{BORDER}" opacity="0">
    <animate attributeName="opacity" values="0;0.45" begin="0.15s" dur="0.4s" fill="freeze"/>
  </rect>
  <g clip-path="url(#barClip)">
    {''.join(segments)}
    <rect x="-140" y="{BAR_Y}" width="140" height="{BAR_H}" fill="url(#sheen)" pointer-events="none">
      <animateTransform attributeName="transform" type="translate"
                        values="0 0; {WIDTH + 160} 0" dur="4.5s"
                        begin="{done:.2f}s" repeatCount="indefinite"/>
    </rect>
  </g>

  {''.join(chips)}

  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="12"
        fill="none" stroke="url(#edge)" stroke-width="1.5" opacity="0.9"/>
</svg>
'''


def bootstrap():
    """Write the placeholder only when there is no strip at all yet."""
    if os.path.exists(OUT_PATH):
        return 0
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(render_pending())
    print(f"wrote {OUT_PATH} (placeholder — no data yet)")
    return 0


def render_pending():
    """Placeholder for the gap between committing this script and the first run.

    Better than a broken image in the README, and it states plainly that there
    is no data yet rather than showing invented proportions.
    """
    height = 150
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}"
     width="{WIDTH}" height="{height}" role="img" aria-label="language breakdown pending first run">
  <title>Language breakdown — awaiting the first scheduled run</title>
  <defs>{defs_border_gradient("edge", (PURPLE, ACCENT, GREEN))}</defs>
  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="12" fill="{BG}"/>
  {window_chrome(WIDTH, "~/stack $ cloc --by-lang")}
  <text x="{PAD}" y="{BAR_Y + 8}" font-family="{MONO}" font-size="13" fill="{DIM}">
    awaiting first scheduled run
  </text>
  <rect x="{PAD}" y="{BAR_Y + 26}" width="9" height="15" fill="{FG}">
    <animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;0.45;0.5;0.95;1"
             dur="1.1s" repeatCount="indefinite"/>
  </rect>
  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="12"
        fill="none" stroke="url(#edge)" stroke-width="1.5" opacity="0.9"/>
</svg>
'''


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    try:
        totals = fetch_languages(username)
    except Exception as exc:
        print(f"skip: could not fetch languages for {username} ({exc}); keeping existing strip")
        return bootstrap()

    langs = top_slice(totals)
    if not langs:
        print(f"skip: no language data for {username}; keeping existing strip")
        return bootstrap()

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(render_svg(langs))
    print(f"wrote {OUT_PATH} ({len(langs)} languages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
