"""Generate a classic GitHub-style green contribution calendar SVG.

Real data straight from the GraphQL contribution calendar -- same green
levels GitHub itself uses, rendered as our own asset instead of depending
on an external streak-stats service for the hero slot.
"""

from pathlib import Path

from _github_api import GITHUB_USERNAME, graphql

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "assets" / "contribution-graph.svg"

BG = "#06161d"
TEXT = "#8b949e"
LEVEL_COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

CELL = 11
GAP = 3
LEFT_PAD = 28
TOP_PAD = 26

CONTRIBUTIONS_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount weekday } }
      }
    }
  }
}
"""


def fetch_calendar():
    try:
        result = graphql(CONTRIBUTIONS_QUERY, {"login": GITHUB_USERNAME})
        calendar = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        return calendar["weeks"], calendar["totalContributions"]
    except Exception as error:  # pragma: no cover - network best-effort
        print(f"Warning: could not fetch contribution calendar ({error})")
        return [], 0


def level_for(count: int) -> int:
    if count == 0:
        return 0
    if count <= 2:
        return 1
    if count <= 5:
        return 2
    if count <= 9:
        return 3
    return 4


def build_svg(weeks, total: int) -> str:
    n_weeks = len(weeks) or 1
    width = LEFT_PAD + n_weeks * (CELL + GAP)
    height = TOP_PAD + 7 * (CELL + GAP) + 20

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" '
        f'role="img" aria-label="{GITHUB_USERNAME}\'s GitHub contribution graph, {total} contributions this year">',
        '  <style>text{font-family:"Courier New",Courier,monospace;}</style>',
        f'  <rect width="{width}" height="{height}" fill="{BG}"/>',
        f'  <text x="{LEFT_PAD}" y="16" fill="{TEXT}" font-size="12">{total} contributions in the last year</text>',
    ]

    day_labels = {1: "Mon", 3: "Wed", 5: "Fri"}
    for weekday, label in day_labels.items():
        y = TOP_PAD + weekday * (CELL + GAP) + CELL - 2
        lines.append(f'  <text x="0" y="{y}" fill="{TEXT}" font-size="9">{label}</text>')

    for week_index, week in enumerate(weeks):
        x = LEFT_PAD + week_index * (CELL + GAP)
        for day in week["contributionDays"]:
            weekday = day["weekday"]
            y = TOP_PAD + weekday * (CELL + GAP)
            color = LEVEL_COLORS[level_for(day["contributionCount"])]
            lines.append(
                f'  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}">'
                f'<title>{day["date"]}: {day["contributionCount"]} contributions</title></rect>'
            )

    legend_x = width - LEFT_PAD - (len(LEVEL_COLORS) * (CELL + GAP)) - 30
    legend_y = height - 14
    lines.append(f'  <text x="{legend_x - 26}" y="{legend_y + 9}" fill="{TEXT}" font-size="9">Less</text>')
    for i, color in enumerate(LEVEL_COLORS):
        lines.append(f'  <rect x="{legend_x + i * (CELL + GAP)}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}"/>')
    lines.append(
        f'  <text x="{legend_x + len(LEVEL_COLORS) * (CELL + GAP) + 4}" y="{legend_y + 9}" fill="{TEXT}" font-size="9">More</text>'
    )

    lines.append("</svg>")
    return "\n".join(lines)


def main():
    weeks, total = fetch_calendar()
    svg = build_svg(weeks, total)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(svg)
    print(f"Generated contribution graph at {OUTPUT_PATH} ({total} contributions)")


if __name__ == "__main__":
    main()
