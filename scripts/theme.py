"""Shared visual language for every generated SVG in this profile.

One palette, one font stack, one set of animation primitives, so the header,
the neofetch card, the heatmap and the language bars read as a single system
rather than four unrelated widgets.

Everything here has to survive being rendered by GitHub as `<img src="*.svg">`:
CSS animations and SMIL both run in that context, but scripts, external
stylesheets and webfonts do not. So: no <script>, no @import, no
<foreignObject>, and font stacks limited to families the viewer already has.
"""

# GitHub dark canvas
BG = "#0d1117"
CHROME = "#161b22"
PANEL = "#11161d"
BORDER = "#30363d"
FG = "#c9d1d9"
DIM = "#8b949e"
FAINT = "#484f58"

# Accents
ACCENT = "#58a6ff"
GREEN = "#39d353"
PURPLE = "#bc8cff"
PINK = "#f778ba"
ORANGE = "#ffa657"
CYAN = "#56d4dd"

# Terminal window dots
DOTS = ["#ff5f56", "#ffbd2e", "#27c93f"]

# Contribution ramp (GitHub's own dark-theme greens)
LEVEL_COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

# Webfonts never load inside an <img>-embedded SVG, so name only families that
# ship with the OS and let the generic keyword catch the rest.
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

# Colours the language bars cycle through, in order.
LANG_COLORS = [ACCENT, GREEN, PURPLE, ORANGE, PINK, CYAN]

# Well-known language colours win over the cycle when we recognise the name.
LANG_PALETTE = {
    "Python": "#3776ab",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Shell": "#89e051",
    "Go": "#00add8",
    "Rust": "#dea584",
    "Java": "#b07219",
    "C": "#555555",
    "C++": "#f34b7d",
    "C#": "#178600",
    "Ruby": "#701516",
    "PHP": "#4f5d95",
    "Swift": "#f05138",
    "Kotlin": "#a97bff",
    "Dart": "#00b4ab",
    "Vue": "#41b883",
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


def defs_glow(ident="glow", std=2.4):
    """Soft neon bloom. Kept cheap -- a single blur merged under the source."""
    return f'''<filter id="{ident}" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="{std}" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>'''


def defs_border_gradient(ident="edge", colors=(ACCENT, PURPLE, GREEN)):
    """Gradient that slides along the card border, forever."""
    stops = "".join(
        f'<stop offset="{i / (len(colors) - 1):.3f}" stop-color="{c}"/>'
        for i, c in enumerate(colors)
    )
    return f'''<linearGradient id="{ident}" x1="0" y1="0" x2="1" y2="0">
      {stops}
      <animateTransform attributeName="gradientTransform" type="translate"
                        values="-1 0; 1 0; -1 0" dur="9s" repeatCount="indefinite"/>
    </linearGradient>'''


def scanlines(width, height, ident="scan", opacity=0.055, period=3, radius=12):
    """CRT scanline overlay plus a slow vertical drift.

    `period` is the pixel pitch of the lines; the layer creeps downward by
    exactly one period, so the loop is seamless. Returns (defs, body) -- the
    caller drops `body` last, on top of everything else.
    """
    defs = f'''<pattern id="{ident}" width="{width}" height="{period}" patternUnits="userSpaceOnUse">
      <rect x="0" y="0" width="{width}" height="1" fill="#ffffff" opacity="{opacity}"/>
    </pattern>
    <clipPath id="{ident}-clip">
      <rect x="0" y="0" width="{width}" height="{height}" rx="{radius}"/>
    </clipPath>'''
    body = f'''<g clip-path="url(#{ident}-clip)" pointer-events="none">
    <rect x="0" y="-{period}" width="{width}" height="{height + period * 2}" fill="url(#{ident})">
      <animateTransform attributeName="transform" type="translate"
                        values="0 0; 0 {period}" dur="1.6s" repeatCount="indefinite"/>
    </rect>
  </g>'''
    return defs, body


def grid_pattern(ident="grid", step=26, color=BORDER, opacity=0.30):
    """Faint blueprint grid for card backgrounds."""
    return f'''<pattern id="{ident}" width="{step}" height="{step}" patternUnits="userSpaceOnUse">
      <path d="M {step} 0 L 0 0 0 {step}" fill="none" stroke="{color}"
            stroke-width="0.6" opacity="{opacity}"/>
    </pattern>'''


def type_reveal(ident, x, y, width, height, begin, dur):
    """clipPath that wipes left-to-right, i.e. a typewriter.

    Pair it with a <text clip-path="url(#ident)">; the text itself never moves,
    which keeps glyph positions stable while the reveal runs.
    """
    return f'''<clipPath id="{ident}">
      <rect x="{x:.1f}" y="{y:.1f}" width="0" height="{height:.1f}">
        <animate attributeName="width" from="0" to="{width:.1f}"
                 begin="{begin:.2f}s" dur="{dur:.2f}s" fill="freeze" calcMode="linear"/>
      </rect>
    </clipPath>'''


def cycle_opacity(index, count, total, fade=0.4):
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


def cursor(x, y, w=8, h=15, fill=FG, begin=0.0):
    """Blinking block cursor that appears once the typing before it is done."""
    return f'''<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" fill="{fill}" opacity="0">
      <animate attributeName="opacity" values="0;1" begin="{begin:.2f}s" dur="0.01s" fill="freeze"/>
      <animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;0.45;0.5;0.95;1"
               dur="1.1s" begin="{begin:.2f}s" repeatCount="indefinite"/>
    </rect>'''


def window_chrome(width, title, height=36):
    """The traffic-light title bar shared by every card."""
    return f'''<rect x="0" y="0" width="{width}" height="{height}" rx="12" fill="{CHROME}"/>
  <rect x="0" y="{height - 12}" width="{width}" height="12" fill="{CHROME}"/>
  <line x1="0" y1="{height}" x2="{width}" y2="{height}" stroke="{BORDER}" stroke-width="1"/>
  <circle cx="22" cy="{height / 2}" r="6" fill="{DOTS[0]}"/>
  <circle cx="42" cy="{height / 2}" r="6" fill="{DOTS[1]}"/>
  <circle cx="62" cy="{height / 2}" r="6" fill="{DOTS[2]}"/>
  <text x="{width / 2}" y="{height / 2 + 4}" fill="{DIM}" font-family="{MONO}"
        font-size="12" text-anchor="middle">{esc(title)}</text>'''


def card_frame(width, height, title, radius=12):
    """Background + animated border + chrome. Returns (defs, body)."""
    body = f'''<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="{radius}" fill="{BG}"/>
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="{radius}"
        fill="none" stroke="url(#edge)" stroke-width="1.5" opacity="0.85"/>
  {window_chrome(width, title)}'''
    return defs_border_gradient("edge"), body
