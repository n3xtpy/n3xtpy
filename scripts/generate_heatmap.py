"""Scrape the public GitHub contributions calendar and re-render it as a card
sized to match the rest of the profile: cells wash in on a diagonal, a faint
sheen passes over the finished grid, and the streak numbers sit underneath in
the same headline style the profile card uses.

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
    BORDER,
    CARD_W,
    DIM,
    GREEN,
    LEVEL_COLORS,
    MONO,
    ORANGE,
    PAD,
    PURPLE,
    card_shell,
    card_title,
    appear,
    card_border,
    defs_card,
    esc,
    fade_in,
    sheen,
    stat_block,
)

USERNAME = "n3xtpy"
OUT_PATH = "assets/heatmap.svg"

LABEL_W = 34           # gutter for the Mon/Wed/Fri column
CELL_GAP = 3
GRID_TOP = 88
MONTH_LABEL_Y = 78

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

    # The grid is sized to the card, not the other way round: whatever number
    # of weeks came back, the columns stretch to fill exactly one card width
    # so this card lines up with the three around it.
    grid_x = PAD + LABEL_W
    grid_w = CARD_W - PAD - grid_x
    pitch = grid_w / max(1, len(weeks))
    cell = pitch - CELL_GAP
    grid_h = 7 * pitch - CELL_GAP
    grid_bottom = GRID_TOP + grid_h

    rule_y = int(grid_bottom + 22)
    stats_y = rule_y + 36
    height = stats_y + 40

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
    span = 2.0
    max_coord = max(1, (len(weeks) - 1) * 0.7 + 6)
    cells = []
    for w, week in enumerate(weeks):
        for d, entry in enumerate(week):
            if entry is None:
                continue  # calendar edge: before the first day or after today
            date, level = entry
            x = grid_x + w * pitch
            y = GRID_TOP + d * pitch
            color = LEVEL_COLORS[min(max(level, 0), 4)]
            delay = (w * 0.7 + d) / max_coord * span
            cells.append(f'''
      <rect x="{x:.2f}" y="{y:.2f}" width="{cell:.2f}" height="{cell:.2f}" rx="2.5" fill="{color}">
        <title>{esc(date.isoformat())} · level {level}</title>
        {appear(1, delay, 0.45)}
      </rect>''')

    weekday_elems = "".join(
        f'<text x="{grid_x - 10}" y="{GRID_TOP + d * pitch + cell - 1:.1f}" fill="{DIM}" '
        f'font-family="{MONO}" font-size="9.5" text-anchor="end">{name}</text>'
        for d, name in WEEKDAYS.items()
    )

    month_elems = "".join(
        f'<text x="{grid_x + w * pitch:.1f}" y="{MONTH_LABEL_Y}" fill="{DIM}" '
        f'font-family="{MONO}" font-size="10.5">{name}</text>'
        for w, name in month_labels(weeks)
    )

    stats_begin = span + 0.4
    figures = [
        (f"{total:,}", total_label, GREEN),
        (f"{current}", "day streak", ORANGE),
        (f"{longest}", "longest run", PURPLE),
    ]
    stat_elems = "".join(
        stat_block(PAD + i * 168, stats_y, value, label, color, begin=stats_begin + i * 0.14)
        for i, (value, label, color) in enumerate(figures)
    )

    # Legend, right-aligned against the same gutter everything else uses.
    legend_pitch = 14
    legend_right = CARD_W - PAD
    legend_x = legend_right - 40 - 5 * legend_pitch - 44
    legend_swatches = "".join(
        f'<rect x="{legend_x + 40 + i * legend_pitch}" y="{stats_y - 9}" width="11" height="11" '
        f'rx="2.5" fill="{c}"/>'
        for i, c in enumerate(LEVEL_COLORS)
    )

    sheen_defs, sheen_body = sheen(
        "gridSheen", grid_x, GRID_TOP - 3, grid_w, grid_h + 6, span + 0.3, dur=5.5
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CARD_W} {height}"
     width="{CARD_W}" height="{height}" role="img" aria-label="contribution heatmap">
  <title>{total:,} {total_label} — {current} day current streak, {longest} longest</title>
  <defs>
    {defs_card(CARD_W, height, accent=GREEN)}
    {sheen_defs}
  </defs>

  {card_shell(CARD_W, height, accent=GREEN)}
  {card_title(CARD_W, "contributions", meta="last 12 months", accent=GREEN)}

  {month_elems}
  {weekday_elems}
  {''.join(cells)}
  {sheen_body}

  <line x1="{PAD}" y1="{rule_y}" x2="{CARD_W - PAD}" y2="{rule_y}" stroke="{BORDER}" stroke-width="1"/>
  {stat_elems}

  <g>
    {fade_in(stats_begin + 0.4, 0.5)}
    <text x="{legend_x}" y="{stats_y}" fill="{DIM}" font-family="{MONO}" font-size="11">Less</text>
    {legend_swatches}
    <text x="{legend_x + 40 + 5 * legend_pitch + 6}" y="{stats_y}" fill="{DIM}"
          font-family="{MONO}" font-size="11">More</text>
  </g>

  {card_border(CARD_W, height)}
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
