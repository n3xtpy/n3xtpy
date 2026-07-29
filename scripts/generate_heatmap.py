"""Scrape the public GitHub contributions calendar and re-render it as an
animated SVG card: cells wash in on a diagonal wave, a sheen sweeps across
the finished grid on a loop, and the streak numbers count up underneath.

No token needed -- github.com/users/<username>/contributions is a public,
unauthenticated endpoint. Parsed with regexes rather than bs4 to keep the
dependency footprint down. If the scrape fails or comes back empty the
existing card is left alone, so the README never goes blank.
"""
import datetime
import re
import sys

import requests

from theme import (
    ACCENT,
    BG,
    BORDER,
    DIM,
    FG,
    GREEN,
    LEVEL_COLORS,
    MONO,
    ORANGE,
    PURPLE,
    defs_border_gradient,
    esc,
    window_chrome,
)

USERNAME = "n3xtpy"
OUT_PATH = "assets/heatmap.svg"

CELL = 11
GAP = 3
PITCH = CELL + GAP

PAD_X = 20
LABEL_W = 30           # room for the Mon/Wed/Fri column
GRID_TOP = 74          # chrome + month labels
MONTH_LABEL_Y = 66
FOOTER_H = 52

WEEKDAYS = {1: "Mon", 3: "Wed", 5: "Fri"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

CELL_RE = re.compile(
    r'<(?:td|rect)\b[^>]*\bdata-date="(?P<date>[^"]+)"[^>]*?(?:data-level="(?P<level>\d)")?[^>]*>',
)
LEVEL_CLASS_RE = re.compile(r"level-(\d)")
TOTAL_RE = re.compile(r"([\d,]+)\s+contributions?\s+in\s+the\s+last\s+year", re.I)


def fetch_calendar(username):
    url = f"https://github.com/users/{username}/contributions"
    r = requests.get(url, timeout=20, headers={"User-Agent": "profile-readme-bot"})
    r.raise_for_status()
    html = r.text

    days = []
    for m in CELL_RE.finditer(html):
        level = m.group("level")
        if level is None:
            lm = LEVEL_CLASS_RE.search(m.group(0))
            level = lm.group(1) if lm else "0"
        days.append({"date": m.group("date"), "level": str(level)})

    tm = TOTAL_RE.search(html)
    total = int(tm.group(1).replace(",", "")) if tm else None
    return days, total


def parse_days(days):
    """[(date, level)] sorted chronologically, bad rows dropped."""
    out = []
    for day in days:
        try:
            out.append((datetime.date.fromisoformat(day["date"]), int(day["level"])))
        except (ValueError, KeyError, TypeError):
            continue
    out.sort()
    return out


def build_weeks(parsed):
    """Lay the calendar out as columns of weeks, keyed off the real dates.

    The scraped HTML is a table with one row per weekday, so reading it in
    document order gives cells that are seven days apart, not one -- chunking
    that stream into groups of seven (as this script used to) scrambles the
    grid. Placing each cell by its own date is immune to the source ordering.
    """
    if not parsed:
        return []
    first = parsed[0][0]
    # GitHub's calendar columns start on Sunday; date.weekday() is Mon=0..Sun=6.
    sunday_index = (first.weekday() + 1) % 7
    start = first - datetime.timedelta(days=sunday_index)

    cells = {}
    for date, level in parsed:
        col = (date - start).days // 7
        row = (date.weekday() + 1) % 7
        cells[(col, row)] = (date, level)

    ncols = max(col for col, _ in cells) + 1
    return [[cells.get((c, r)) for r in range(7)] for c in range(ncols)]


def streaks(parsed):
    """(current, longest) run of consecutive days with any contribution.

    The final day of the calendar is today and is usually still empty, so a
    zero there alone doesn't end the current streak.
    """
    longest = run = 0
    for _, level in parsed:
        if level:
            run += 1
            longest = max(longest, run)
        else:
            run = 0

    current = 0
    for i, (_, level) in enumerate(reversed(parsed)):
        if level:
            current += 1
        elif i == 0:
            continue  # today hasn't happened yet
        else:
            break
    return current, longest


def month_labels(weeks):
    """Column index and name for each week that opens a new month."""
    out = []
    seen = None
    for w, week in enumerate(weeks):
        date = next((cell[0] for cell in week if cell), None)
        if date is None:
            continue
        if date.month != seen:
            # Drop a label that would collide with the previous one.
            if not out or w - out[-1][0] >= 3:
                out.append((w, MONTHS[date.month - 1]))
            seen = date.month
    return out


def render_svg(days, total=None):
    parsed = parse_days(days)
    weeks = build_weeks(parsed)
    grid_x = PAD_X + LABEL_W
    grid_w = len(weeks) * PITCH
    grid_h = 7 * PITCH
    width = int(grid_x + grid_w + PAD_X)
    height = int(GRID_TOP + grid_h + FOOTER_H)

    # The page's own "N contributions in the last year" is authoritative. Without
    # it we can only count days that had *any* activity, so say that instead of
    # passing an undercount off as a contribution total.
    total_label = "contributions"
    if total is None:
        total = sum(1 for _, level in parsed if level)
        total_label = "active days"
    current, longest = streaks(parsed)

    # Diagonal wave: delay rises with column and row, so the fill sweeps in
    # from the top-left corner rather than marching column by column.
    span = 2.4
    max_coord = max(1, (len(weeks) - 1) * 0.75 + 6)
    cells = []
    for w, week in enumerate(weeks):
        for d, cell in enumerate(week):
            if cell is None:
                continue  # calendar edge: before the first day or after today
            date, level = cell
            x = grid_x + w * PITCH
            y = GRID_TOP + d * PITCH
            color = LEVEL_COLORS[min(max(level, 0), 4)]
            delay = (w * 0.75 + d) / max_coord * span
            title = f"<title>{esc(date.isoformat())} · level {level}</title>"
            cells.append(f'''
      <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{color}" opacity="0">{title}
        <animate attributeName="opacity" values="0;1" begin="{delay:.2f}s" dur="0.45s" fill="freeze"/>
        <animate attributeName="rx" values="5.5;2.5" begin="{delay:.2f}s" dur="0.45s" fill="freeze"/>
      </rect>''')

    weekday_elems = "".join(
        f'<text x="{PAD_X + LABEL_W - 8}" y="{GRID_TOP + d * PITCH + CELL - 1}" fill="{DIM}" '
        f'font-family="{MONO}" font-size="9.5" text-anchor="end">{name}</text>'
        for d, name in WEEKDAYS.items()
    )

    month_elems = "".join(
        f'<text x="{grid_x + w * PITCH}" y="{MONTH_LABEL_Y}" fill="{DIM}" '
        f'font-family="{MONO}" font-size="10">{name}</text>'
        for w, name in month_labels(weeks)
    )

    legend_x = width - PAD_X - 5 * PITCH - 74
    legend_y = GRID_TOP + grid_h + 26
    legend = "".join(
        f'<rect x="{legend_x + 34 + i * PITCH}" y="{legend_y - 9}" width="{CELL}" height="{CELL}" '
        f'rx="2.5" fill="{c}"/>'
        for i, c in enumerate(LEVEL_COLORS)
    )

    stats_begin = span + 0.5
    stat_items = [
        (f"{total:,}", total_label, GREEN),
        (f"{current}", "day streak", ORANGE),
        (f"{longest}", "longest", PURPLE),
    ]
    stat_elems = []
    sx = PAD_X + 4
    for i, (value, label, color) in enumerate(stat_items):
        stat_elems.append(f'''
    <g opacity="0">
      <animate attributeName="opacity" values="0;1" begin="{stats_begin + i * 0.18:.2f}s" dur="0.5s" fill="freeze"/>
      <text x="{sx}" y="{legend_y}" font-family="{MONO}" font-size="14" font-weight="700" fill="{color}">{esc(value)}</text>
      <text x="{sx + len(value) * 8.6 + 8}" y="{legend_y}" font-family="{MONO}" font-size="11.5" fill="{DIM}">{esc(label)}</text>
    </g>''')
        sx += len(value) * 8.6 + len(label) * 7.0 + 30

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"
     width="{width}" height="{height}" role="img" aria-label="contribution heatmap">
  <title>{total:,} {total_label} — {current} day current streak, {longest} longest</title>
  <defs>
    {defs_border_gradient("edge", (GREEN, ACCENT, PURPLE))}
    <linearGradient id="sheen" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset="50%" stop-color="#ffffff" stop-opacity="0.20"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
    <!-- Clipped to the grid alone, so the sweep never washes over the
         weekday labels sitting in the left gutter. -->
    <clipPath id="gridClip">
      <rect x="{grid_x}" y="{GRID_TOP - 4}" width="{grid_w}" height="{grid_h + 8}"/>
    </clipPath>
  </defs>

  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" fill="{BG}"/>
  {window_chrome(width, "contributions — last 12 months")}

  {month_elems}
  {weekday_elems}
  {''.join(cells)}

  <!-- Sheen sweeps the finished grid, so the card keeps moving after the fill. -->
  <g clip-path="url(#gridClip)" pointer-events="none">
    <rect x="{grid_x - 160}" y="{GRID_TOP - 4}" width="160" height="{grid_h + 8}" fill="url(#sheen)">
      <animateTransform attributeName="transform" type="translate"
                        values="0 0; {grid_w + 200} 0" dur="4.5s"
                        begin="{span + 0.3:.2f}s" repeatCount="indefinite"/>
    </rect>
  </g>

  <line x1="{PAD_X}" y1="{GRID_TOP + grid_h + 12}" x2="{width - PAD_X}" y2="{GRID_TOP + grid_h + 12}"
        stroke="{BORDER}" stroke-width="1"/>
  {''.join(stat_elems)}

  <g opacity="0">
    <animate attributeName="opacity" values="0;1" begin="{stats_begin + 0.5:.2f}s" dur="0.5s" fill="freeze"/>
    <text x="{legend_x}" y="{legend_y}" fill="{DIM}" font-family="{MONO}" font-size="11">Less</text>
    {legend}
    <text x="{legend_x + 34 + 5 * PITCH + 6}" y="{legend_y}" fill="{DIM}" font-family="{MONO}" font-size="11">More</text>
  </g>

  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12"
        fill="none" stroke="url(#edge)" stroke-width="1.5" opacity="0.9"/>
</svg>
'''


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    try:
        days, total = fetch_calendar(username)
    except Exception as exc:
        print(f"skip: could not fetch calendar for {username} ({exc}); keeping existing heatmap")
        return 0

    if not days:
        print(f"skip: calendar for {username} parsed as empty; keeping existing heatmap")
        return 0

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(render_svg(days, total))
    print(f"wrote {OUT_PATH} ({len(days)} days)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
