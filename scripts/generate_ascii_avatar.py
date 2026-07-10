"""Generate a colored ASCII-art SVG portrait from a GitHub avatar."""

import urllib.request
from io import BytesIO
from pathlib import Path

from PIL import Image

GITHUB_USERNAME = "shre2201"
AVATAR_URL = f"https://github.com/{GITHUB_USERNAME}.png?size=460"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "assets" / "ascii-avatar.svg"

COLS = 70
ROWS = 45
CHAR_W = 9
CHAR_H = 16
# Dark-to-light ramp; index chosen by cell luminance.
RAMP = " .:-=+*%@#"


def fetch_avatar() -> Image.Image:
    request = urllib.request.Request(AVATAR_URL, headers={"User-Agent": "ascii-avatar-generator"})
    with urllib.request.urlopen(request, timeout=15) as response:
        data = response.read()
    return Image.open(BytesIO(data)).convert("RGB")


def build_svg(image: Image.Image) -> str:
    small = image.resize((COLS, ROWS), Image.LANCZOS)
    pixels = small.load()

    width = COLS * CHAR_W
    height = ROWS * CHAR_H

    lines = [
        f'<svg width="100%" height="{height}" viewBox="0 0 {width} {height}" '
        'xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-label="ASCII portrait of {GITHUB_USERNAME}">',
        f'  <rect width="{width}" height="{height}" fill="#06161d"/>',
        '  <style>text{font-family:"Courier New",Courier,monospace;'
        f'font-size:{CHAR_H}px;dominant-baseline:hanging;}}</style>',
    ]

    for row in range(ROWS):
        y = row * CHAR_H
        spans = []
        for col in range(COLS):
            r, g, b = pixels[col, row]
            luminance = 0.299 * r + 0.587 * g + 0.114 * b
            char_index = int((luminance / 255) * (len(RAMP) - 1))
            char = RAMP[char_index]
            if char == " ":
                continue
            x = col * CHAR_W
            escaped = "&amp;" if char == "&" else char
            spans.append(f'<tspan x="{x}" y="{y}" fill="rgb({r},{g},{b})">{escaped}</tspan>')
        if spans:
            lines.append(f'  <text>{"".join(spans)}</text>')

    lines.append("</svg>")
    return "\n".join(lines)


def main():
    image = fetch_avatar()
    svg = build_svg(image)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(svg)
    print(f"Generated ASCII avatar at {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
