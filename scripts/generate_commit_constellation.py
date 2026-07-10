"""Plot recent commit activity as a night sky.

Each recent push becomes a star: hour-of-day sets its horizontal position,
day-of-week sets its vertical band, and the number of commits in that push
sets its brightness/size. No two users produce the same sky.
"""

import random
from datetime import datetime, timezone
from pathlib import Path

from _github_api import GITHUB_USERNAME, get_json

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "assets" / "commit-constellation.svg"

WIDTH, HEIGHT = 900, 420
DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def fetch_pushes():
    pushes = []
    for page in (1, 2, 3):
        events = get_json(
            f"https://api.github.com/users/{GITHUB_USERNAME}/events/public?per_page=100&page={page}"
        )
        if not events:
            break
        for event in events:
            if event.get("type") != "PushEvent":
                continue
            created_at = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
            commit_count = max(1, int(event.get("payload", {}).get("size", 1)))
            pushes.append((created_at, commit_count))
        if len(events) < 100:
            break
    return pushes


def build_svg(pushes) -> str:
    rng = random.Random(f"{GITHUB_USERNAME}-{len(pushes)}")

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="100%" '
        f'role="img" aria-label="Night sky built from {GITHUB_USERNAME}\'s recent commit activity">',
        '  <style>text{font-family:"Courier New",Courier,monospace;}</style>',
        f'  <rect width="{WIDTH}" height="{HEIGHT}" fill="#050912"/>',
    ]

    # faint background stars for atmosphere
    for _ in range(120):
        x = rng.uniform(20, WIDTH - 20)
        y = rng.uniform(20, HEIGHT - 70)
        r = rng.choice([0.6, 0.8, 1.0])
        lines.append(f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#ffffff" opacity="{rng.uniform(0.08, 0.25):.2f}"/>')

    band_height = (HEIGHT - 90) / 7
    for day_index, label in enumerate(DAY_LABELS):
        y = 30 + band_height * day_index
        lines.append(f'  <text x="16" y="{y + band_height / 2 + 4:.1f}" fill="#334155" font-size="11">{label}</text>')

    if not pushes:
        lines.append(
            f'  <text x="{WIDTH / 2}" y="{HEIGHT / 2}" fill="#64748b" font-size="14" text-anchor="middle">'
            "no recent public activity to chart</text>"
        )
    else:
        latest = max(pushes, key=lambda item: item[0])
        for created_at, commit_count in pushes:
            hour_fraction = (created_at.hour * 60 + created_at.minute) / (24 * 60)
            x = 60 + hour_fraction * (WIDTH - 90)
            weekday = created_at.weekday()  # Monday=0
            band_y = 30 + band_height * weekday
            y = band_y + rng.uniform(band_height * 0.2, band_height * 0.8)
            radius = 1.6 + min(commit_count, 12) * 0.35
            opacity = min(1.0, 0.45 + commit_count * 0.06)
            is_latest = created_at == latest[0]
            color = "#f0b7c8" if is_latest else "#dbeafe"
            lines.append(f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" fill="{color}" opacity="{opacity:.2f}"/>')
            if radius > 3.2:
                lines.append(
                    f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="{radius + 3:.1f}" fill="none" '
                    f'stroke="{color}" stroke-width="0.6" opacity="{opacity * 0.4:.2f}"/>'
                )

        caption = f"the sky the moment you last shipped &#183; {latest[0].strftime('%b %d, %Y %H:%M UTC')}"
        lines.append(
            f'  <text x="{WIDTH / 2}" y="{HEIGHT - 34}" fill="#94a3b8" font-size="13" text-anchor="middle">'
            f"{caption}</text>"
        )

    lines.append(
        f'  <text x="{WIDTH / 2}" y="{HEIGHT - 12}" fill="#475569" font-size="11" text-anchor="middle">'
        f"{len(pushes)} pushes charted &#183; x-axis = hour of day (UTC), y-axis = day of week</text>"
    )
    lines.append("</svg>")
    return "\n".join(lines)


def main():
    pushes = fetch_pushes()
    svg = build_svg(pushes)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(svg)
    print(f"Generated commit constellation at {OUTPUT_PATH} ({len(pushes)} pushes)")


if __name__ == "__main__":
    main()
