"""Generate the animated terminal header banner for the profile README.

A prompt types itself out, the name draws in behind a gradient sweep, and a
set of taglines rotates underneath on an endless loop -- all in SMIL/CSS so
it survives GitHub rendering the file as a plain <img>.

Purely local: no network, no source image, so it can never fail the workflow.
"""
import sys

from theme import (
    ACCENT,
    BG,
    CYAN,
    DIM,
    FG,
    GREEN,
    MONO,
    PURPLE,
    cursor,
    cycle_opacity,
    defs_border_gradient,
    defs_glow,
    esc,
    grid_pattern,
    scanlines,
    type_reveal,
    window_chrome,
)

OUT_PATH = "assets/header.svg"
USERNAME = "n3xtpy"

WIDTH = 880
HEIGHT = 242

TAGLINES = [
    "building things that build themselves",
    "python · javascript · automation",
    "this README regenerates itself every day",
    "if it runs twice, it should run on a cron",
]

# Every glyph in the prompt is this wide at font-size 15 in a monospace face.
PROMPT_CHAR_W = 9.02
PROMPT_FONT = 15


def render_svg(username):
    prompt = f"{username}@github:~$ "
    command = "whoami"
    prompt_x = 34
    prompt_y = 96

    # Type the prompt, then the command, at a steady per-character rate.
    prompt_dur = len(prompt) * 0.045
    command_begin = prompt_dur + 0.15
    command_dur = len(command) * 0.075
    command_x = prompt_x + PROMPT_CHAR_W * len(prompt)
    name_begin = command_begin + command_dur + 0.45
    tagline_begin = name_begin + 1.1

    # The rotating taglines share one timeline so exactly one is ever visible.
    cycle_total = len(TAGLINES) * 3.2

    tagline_elems = "".join(
        f'''
    <text x="{prompt_x + 2}" y="190" fill="{DIM}" font-family="{MONO}" font-size="14" opacity="0">
      <tspan fill="{GREEN}">▸ </tspan>{esc(line)}
      {cycle_opacity(i, len(TAGLINES), cycle_total)}
    </text>'''
        for i, line in enumerate(TAGLINES)
    )

    scan_defs, scan_body = scanlines(WIDTH, HEIGHT, opacity=0.05)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}"
     width="{WIDTH}" height="{HEIGHT}" role="img" aria-label="{esc(username)} — animated terminal header">
  <title>{esc(username)}@github</title>
  <defs>
    {defs_border_gradient("edge", (ACCENT, PURPLE, GREEN))}
    {defs_glow("softglow", 3.2)}
    {grid_pattern("grid", 26)}
    {scan_defs}
    <radialGradient id="vignette" cx="0.5" cy="0.1" r="0.9">
      <stop offset="0%" stop-color="{ACCENT}" stop-opacity="0.16"/>
      <stop offset="60%" stop-color="{PURPLE}" stop-opacity="0.05"/>
      <stop offset="100%" stop-color="{BG}" stop-opacity="0"/>
    </radialGradient>

    <!-- Sweeps across the name once it has landed, like a CRT refresh. -->
    <linearGradient id="nameFill" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{ACCENT}"/>
      <stop offset="45%" stop-color="{CYAN}"/>
      <stop offset="100%" stop-color="{PURPLE}"/>
      <animateTransform attributeName="gradientTransform" type="translate"
                        values="-0.6 0; 0.6 0; -0.6 0" dur="7s" repeatCount="indefinite"/>
    </linearGradient>

    {type_reveal("promptClip", prompt_x, prompt_y - 15, PROMPT_CHAR_W * len(prompt), 22, 0.2, prompt_dur)}
    {type_reveal("cmdClip", command_x, prompt_y - 15, PROMPT_CHAR_W * len(command) + 4, 22, command_begin, command_dur)}
  </defs>

  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="14" fill="{BG}"/>
  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="14" fill="url(#grid)"/>
  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="14" fill="url(#vignette)"/>

  {window_chrome(WIDTH, "bash — 80×24")}

  <text x="{prompt_x}" y="{prompt_y}" fill="{GREEN}" font-family="{MONO}" font-size="{PROMPT_FONT}"
        clip-path="url(#promptClip)" xml:space="preserve">{esc(prompt)}</text>
  <text x="{command_x}" y="{prompt_y}" fill="{FG}" font-family="{MONO}" font-size="{PROMPT_FONT}"
        clip-path="url(#cmdClip)">{esc(command)}</text>

  <!-- The answer to `whoami`: rises into place, then breathes. -->
  <g opacity="0" filter="url(#softglow)">
    <animate attributeName="opacity" values="0;1" begin="{name_begin:.2f}s" dur="0.5s" fill="freeze"/>
    <animateTransform attributeName="transform" type="translate" values="0 14; 0 0"
                      begin="{name_begin:.2f}s" dur="0.6s" fill="freeze" calcMode="spline"
                      keySplines="0.16 1 0.3 1"/>
    <text x="{prompt_x}" y="158" fill="url(#nameFill)" font-family="{MONO}"
          font-size="52" font-weight="700" letter-spacing="1.5">{esc(username)}</text>
  </g>

  {tagline_elems}

  {cursor(command_x + PROMPT_CHAR_W * len(command) + 3, prompt_y - 13, begin=command_begin + command_dur)}

  <!-- A rect, not a line: a zero-height bbox gives an objectBoundingBox
       gradient nothing to resolve against, and the stroke renders as nothing. -->
  <g opacity="0">
    <animate attributeName="opacity" values="0;1" begin="{tagline_begin:.2f}s" dur="0.6s" fill="freeze"/>
    <rect x="{prompt_x}" y="208" width="{WIDTH - 2 * prompt_x}" height="1.5" rx="0.75" fill="url(#edge)"/>
  </g>

  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="14"
        fill="none" stroke="url(#edge)" stroke-width="1.5" opacity="0.9"/>
  {scan_body}
</svg>
'''


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(render_svg(username))
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
