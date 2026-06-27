"""Generate a calm animated SVG banner for a GitHub profile README."""

from pathlib import Path
from random import Random

WIDTH = 960
HEIGHT = 190
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "assets" / "aesthetic-banner.svg"


def build_svg():
    rng = Random(2201)
    nodes = [
        (120, 126),
        (214, 78),
        (308, 118),
        (418, 68),
        (520, 112),
        (642, 76),
        (746, 120),
        (846, 86),
    ]
    lines = [
        (
            f'<svg width="100%" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" '
            'xmlns="http://www.w3.org/2000/svg" role="img" '
            'aria-label="Minimal animated banner for Shreshtha">'
        ),
        "  <defs>",
        '    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '      <stop offset="0" stop-color="#09111f"/>',
        '      <stop offset="0.55" stop-color="#111827"/>',
        '      <stop offset="1" stop-color="#15111f"/>',
        "    </linearGradient>",
        '    <linearGradient id="name" x1="0" y1="0" x2="1" y2="0">',
        '      <stop offset="0" stop-color="#c7d2fe"/>',
        '      <stop offset="0.5" stop-color="#dbeafe"/>',
        '      <stop offset="1" stop-color="#f0b7c8"/>',
        "    </linearGradient>",
        '    <filter id="blur">',
        '      <feGaussianBlur stdDeviation="18"/>',
        "    </filter>",
        "  </defs>",
        '  <rect width="960" height="190" rx="18" fill="url(#bg)"/>',
        '  <circle cx="220" cy="38" r="92" fill="#9db4ff" opacity="0.13" filter="url(#blur)">',
        '    <animate attributeName="cx" values="210;250;210" dur="9s" repeatCount="indefinite"/>',
        "  </circle>",
        '  <circle cx="760" cy="150" r="120" fill="#f0b7c8" opacity="0.10" filter="url(#blur)">',
        '    <animate attributeName="cy" values="145;118;145" dur="10s" repeatCount="indefinite"/>',
        "  </circle>",
        "  <style>",
        "    .soft-line { stroke: #9db4ff; stroke-width: 1; opacity: 0.22; }",
        "    .node { fill: #dbeafe; opacity: 0.72; }",
        "    .tiny { fill: #f0b7c8; opacity: 0.48; }",
        "    .name { font-family: 'Courier New', Courier, monospace; font-weight: 700; letter-spacing: 0; }",
        "  </style>",
        '  <g fill="none">',
    ]

    for index, ((x1, y1), (x2, y2)) in enumerate(zip(nodes, nodes[1:])):
        lines.extend(
            [
                f'    <path class="soft-line" d="M{x1} {y1} C{x1 + 36} {y1 - 28}, {x2 - 36} {y2 + 28}, {x2} {y2}" pathLength="1">',
                (
                    f'      <animate attributeName="stroke-dasharray" values="0 1;0.72 1;0 1" '
                    f'dur="{6.5 + index * 0.25:.2f}s" begin="{index * 0.22:.2f}s" repeatCount="indefinite"/>'
                ),
                "    </path>",
            ]
        )

    lines.append("  </g>")

    for index, (x, y) in enumerate(nodes):
        lines.extend(
            [
                f'  <circle class="node" cx="{x}" cy="{y}" r="3.2">',
                (
                    f'    <animate attributeName="opacity" values="0.38;0.82;0.38" '
                    f'dur="{4.6 + index * 0.18:.2f}s" begin="{index * 0.16:.2f}s" repeatCount="indefinite"/>'
                ),
                "  </circle>",
            ]
        )

    for _ in range(26):
        x = rng.randrange(55, WIDTH - 55)
        y = rng.randrange(34, HEIGHT - 26)
        radius = rng.choice([1.0, 1.2, 1.4, 1.6])
        lines.extend(
            [
                f'  <circle class="tiny" cx="{x}" cy="{y}" r="{radius}">',
                (
                    f'    <animate attributeName="opacity" values="0.12;0.5;0.12" '
                    f'dur="{rng.uniform(5.2, 8.8):.2f}s" begin="{rng.uniform(0, 3):.2f}s" repeatCount="indefinite"/>'
                ),
                "  </circle>",
            ]
        )

    lines.extend(
        [
            '  <text class="name" x="480" y="86" fill="url(#name)" font-size="46" text-anchor="middle">SHRESHTHA</text>',
            '  <text x="480" y="122" fill="#a7b4c8" font-family="\'Courier New\', Courier, monospace" font-size="15" text-anchor="middle">',
            "    AI/ML enthusiast · RAG systems · AI Developer",
            "  </text>",
            '  <text x="480" y="154" fill="#64748b" font-family="\'Courier New\', Courier, monospace" font-size="12" text-anchor="middle">',
            "    Even AI can't predict me",
            "  </text>",
            "</svg>",
        ]
    )
    return "\n".join(lines)


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(build_svg())
    print(f"Generated aesthetic banner at {OUTPUT_PATH}")


if __name__ == "__main__":
    main()