"""Generate the banner card at the top of the profile README.

A single line types itself out, the name settles in underneath it, and a set
of taglines rotates on the last line forever -- all in SMIL/CSS so it survives
GitHub rendering the file as a plain <img>.

Purely local: no network, no source image, so it can never fail the workflow.
"""
import sys

from theme import (
    ACCENT,
    BORDER,
    CARD_W,
    DIM,
    FG,
    GREEN,
    MONO,
    PAD,
    card_border,
    card_shell,
    caret,
    cycle_opacity,
    defs_card,
    esc,
    fade_in,
    text_w,
    type_reveal,
)

OUT_PATH = "assets/header.svg"
USERNAME = "n3xtpy"

HEIGHT = 206

ROLE = "Automation · Python · JavaScript · CI pipelines"

TAGLINES = [
    "building things that build themselves",
    "if it runs twice, it should run on a cron",
    "this README regenerates itself every day",
]

PROMPT_FONT = 13.5
NAME_FONT = 46


def render_svg(username):
    prompt = f"{username}@github:~$ "
    command = "whoami"

    x = PAD
    prompt_y = 58
    prompt_w = text_w(prompt, PROMPT_FONT)
    command_x = x + prompt_w
    command_w = text_w(command, PROMPT_FONT)

    # Type the prompt, then the command, at a steady per-character rate.
    prompt_dur = len(prompt) * 0.04
    command_begin = 0.2 + prompt_dur + 0.15
    command_dur = len(command) * 0.07
    answer_begin = command_begin + command_dur + 0.35
    tagline_begin = answer_begin + 0.9

    # The rotating taglines share one timeline so exactly one is ever visible.
    cycle_total = len(TAGLINES) * 3.6
    tagline_x = x + 20
    # Only the first line is visible in the markup. With SMIL running, the
    # shared timeline hides it and rotates all of them; without SMIL, one
    # tagline sits there instead of all three printed on top of each other.
    tagline_elems = "".join(
        f'''
    <text x="{tagline_x}" y="180" fill="{DIM}" font-family="{MONO}" font-size="13.5"
          opacity="{1 if i == 0 else 0}">{esc(line)}
      {cycle_opacity(i, len(TAGLINES), cycle_total)}
    </text>'''
        for i, line in enumerate(TAGLINES)
    )

    # Dot matrix in the right gutter: pure texture, faded out toward the edge
    # so it never competes with the name for attention.
    dots = "".join(
        f'<circle cx="{CARD_W - PAD - 6 - col * 15}" cy="{84 + row * 15}" r="1.7" fill="{ACCENT}"/>'
        for col in range(10)
        for row in range(5)
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CARD_W} {HEIGHT}"
     width="{CARD_W}" height="{HEIGHT}" role="img" aria-label="{esc(username)} — profile banner">
  <title>{esc(username)} — {esc(ROLE)}</title>
  <defs>
    {defs_card(CARD_W, HEIGHT)}
    {type_reveal("promptClip", x, prompt_y - 13, prompt_w + 2, 20, 0.2, prompt_dur)}
    {type_reveal("cmdClip", command_x, prompt_y - 13, command_w + 4, 20, command_begin, command_dur)}
    <linearGradient id="dotFade" x1="1" y1="0" x2="0" y2="0">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.30"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
    <mask id="dotMask">
      <rect x="0" y="0" width="{CARD_W}" height="{HEIGHT}" fill="url(#dotFade)"/>
    </mask>
  </defs>

  {card_shell(CARD_W, HEIGHT)}

  <g mask="url(#dotMask)">{dots}</g>

  <text x="{x}" y="{prompt_y}" fill="{GREEN}" font-family="{MONO}" font-size="{PROMPT_FONT}"
        clip-path="url(#promptClip)" xml:space="preserve">{esc(prompt)}</text>
  <text x="{command_x}" y="{prompt_y}" fill="{FG}" font-family="{MONO}" font-size="{PROMPT_FONT}"
        clip-path="url(#cmdClip)">{esc(command)}</text>
  {caret(command_x + command_w + 3, prompt_y - 12, w=7, h=15, begin=command_begin + command_dur)}

  <!-- Right-hand status, so the top line is balanced rather than left-heavy. -->
  <g>
    {fade_in(tagline_begin, 0.5)}
    <circle cx="{CARD_W - PAD - 148}" cy="{prompt_y - 4}" r="3.5" fill="{GREEN}"/>
    <text x="{CARD_W - PAD}" y="{prompt_y}" fill="{DIM}" font-family="{MONO}" font-size="12"
          text-anchor="end">rebuilt daily by CI</text>
  </g>

  <!-- The answer to `whoami`: name, then what the name does. -->
  <g>
    {fade_in(answer_begin, 0.55, shift=10)}
    <text x="{x - 2}" y="{118}" fill="{FG}" font-family="{MONO}" font-size="{NAME_FONT}"
          font-weight="700" letter-spacing="-1.5">{esc(username)}</text>
    <text x="{x}" y="{146}" fill="{DIM}" font-family="{MONO}" font-size="13.5"
          letter-spacing="0.2">{esc(ROLE)}</text>
  </g>

  <g>
    {fade_in(tagline_begin, 0.5)}
    <line x1="{x}" y1="{162}" x2="{CARD_W - PAD}" y2="{162}" stroke="{BORDER}" stroke-width="1"/>
    <text x="{x}" y="180" fill="{GREEN}" font-family="{MONO}" font-size="13.5">▸</text>
  </g>
  {tagline_elems}

  {card_border(CARD_W, HEIGHT)}
</svg>
'''


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(render_svg(username))
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
