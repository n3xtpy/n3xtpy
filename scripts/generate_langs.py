"""Generate the language-breakdown card for the profile README.

One stacked bar whose segments unroll in sequence, then a two-column legend
underneath. Deliberately a different read from the top-four list on the
profile card: this one is about proportion across the whole account, not the
languages the most repos happen to be tagged with.

Language weight is measured in bytes of source, summed across every public
repo via the per-repo /languages endpoint -- far more honest than counting
repos, where a one-file experiment weighs the same as a real project. That
costs one request per repo, so the repo list is capped and the whole thing
degrades to leaving the existing card in place if the API says no.
"""
import os
import sys

import requests

from theme import (
    BORDER,
    CARD_W,
    DIM,
    FG,
    MONO,
    PAD,
    PURPLE,
    card_border,
    card_shell,
    appear,
    card_title,
    caret,
    defs_card,
    esc,
    fade_in,
    grow_w,
    lang_color,
    sheen,
    text_w,
)

USERNAME = "n3xtpy"
OUT_PATH = "assets/langs.svg"

BAR_Y = 82
BAR_H = 20
LEGEND_TOP = 148
LEGEND_LH = 28
COLS = 2
MAX_REPOS = 40      # keeps us inside the 60 req/hr unauthenticated budget
MAX_SHOWN = 8       # everything past this collapses into "other"

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
            continue  # one bad repo shouldn't sink the whole card
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


def render_svg(langs):
    bar_w = CARD_W - 2 * PAD
    col_w = bar_w / COLS
    rows = (len(langs) + COLS - 1) // COLS
    height = int(LEGEND_TOP + (rows - 1) * LEGEND_LH + 40)

    segments, legend = [], []
    x = float(PAD)
    for i, (lang, share) in enumerate(langs):
        seg_w = bar_w * share
        color = lang_color(lang, i) if lang != "other" else BORDER
        begin = 0.35 + i * 0.14

        # x is fixed; only the width animates, so segments unroll left to right.
        segments.append(f'''
    <rect x="{x:.2f}" y="{BAR_Y}" width="{seg_w:.2f}" height="{BAR_H}" fill="{color}">
      <title>{esc(lang)} — {share * 100:.1f}%</title>
      {grow_w(seg_w, begin, 0.9)}
    </rect>''')
        x += seg_w

        # Legend fills column-major, so the biggest languages stay on the left.
        col, row = i % COLS, i // COLS
        lx = PAD + col * col_w
        ly = LEGEND_TOP + row * LEGEND_LH
        pct = f"{share * 100:.1f}%"
        # The name is left-aligned and the share right-aligned against a rule,
        # so the eye can run down either edge of the column.
        legend.append(f'''
    <g>
      {fade_in(begin + 0.4, 0.45)}
      <rect x="{lx}" y="{ly - 9}" width="10" height="10" rx="2.5" fill="{color}"/>
      <text x="{lx + 20}" y="{ly}" font-family="{MONO}" font-size="13" fill="{FG}">{esc(lang)}</text>
      <text x="{lx + col_w - 28}" y="{ly}" font-family="{MONO}" font-size="12.5" fill="{DIM}"
            text-anchor="end">{pct}</text>
      <line x1="{lx + 26 + text_w(lang, 13)}" y1="{ly - 4}"
            x2="{lx + col_w - 34 - text_w(pct, 12.5)}" y2="{ly - 4}"
            stroke="{BORDER}" stroke-width="1"/>
    </g>''')

    done = 0.35 + len(langs) * 0.14 + 0.9
    sheen_defs, sheen_body = sheen("barSheen", PAD, BAR_Y, bar_w, BAR_H, done, dur=5.5)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CARD_W} {height}"
     width="{CARD_W}" height="{height}" role="img" aria-label="language breakdown by bytes of source">
  <title>Language breakdown by bytes of source across public repositories</title>
  <defs>
    {defs_card(CARD_W, height, accent=PURPLE)}
    {sheen_defs}
    <clipPath id="barClip">
      <rect x="{PAD}" y="{BAR_Y}" width="{bar_w}" height="{BAR_H}" rx="{BAR_H / 2}"/>
    </clipPath>
  </defs>

  {card_shell(CARD_W, height, accent=PURPLE)}
  {card_title(CARD_W, "stack", meta="bytes of source · public repos", accent=PURPLE)}

  <rect x="{PAD}" y="{BAR_Y}" width="{bar_w}" height="{BAR_H}" rx="{BAR_H / 2}" fill="{BORDER}" opacity="0.5">
    {appear(0.5, 0.15, 0.4)}
  </rect>
  <g clip-path="url(#barClip)">
    {''.join(segments)}
  </g>
  {sheen_body}

  {''.join(legend)}

  {card_border(CARD_W, height)}
</svg>
'''


def bootstrap():
    """Write the placeholder only when there is no card at all yet."""
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
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CARD_W} {height}"
     width="{CARD_W}" height="{height}" role="img" aria-label="language breakdown pending first run">
  <title>Language breakdown — awaiting the first scheduled run</title>
  <defs>{defs_card(CARD_W, height, accent=PURPLE)}</defs>
  {card_shell(CARD_W, height, accent=PURPLE)}
  {card_title(CARD_W, "stack", meta="bytes of source · public repos", accent=PURPLE)}
  <text x="{PAD}" y="{BAR_Y + 10}" font-family="{MONO}" font-size="13" fill="{DIM}">awaiting first scheduled run</text>
  {caret(PAD, BAR_Y + 24, w=8, h=15, fill=PURPLE)}
  {card_border(CARD_W, height)}
</svg>
'''


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    try:
        totals = fetch_languages(username)
    except Exception as exc:
        print(f"skip: could not fetch languages for {username} ({exc}); keeping existing card")
        return bootstrap()

    langs = top_slice(totals)
    if not langs:
        print(f"skip: no language data for {username}; keeping existing card")
        return bootstrap()

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(render_svg(langs))
    print(f"wrote {OUT_PATH} ({len(langs)} languages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
