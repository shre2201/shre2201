"""Generate an RPG-style character sheet SVG driven by real GitHub data.

XP bars are sized from actual language bytes across your repos (the
GitHub "languages" API), level comes from account age, and quests are
your repos with a status derived from how recently each was pushed to.
"""

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from _github_api import GITHUB_USERNAME, get_json, graphql

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "assets" / "skill-sheet.svg"

WIDTH = 720
PAD_X = 24
BAR_WIDTH = 320
ROW_H = 30
MAX_LANGUAGES = 6
MAX_QUESTS = 8

CLASS_LABEL = "AI/ML Class"

CREATED_AT_QUERY = """
query($login: String!) {
  user(login: $login) { createdAt }
}
"""


def fetch_data():
    repos = get_json(f"https://api.github.com/users/{GITHUB_USERNAME}/repos?per_page=100")
    repos = [repo for repo in repos if not repo.get("fork")]

    language_bytes = Counter()
    for repo in repos:
        try:
            languages = get_json(repo["languages_url"])
        except Exception:  # pragma: no cover - network best-effort
            continue
        for language, byte_count in languages.items():
            language_bytes[language] += byte_count

    created_at = None
    try:
        result = graphql(CREATED_AT_QUERY, {"login": GITHUB_USERNAME})
        created_at = result["data"]["user"]["createdAt"]
    except Exception as error:  # pragma: no cover - network best-effort
        print(f"Warning: could not fetch account age ({error}); defaulting level to 1")

    if created_at:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        years_active = max(0, (datetime.now(timezone.utc) - created).days // 365)
    else:
        years_active = 0

    return repos, language_bytes, years_active


def escape(text: str) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(repos, language_bytes, years_active) -> str:
    level = years_active + 1
    top_languages = language_bytes.most_common(MAX_LANGUAGES)
    total_bytes = sum(count for _, count in top_languages) or 1

    quests = sorted(repos, key=lambda repo: repo.get("pushed_at") or "", reverse=True)[:MAX_QUESTS]
    now = datetime.now(timezone.utc)

    height = 150 + len(top_languages) * ROW_H + 40 + len(quests) * ROW_H + 30

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" width="100%" '
        f'role="img" aria-label="Character sheet generated from {GITHUB_USERNAME}\'s GitHub data">',
        "  <style>",
        '    text { font-family: "Courier New", Courier, monospace; }',
        "  </style>",
        f'  <rect width="{WIDTH}" height="{height}" rx="12" fill="#06161d"/>',
        f'  <rect width="{WIDTH}" height="56" rx="12" fill="#102027"/>',
        f'  <rect y="42" width="{WIDTH}" height="14" fill="#102027"/>',
        f'  <text x="{PAD_X}" y="34" fill="#dbeafe" font-size="18" font-weight="bold">{escape(GITHUB_USERNAME)}</text>',
        f'  <text x="{WIDTH - PAD_X}" y="34" fill="#facc15" font-size="16" text-anchor="end">Lv.{level}</text>',
        f'  <text x="{PAD_X}" y="50" fill="#7dd3fc" font-size="12">[{CLASS_LABEL}]</text>',
    ]

    y = 92
    lines.append(f'  <text x="{PAD_X}" y="{y}" fill="#94a3b8" font-size="13">Skills (by bytes written)</text>')
    y += 14
    for language, byte_count in top_languages:
        pct = byte_count / total_bytes
        y += ROW_H
        bar_x = PAD_X + 140
        lines.append(f'  <text x="{PAD_X}" y="{y}" fill="#dbeafe" font-size="13">{escape(language)}</text>')
        lines.append(f'  <rect x="{bar_x}" y="{y - 12}" width="{BAR_WIDTH}" height="14" fill="#1d2b37" rx="3"/>')
        lines.append(
            f'  <rect x="{bar_x}" y="{y - 12}" width="{BAR_WIDTH * pct:.1f}" height="14" fill="#9db4ff" rx="3"/>'
        )
        lines.append(
            f'  <text x="{bar_x + BAR_WIDTH + 10}" y="{y}" fill="#64748b" font-size="12">{pct * 100:.0f}%</text>'
        )

    y += ROW_H
    lines.append(f'  <text x="{PAD_X}" y="{y}" fill="#94a3b8" font-size="13">Quests</text>')
    y += 6
    for repo in quests:
        y += ROW_H
        pushed_at = repo.get("pushed_at")
        active = False
        if pushed_at:
            pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
            active = (now - pushed).days <= 30
        box = "[ ]" if active else "[x]"
        status = "in progress" if active else "shipped"
        color = "#f0b7c8" if active else "#4ade80"
        lines.append(
            f'  <text x="{PAD_X}" y="{y}" fill="{color}" font-size="13">{box} {escape(repo.get("name", "repo"))}'
            f'</text>'
        )
        lines.append(
            f'  <text x="{WIDTH - PAD_X}" y="{y}" fill="#64748b" font-size="12" text-anchor="end">'
            f"({status})</text>"
        )

    lines.append("</svg>")
    return "\n".join(lines)


def main():
    repos, language_bytes, years_active = fetch_data()
    svg = build_svg(repos, language_bytes, years_active)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(svg)
    print(f"Generated skill sheet at {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
