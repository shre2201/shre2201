"""Generate a looping animated SVG of a Jupyter cell "running" against real
GitHub data: types out a query, then reveals the real output line by line.

Same SMIL-only constraint as everything else here (no JS in an img-embedded
SVG) -- the "typing" is a clip-path reveal, not actual text input.
"""

from collections import Counter
from pathlib import Path

from _github_api import GITHUB_USERNAME, get_json, graphql

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "assets" / "jupyter-cell.svg"

WIDTH, HEIGHT = 600, 190
BG = "#06161d"
PANEL = "#0b1c26"
PROMPT_COLOR = "#4ade80"
CODE_COLOR = "#dbeafe"
OUT_LABEL_COLOR = "#f87171"
TEXT_COLOR = "#94a3b8"
VALUE_COLOR = "#7dd3fc"

CYCLE_S = 9

CONTRIBUTIONS_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar { totalContributions }
    }
  }
}
"""


def fetch_data():
    repos = get_json(f"https://api.github.com/users/{GITHUB_USERNAME}/repos?per_page=100")
    repos = [r for r in repos if not r.get("fork")]
    languages = Counter(r["language"] for r in repos if r.get("language"))
    top_language = languages.most_common(1)[0][0] if languages else "n/a"

    contributions = 0
    try:
        result = graphql(CONTRIBUTIONS_QUERY, {"login": GITHUB_USERNAME})
        contributions = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    except Exception as error:  # pragma: no cover - network best-effort
        print(f"Warning: could not fetch contributions ({error})")

    return {"repos": len(repos), "top_language": top_language, "contributions": contributions}


def build_svg(data: dict) -> str:
    code = "profile.summary()"
    code_char_w = 9.4
    code_x = 90
    code_width = len(code) * code_char_w + 6

    output_lines = [
        f'repos           = {data["repos"]}',
        f'top_language    = "{data["top_language"]}"',
        f'contributions   = {data["contributions"]}  # this year',
    ]

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="100%" '
        f'role="img" aria-label="Animated Jupyter cell querying real GitHub stats for {GITHUB_USERNAME}">',
        '  <style>text{font-family:"Courier New",Courier,monospace;font-size:15px;}</style>',
        f'  <rect width="{WIDTH}" height="{HEIGHT}" fill="{BG}"/>',
        f'  <rect x="12" y="12" width="{WIDTH - 24}" height="{HEIGHT - 24}" rx="10" fill="{PANEL}"/>',
        f'  <circle cx="30" cy="28" r="5" fill="#fb7185"/>',
        f'  <circle cx="46" cy="28" r="5" fill="#facc15"/>',
        f'  <circle cx="62" cy="28" r="5" fill="#4ade80"/>',
        f'  <text x="{WIDTH - 28}" y="33" fill="{TEXT_COLOR}" font-size="12" text-anchor="end">'
        f"{GITHUB_USERNAME} — jupyter</text>",
        f'  <text x="28" y="60" fill="{PROMPT_COLOR}">In [1]:</text>',
    ]

    # Typing reveal: a clip rect widens in one discrete jump per character
    # (calcMode="discrete"), so each letter pops in like a real keystroke
    # instead of the text smoothly sliding into view.
    typing_start, typing_end = 0.02, 0.32
    n = len(code)
    step_keytimes = [typing_start + i * (typing_end - typing_start) / n for i in range(n + 1)]
    step_widths = [round(i * code_char_w) for i in range(n + 1)]

    width_keytimes = [0.0] + step_keytimes + [0.95, 1.0]
    width_values = [0] + step_widths + [step_widths[-1], step_widths[-1]]
    cursor_x_values = [code_x] + [code_x + w for w in step_widths] + [code_x + step_widths[-1], code_x]

    lines.append(
        f'  <clipPath id="typeClip"><rect x="{code_x}" y="46" width="0" height="20">'
        f'<animate attributeName="width" '
        f'values="{";".join(str(v) for v in width_values)}" '
        f'keyTimes="{";".join(f"{t:.4f}" for t in width_keytimes)}" '
        f'calcMode="discrete" dur="{CYCLE_S}s" repeatCount="indefinite"/>'
        f"</rect></clipPath>"
    )
    lines.append(f'  <g clip-path="url(#typeClip)"><text x="{code_x}" y="60" fill="{CODE_COLOR}">{code}</text></g>')
    lines.append(
        f'  <rect y="46" width="2" height="18" fill="{CODE_COLOR}">'
        f'<animate attributeName="x" '
        f'values="{";".join(str(v) for v in cursor_x_values)}" '
        f'keyTimes="{";".join(f"{t:.4f}" for t in width_keytimes)}" '
        f'calcMode="discrete" dur="{CYCLE_S}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="1;0;1;0;1;0;1;0" dur="0.9s" repeatCount="indefinite"/>'
        f"</rect>"
    )

    out_label_begin = 0.36
    lines.append(
        f'  <text x="28" y="90" fill="{OUT_LABEL_COLOR}" opacity="0">Out[1]:'
        f'<animate attributeName="opacity" values="0;0;1;1;0" '
        f'keyTimes="0;{out_label_begin};{out_label_begin + 0.03};0.95;1" dur="{CYCLE_S}s" '
        f'repeatCount="indefinite"/></text>'
    )

    row_y = [112, 132, 152]
    stagger = 0.08
    for index, line in enumerate(output_lines):
        begin = out_label_begin + 0.05 + index * stagger
        key = min(begin + 0.04, 0.94)
        lines.append(
            f'  <text x="46" y="{row_y[index]}" fill="{VALUE_COLOR}" opacity="0">{line}'
            f'<animate attributeName="opacity" values="0;0;1;1;0" '
            f'keyTimes="0;{begin:.2f};{key:.2f};0.95;1" dur="{CYCLE_S}s" repeatCount="indefinite"/></text>'
        )

    lines.append("</svg>")
    return "\n".join(lines)


def main():
    data = fetch_data()
    svg = build_svg(data)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(svg)
    print(f"Generated jupyter cell at {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
