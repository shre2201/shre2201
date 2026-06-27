"""Generate a GitHub README-compatible animated burn-text SVG."""

from pathlib import Path
from random import Random

TEXT_LINES = ["SHRESHTHA", "builds things that feel useful"]
FONT_SIZE = 54
SUBTITLE_SIZE = 18
WIDTH = 960
HEIGHT = 190
LOOP_SECONDS = 7.8

START_COLOR = "#80757a"
BURN_COLORS = ["#ffffff", "#fff75d", "#ff8a1f", "#fb3f2f", "#8a003c"]
FINAL_COLORS = ["#22d3ee", "#f8e16c"]
SMOKE_CHARS = [".", ":", "'", "`"]

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = SCRIPT_DIR.parent / "assets" / "burn-banner.svg"


def lerp(a, b, t):
    return int(a + (b - a) * t)


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def blend(left, right, t):
    return tuple(lerp(left[i], right[i], t) for i in range(3))


def gradient(stops, count):
    rgbs = [hex_to_rgb(stop) for stop in stops]
    if count <= 1:
        return [stops[0]]

    result = []
    segments = len(rgbs) - 1
    for index in range(count):
        position = index / (count - 1) * segments
        low = min(int(position), segments - 1)
        result.append(rgb_to_hex(blend(rgbs[low], rgbs[low + 1], position - low)))
    return result


def escape_xml(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def char_positions():
    positions = []
    title = TEXT_LINES[0]
    subtitle = TEXT_LINES[1]

    title_spacing = 42
    title_x = (WIDTH - (len(title) - 1) * title_spacing) / 2
    for index, char in enumerate(title):
        positions.append(
            {
                "char": char,
                "x": title_x + index * title_spacing,
                "y": 88,
                "size": FONT_SIZE,
                "weight": 800,
                "delay": index * 0.13,
                "line": 0,
            }
        )

    subtitle_spacing = 12
    subtitle_x = (WIDTH - (len(subtitle) - 1) * subtitle_spacing) / 2
    for index, char in enumerate(subtitle):
        if char == " ":
            continue
        positions.append(
            {
                "char": char,
                "x": subtitle_x + index * subtitle_spacing,
                "y": 132,
                "size": SUBTITLE_SIZE,
                "weight": 600,
                "delay": 1.15 + index * 0.035,
                "line": 1,
            }
        )

    return positions


def build_svg():
    rng = Random(20260627)
    final_colors = gradient(FINAL_COLORS, len(TEXT_LINES))
    burn_key_times = "0;0.06;0.10;0.14;0.18;0.24;0.36;0.76;1"
    lines = [
        (
            f'<svg width="100%" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" '
            'xmlns="http://www.w3.org/2000/svg" role="img" '
            'aria-label="Animated burn banner for Shreshtha">'
        ),
        "  <defs>",
        '    <linearGradient id="ember-bg" x1="0" y1="0" x2="1" y2="1">',
        '      <stop offset="0" stop-color="#080f14"/>',
        '      <stop offset="0.56" stop-color="#13242b"/>',
        '      <stop offset="1" stop-color="#1c1118"/>',
        "    </linearGradient>",
        '    <radialGradient id="heat" cx="50%" cy="78%" r="70%">',
        '      <stop offset="0" stop-color="#fb7185" stop-opacity="0.22"/>',
        '      <stop offset="0.42" stop-color="#f8e16c" stop-opacity="0.10"/>',
        '      <stop offset="1" stop-color="#06161d" stop-opacity="0"/>',
        "    </radialGradient>",
        '    <filter id="soft-glow">',
        '      <feGaussianBlur stdDeviation="2.5" result="blur"/>',
        '      <feMerge>',
        '        <feMergeNode in="blur"/>',
        '        <feMergeNode in="SourceGraphic"/>',
        '      </feMerge>',
        "    </filter>",
        "  </defs>",
        '  <rect width="960" height="190" rx="18" fill="url(#ember-bg)"/>',
        '  <rect width="960" height="190" rx="18" fill="url(#heat)"/>',
        "  <style>",
        "    .char { font-family: 'Courier New', Courier, monospace; text-anchor: middle; dominant-baseline: middle; }",
        "    .title-char { letter-spacing: 0; }",
        "    .smoke { font-family: 'Courier New', Courier, monospace; opacity: 0; }",
        "    .spark { opacity: 0; }",
        "  </style>",
        '  <g filter="url(#soft-glow)">',
    ]

    for index, item in enumerate(char_positions()):
        final = final_colors[item["line"]]
        delay = item["delay"]
        x = item["x"]
        y = item["y"]
        char = escape_xml(item["char"])
        klass = "char title-char" if item["line"] == 0 else "char"

        burn_values = ";".join([START_COLOR, *BURN_COLORS, final, final, START_COLOR])
        lines.extend(
            [
                (
                    f'    <text class="{klass}" x="{x:.1f}" y="{y:.1f}" '
                    f'font-size="{item["size"]}" font-weight="{item["weight"]}" '
                    f'fill="{START_COLOR}">{char}'
                ),
                (
                    f'      <animate attributeName="fill" dur="{LOOP_SECONDS}s" '
                    f'begin="{delay:.2f}s" repeatCount="indefinite" '
                    f'values="{burn_values}" keyTimes="{burn_key_times}"/>'
                ),
                (
                    f'      <animateTransform attributeName="transform" type="translate" '
                    f'dur="{LOOP_SECONDS}s" begin="{delay:.2f}s" repeatCount="indefinite" '
                    'values="0 0; 0 -3; 0 1; 0 0; 0 0" '
                    'keyTimes="0;0.12;0.2;0.32;1"/>'
                ),
                (
                    f'      <animate attributeName="opacity" dur="{LOOP_SECONDS}s" '
                    f'begin="{delay:.2f}s" repeatCount="indefinite" '
                    'values="0.55;1;0.78;1;1;0.55" '
                    'keyTimes="0;0.1;0.14;0.24;0.76;1"/>'
                ),
                "    </text>",
            ]
        )

        if item["line"] == 0:
            smoke_x = x + rng.uniform(-10, 10)
            smoke_y = y - rng.uniform(26, 42)
            smoke = escape_xml(rng.choice(SMOKE_CHARS))
            lines.extend(
                [
                    (
                        f'    <text class="smoke" x="{smoke_x:.1f}" y="{smoke_y:.1f}" '
                        f'font-size="{rng.randrange(16, 23)}" fill="#b6c4c9">{smoke}'
                    ),
                    (
                        f'      <animate attributeName="opacity" dur="{LOOP_SECONDS}s" '
                        f'begin="{delay + 0.15:.2f}s" repeatCount="indefinite" '
                        'values="0;0.52;0.18;0;0" keyTimes="0;0.08;0.18;0.32;1"/>'
                    ),
                    (
                        f'      <animateTransform attributeName="transform" type="translate" '
                        f'dur="{LOOP_SECONDS}s" begin="{delay + 0.15:.2f}s" '
                        'repeatCount="indefinite" values="0 0; 0 -12; 0 -28; 0 -28" '
                        'keyTimes="0;0.16;0.34;1"/>'
                    ),
                    "    </text>",
                ]
            )

            spark_x = x + rng.uniform(-12, 12)
            spark_y = y + rng.uniform(20, 36)
            lines.extend(
                [
                    (
                        f'    <circle class="spark" cx="{spark_x:.1f}" cy="{spark_y:.1f}" '
                        f'r="{rng.uniform(1.4, 2.6):.1f}" fill="#f8e16c">'
                    ),
                    (
                        f'      <animate attributeName="opacity" dur="{LOOP_SECONDS}s" '
                        f'begin="{delay + 0.08:.2f}s" repeatCount="indefinite" '
                        'values="0;1;0.2;0;0" keyTimes="0;0.05;0.14;0.24;1"/>'
                    ),
                    (
                        f'      <animateTransform attributeName="transform" type="translate" '
                        f'dur="{LOOP_SECONDS}s" begin="{delay + 0.08:.2f}s" '
                        'repeatCount="indefinite" values="0 0; 0 -9; 0 -18; 0 -18" '
                        'keyTimes="0;0.12;0.24;1"/>'
                    ),
                    "    </circle>",
                ]
            )

    lines.extend(
        [
            "  </g>",
            '  <text x="480" y="166" fill="#94a3b8" font-family="\'Courier New\', Courier, monospace" font-size="13" text-anchor="middle">',
            "    <tspan fill=\"#22d3ee\">$</tspan> ./ignite-profile --style original",
            "  </text>",
            "</svg>",
        ]
    )
    return "\n".join(lines)


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(build_svg())
    print(f"Generated burn banner at {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
