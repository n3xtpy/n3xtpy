"""Shared visual language for every generated SVG in this profile.

One palette, one type scale, one card shell, so the header, the profile card,
the heatmap and the language strip read as a single system rather than four
unrelated widgets.

Everything here has to survive being rendered by GitHub as `<img src="*.svg">`:
CSS animations and SMIL both run in that context, but scripts, external
stylesheets and webfonts do not. So: no <script>, no @import, no
<foreignObject>, and font stacks limited to families the viewer already has.

Design rules, in case a future card gets added:

  * One accent per card, GitHub Primer colours only. Neon is a costume.
  * Motion is confirmation, not decoration -- things fade and grow into place
    once, and only the smallest element keeps moving afterwards.
  * Every card is CARD_W wide and uses PAD gutters, so the README stacks into
    a single clean column at any zoom.
"""

# Canvas. Matches GitHub's own dark surfaces so the cards sit flush against
# the README rather than floating on a slightly-wrong grey.
BG = "#0d1117"
SURFACE = "#111720"
RAISED = "#161b22"
BORDER = "#21262d"
BORDER_SOFT = "#1b2129"

# Text
FG = "#e6edf3"
DIM = "#7d8590"
FAINT = "#484f58"

# Accents -- Primer's, not neon.
ACCENT = "#58a6ff"
GREEN = "#3fb950"
PURPLE = "#a371f7"
ORANGE = "#d29922"
PINK = "#f778ba"
CYAN = "#39c5cf"

# Contribution ramp (GitHub's own dark-theme greens)
LEVEL_COLORS = ["#151b23", "#033a16", "#196c2e", "#2ea043", "#56d364"]

# Shared geometry. Every card is this wide; the README relies on it.
CARD_W = 860
PAD = 32
RADIUS = 14

# Webfonts never load inside an <img>-embedded SVG, so name only families that
# ship with the OS and let the generic keyword catch the rest.
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

# Monospace advance width as a fraction of font-size. Close enough across the
# stack above to lay out columns without measuring glyphs.
CHAR_W = 0.60

# Colours the language bars cycle through, in order.
LANG_COLORS = [ACCENT, GREEN, PURPLE, ORANGE, CYAN, PINK]

# Well-known language colours win over the cycle when we recognise the name.
LANG_PALETTE = {
    "Python": "#3776ab",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "SCSS": "#c6538c",
    "Shell": "#89e051",
    "Go": "#00add8",
    "Rust": "#dea584",
    "Java": "#b07219",
    "C": "#8f9aa6",
    "C++": "#f34b7d",
    "C#": "#178600",
    "Ruby": "#cc342d",
    "PHP": "#4f5d95",
    "Swift": "#f05138",
    "Kotlin": "#a97bff",
    "Dart": "#00b4ab",
    "Vue": "#41b883",
    "Lua": "#000080",
    "Jupyter Notebook": "#da5b0b",
    "Dockerfile": "#384d54",
    "Makefile": "#427819",
}


def lang_color(name, index=0):
    """Colour for a language: its canonical one if known, else the cycle."""
    return LANG_PALETTE.get(name, LANG_COLORS[index % len(LANG_COLORS)])


def esc(s):
    """XML-escape text destined for an SVG text node or attribute."""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def text_w(s, size):
    """Rendered width of a monospace string, for laying out columns."""
    return len(s) * size * CHAR_W


# ---------------------------------------------------------------- primitives


def defs_card(width, height, accent=ACCENT, ident="card"):
    """Gradients the card shell needs: the panel wash and the top hairline.

    The wash is a barely-there vertical lift, and the hairline is a single
    accent stroke that fades out across the top edge. Together they read as
    'lit from above' without any glow filter.
    """
    return f'''<linearGradient id="{ident}-wash" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{RAISED}"/>
      <stop offset="55%" stop-color="{SURFACE}"/>
      <stop offset="100%" stop-color="{BG}"/>
    </linearGradient>
    <linearGradient id="{ident}-rule" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0"/>
      <stop offset="18%" stop-color="{accent}" stop-opacity="0.85"/>
      <stop offset="62%" stop-color="{accent}" stop-opacity="0.20"/>
      <stop offset="100%" stop-color="{accent}" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="{ident}-clip">
      <rect x="0" y="0" width="{width}" height="{height}" rx="{RADIUS}"/>
    </clipPath>'''


def card_shell(width, height, accent=ACCENT, ident="card"):
    """Panel, border and the accent hairline along the top edge.

    Drawn first; `card_border` closes the frame back over the content so the
    stroke stays crisp against whatever was painted inside.
    """
    return f'''<rect x="0" y="0" width="{width}" height="{height}" rx="{RADIUS}" fill="url(#{ident}-wash)"/>
  <g clip-path="url(#{ident}-clip)">
    <rect x="0" y="0" width="{width}" height="2" fill="url(#{ident}-rule)"/>
  </g>'''


def card_border(width, height, ident="card"):
    """The 1px frame, painted last so nothing bleeds over the edge."""
    return (
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" '
        f'rx="{RADIUS}" fill="none" stroke="{BORDER}" stroke-width="1"/>'
    )


def card_title(width, label, meta="", accent=ACCENT, y=38, rule=True):
    """Section label for a card: accent dot, uppercase label, right-hand meta.

    Replaces the traffic-light title bar the cards used to wear. Four fake
    macOS windows stacked down a README is costume, not design -- this reads
    as a section heading, which is what it actually is.
    """
    parts = [
        f'<circle cx="{PAD + 4}" cy="{y - 5}" r="4" fill="{accent}"/>',
        f'<text x="{PAD + 18}" y="{y}" fill="{FG}" font-family="{MONO}" font-size="13" '
        f'font-weight="700" letter-spacing="1.6">{esc(label.upper())}</text>',
    ]
    if meta:
        parts.append(
            f'<text x="{width - PAD}" y="{y}" fill="{DIM}" font-family="{MONO}" '
            f'font-size="12" text-anchor="end">{esc(meta)}</text>'
        )
    if rule:
        parts.append(
            f'<line x1="{PAD}" y1="{y + 16}" x2="{width - PAD}" y2="{y + 16}" '
            f'stroke="{BORDER}" stroke-width="1"/>'
        )
    return "\n  ".join(parts)


def hold_keytimes(begin, dur):
    """(keyTimes, total) for an animation that idles, then runs.

    Every intro on these cards is written as a single animation starting at
    t=0 that holds its opening value until `begin`, rather than as a delayed
    animation with `begin="1.5s"`. The difference matters: a delayed animation
    needs its element to sit at opacity 0 (or width 0) in the markup, so a
    renderer that ignores SMIL shows an empty card forever. Holding instead
    lets every element carry its *finished* state as its attributes, so the
    worst case is a card that renders complete but never animates.
    """
    total = max(0.01, begin + dur)
    return f"0;{begin / total:.4f};1", total


def fade_in(begin, dur=0.5, shift=0.0):
    """Animations for an element that fades -- and optionally rises -- in.

    Callers write `<g>{fade_in(0.4)}...</g>`: no opacity attribute, because
    the group's natural state is the one it ends in.
    """
    keytimes, total = hold_keytimes(begin, dur)
    anim = (
        f'<animate attributeName="opacity" values="0;0;1" keyTimes="{keytimes}" '
        f'dur="{total:.2f}s" fill="freeze"/>'
    )
    if shift:
        anim += (
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 {shift}; 0 {shift}; 0 0" keyTimes="{keytimes}" '
            f'dur="{total:.2f}s" fill="freeze" calcMode="spline" '
            f'keySplines="0 0 1 1; 0.16 1 0.3 1"/>'
        )
    return anim


def grow_w(to, begin, dur=0.85):
    """Width animation with the easing every bar in this profile uses.

    The rect keeps `width="{to}"` in the markup -- see hold_keytimes -- so a
    renderer without SMIL shows the bar at full length instead of nothing.
    """
    keytimes, total = hold_keytimes(begin, dur)
    return (
        f'<animate attributeName="width" values="0;0;{to:.2f}" keyTimes="{keytimes}" '
        f'dur="{total:.2f}s" fill="freeze" calcMode="spline" '
        f'keySplines="0 0 1 1; 0.16 1 0.3 1"/>'
    )


def appear(to, begin, dur=0.5):
    """Opacity animation for an element whose finished value isn't 1."""
    keytimes, total = hold_keytimes(begin, dur)
    return (
        f'<animate attributeName="opacity" values="0;0;{to}" keyTimes="{keytimes}" '
        f'dur="{total:.2f}s" fill="freeze"/>'
    )


def type_reveal(ident, x, y, width, height, begin, dur):
    """clipPath that wipes left-to-right, i.e. a typewriter.

    Pair it with a <text clip-path="url(#ident)">; the text itself never moves,
    which keeps glyph positions stable while the reveal runs. The clip rect is
    born full-width so the text is legible even where SMIL never starts.
    """
    keytimes, total = hold_keytimes(begin, dur)
    return f'''<clipPath id="{ident}">
      <rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}">
        <animate attributeName="width" values="0;0;{width:.1f}" keyTimes="{keytimes}"
                 dur="{total:.2f}s" fill="freeze" calcMode="linear"/>
      </rect>
    </clipPath>'''


def cycle_opacity(index, count, total, fade=0.45):
    """SMIL <animate> that shows element `index` for its slice of a loop.

    Used for rotating taglines: every element runs the same `total`-second
    timeline, but each one's keyTimes put its visible window in a different
    slot, so exactly one is on screen at a time and the cycle never drifts.
    """
    slot = total / count
    start = index * slot
    end = start + slot
    fade = min(fade, slot / 2.5)
    marks = [0.0, start, start + fade, end - fade, end, total]
    keytimes = ";".join(f"{min(max(m / total, 0.0), 1.0):.4f}" for m in marks)
    return (
        f'<animate attributeName="opacity" values="0;0;1;1;0;0" '
        f'keyTimes="{keytimes}" dur="{total:.2f}s" repeatCount="indefinite"/>'
    )


def caret(x, y, w=8, h=16, fill=ACCENT, begin=0.0):
    """Blinking caret that appears once the typing before it is done.

    The only element on any card that moves forever. Everything else settles.
    """
    return f'''<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="1" fill="{fill}">
      {appear(1, begin, 0.01)}
      <animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;0.45;0.5;0.95;1"
               dur="1.15s" begin="{begin:.2f}s" repeatCount="indefinite"/>
    </rect>'''


def sheen(ident, x, y, width, height, begin, dur=5.0, opacity=0.07):
    """One slow highlight pass across a finished bar or grid.

    Kept faint on purpose: it should register as the surface catching light,
    not as a scanning laser. Returns (defs, body).
    """
    defs = f'''<linearGradient id="{ident}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset="50%" stop-color="#ffffff" stop-opacity="{opacity}"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="{ident}-clip">
      <rect x="{x}" y="{y}" width="{width}" height="{height}"/>
    </clipPath>'''
    band = max(120, width * 0.18)
    body = f'''<g clip-path="url(#{ident}-clip)" pointer-events="none">
    <rect x="{x - band}" y="{y}" width="{band}" height="{height}" fill="url(#{ident})">
      <animateTransform attributeName="transform" type="translate"
                        values="0 0; {width + band * 2:.0f} 0" dur="{dur}s"
                        begin="{begin:.2f}s" repeatCount="indefinite"/>
    </rect>
  </g>'''
    return defs, body


def stat_block(x, y, value, label, color=FG, begin=0.0, size=26):
    """A big number over a small caption -- the profile's one loud element."""
    return f'''<g>
    {fade_in(begin, 0.5, shift=6)}
    <text x="{x}" y="{y}" fill="{color}" font-family="{MONO}" font-size="{size}"
          font-weight="700" letter-spacing="-0.5">{esc(value)}</text>
    <text x="{x}" y="{y + 18}" fill="{DIM}" font-family="{MONO}" font-size="11"
          letter-spacing="0.8">{esc(label.upper())}</text>
  </g>'''
