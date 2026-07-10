"""Grow an SVG tree from real GitHub activity.

Repos become branches (colored by each repo's dominant language), this
year's contributions become leaves, and account age sets the trunk size.
Re-running regenerates a slightly different tree as those numbers change.
"""

import math
import random
from datetime import datetime, timezone
from pathlib import Path

from _github_api import GITHUB_USERNAME, get_json, graphql

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "assets" / "git-tree.svg"

WIDTH, HEIGHT = 900, 480
GROUND_Y = 420

LANGUAGE_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Java": "#b07219",
    "C++": "#f34b7d",
    "C": "#555555",
    "Shell": "#89e051",
    "Jupyter Notebook": "#DA5B0B",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    None: "#6b7280",
}

CONTRIBUTIONS_QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    contributionsCollection {
      contributionCalendar {
        totalContributions
      }
    }
  }
}
"""


def fetch_data():
    repos = get_json(f"https://api.github.com/users/{GITHUB_USERNAME}/repos?per_page=100&sort=created")
    repos = [repo for repo in repos if not repo.get("fork")]

    created_at = None
    total_contributions = 0
    try:
        result = graphql(CONTRIBUTIONS_QUERY, {"login": GITHUB_USERNAME})
        user = result["data"]["user"]
        created_at = user["createdAt"]
        total_contributions = user["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    except Exception as error:  # pragma: no cover - network best-effort
        print(f"Warning: could not fetch contributions via GraphQL ({error}); using fallback")

    if created_at:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        years_active = max(1, (datetime.now(timezone.utc) - created).days // 365)
    else:
        years_active = 1

    return repos, years_active, total_contributions


def build_svg(repos, years_active, total_contributions) -> str:
    branch_count = max(1, min(len(repos), 8))
    rng = random.Random(f"{GITHUB_USERNAME}-{branch_count}-{total_contributions}")

    trunk_width = min(46, 14 + years_active * 6)
    trunk_height = min(200, 110 + years_active * 16)
    trunk_top = GROUND_Y - trunk_height

    leaves_total = max(branch_count * 6, min(280, total_contributions))
    leaves_per_branch = max(6, leaves_total // branch_count)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="100%" '
        f'role="img" aria-label="A tree grown from {GITHUB_USERNAME}\'s GitHub activity">',
        '  <style>text{font-family:"Courier New",Courier,monospace;}</style>',
        f'  <rect width="{WIDTH}" height="{HEIGHT}" fill="#06161d"/>',
        f'  <line x1="40" y1="{GROUND_Y}" x2="{WIDTH - 40}" y2="{GROUND_Y}" stroke="#1d2b37" stroke-width="2"/>',
        f'  <path d="M{WIDTH / 2 - 10} {GROUND_Y} q-24 18 -50 14" stroke="#3a2b22" stroke-width="4" fill="none"/>',
        f'  <path d="M{WIDTH / 2 + 10} {GROUND_Y} q24 18 50 14" stroke="#3a2b22" stroke-width="4" fill="none"/>',
        f'  <rect x="{WIDTH / 2 - trunk_width / 2:.1f}" y="{trunk_top}" width="{trunk_width}" '
        f'height="{trunk_height}" rx="{trunk_width / 3:.1f}" fill="#4b3226"/>',
    ]

    spread_deg = 130
    branch_tips = []
    for i in range(branch_count):
        t = 0 if branch_count == 1 else i / (branch_count - 1)
        angle = math.radians(-90 + spread_deg * (t - 0.5))
        length = 90 + years_active * 12 + rng.uniform(-10, 10)
        base_x, base_y = WIDTH / 2, trunk_top + trunk_height * 0.15
        tip_x = base_x + math.cos(angle) * length
        tip_y = base_y + math.sin(angle) * length
        control_x = base_x + math.cos(angle) * length * 0.5 + rng.uniform(-20, 20)
        control_y = base_y + math.sin(angle) * length * 0.5
        lines.append(
            f'  <path d="M{base_x:.1f} {base_y:.1f} Q{control_x:.1f} {control_y:.1f} '
            f'{tip_x:.1f} {tip_y:.1f}" stroke="#4b3226" stroke-width="{max(3, trunk_width / 6):.1f}" '
            'fill="none" stroke-linecap="round"/>'
        )
        branch_tips.append((tip_x, tip_y))

    for i, (tip_x, tip_y) in enumerate(branch_tips):
        repo = repos[i] if i < len(repos) else None
        color = LANGUAGE_COLORS.get(repo.get("language") if repo else None, LANGUAGE_COLORS[None])
        for _ in range(leaves_per_branch):
            lx = tip_x + rng.uniform(-55, 55)
            ly = tip_y + rng.uniform(-45, 45)
            radius = rng.uniform(2.5, 5)
            opacity = rng.uniform(0.55, 0.95)
            lines.append(
                f'  <circle cx="{lx:.1f}" cy="{ly:.1f}" r="{radius:.1f}" fill="{color}" '
                f'opacity="{opacity:.2f}"/>'
            )

    legend_y = HEIGHT - 78
    lines.append(f'  <text x="40" y="{legend_y}" fill="#7dd3fc" font-size="13">$ git log --graph --all --decorate</text>')
    for i, repo in enumerate(repos[:branch_count]):
        color = LANGUAGE_COLORS.get(repo.get("language"), LANGUAGE_COLORS[None])
        lx = 40 + (i % 4) * 210
        ly = legend_y + 24 + (i // 4) * 18
        lines.append(f'  <circle cx="{lx}" cy="{ly - 4}" r="4" fill="{color}"/>')
        lines.append(f'  <text x="{lx + 12}" y="{ly}" fill="#94a3b8" font-size="12">{repo.get("name", "repo")}</text>')

    lines.append(
        f'  <text x="{WIDTH / 2}" y="{HEIGHT - 10}" fill="#64748b" font-size="12" text-anchor="middle">'
        f"{years_active} year(s) active &#183; {len(repos)} repos &#183; "
        f"{total_contributions} contributions this year</text>"
    )
    lines.append("</svg>")
    return "\n".join(lines)


def main():
    repos, years_active, total_contributions = fetch_data()
    svg = build_svg(repos, years_active, total_contributions)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(svg)
    print(f"Generated git tree at {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
