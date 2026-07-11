"""Generate a 2x2 analytics panel (SVG) summarizing real GitHub activity.

Four small, information-dense charts rather than decoration: language
distribution by bytes written, monthly contribution trend, repo size
comparison, and activity by day of week. Data comes from the REST API
(repos, languages, events) and the GraphQL contribution calendar.
"""

import calendar
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("svg")
import matplotlib.colors
import matplotlib.pyplot as plt

from _github_api import GITHUB_USERNAME, get_json, graphql

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "assets" / "repo-analytics.svg"

BG = "#06161d"
PANEL_BG = "#0b1c26"
ACCENT = "#7dd3fc"
TEXT = "#94a3b8"
GRID = "#1d2b37"
TITLE = "#dbeafe"

CONTRIBUTIONS_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def fetch_repos():
    repos = get_json(f"https://api.github.com/users/{GITHUB_USERNAME}/repos?per_page=100")
    return [repo for repo in repos if not repo.get("fork")]


def fetch_language_bytes(repos):
    totals = Counter()
    for repo in repos:
        try:
            languages = get_json(repo["languages_url"])
        except Exception:  # pragma: no cover - network best-effort
            continue
        for language, byte_count in languages.items():
            totals[language] += byte_count
    return totals


def fetch_monthly_contributions():
    try:
        result = graphql(CONTRIBUTIONS_QUERY, {"login": GITHUB_USERNAME})
        weeks = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    except Exception as error:  # pragma: no cover - network best-effort
        print(f"Warning: could not fetch contribution calendar ({error})")
        return {}
    monthly = defaultdict(int)
    for week in weeks:
        for day in week["contributionDays"]:
            month_key = day["date"][:7]  # YYYY-MM
            monthly[month_key] += day["contributionCount"]
    return monthly


def fetch_weekday_activity():
    counts = Counter()
    for page in (1, 2, 3):
        try:
            events = get_json(
                f"https://api.github.com/users/{GITHUB_USERNAME}/events/public?per_page=100&page={page}"
            )
        except Exception:  # pragma: no cover - network best-effort
            break
        if not events:
            break
        for event in events:
            if event.get("type") != "PushEvent":
                continue
            created = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
            counts[created.weekday()] += 1
        if len(events) < 100:
            break
    return counts


def style_axes(ax, title):
    ax.set_facecolor(PANEL_BG)
    ax.set_title(title, color=TITLE, fontsize=10, fontfamily="monospace", loc="left", pad=8)
    ax.tick_params(colors=TEXT, labelsize=7)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(GRID)
    ax.grid(axis="x", color=GRID, linewidth=0.6, alpha=0.6)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontfamily("monospace")


def plot_languages(ax, language_bytes):
    ax.set_facecolor(BG)
    top = language_bytes.most_common(5)
    if not top:
        ax.text(0.5, 0.5, "no data", color=TEXT, ha="center", va="center", transform=ax.transAxes)
        ax.set_title("language distribution", color=TITLE, fontsize=10, fontfamily="monospace", loc="left", pad=8)
        return
    labels = [name for name, _ in top]
    values = [count for _, count in top]
    shades = [
        matplotlib.colors.to_hex(c)
        for c in plt.cm.Blues([0.9, 0.75, 0.6, 0.45, 0.3][: len(top)])
    ]
    wedges, _, autotexts = ax.pie(
        values,
        colors=shades,
        autopct="%1.0f%%",
        pctdistance=0.75,
        startangle=90,
        wedgeprops={"edgecolor": BG, "linewidth": 1.5},
        textprops={"color": BG, "fontsize": 7, "fontfamily": "monospace", "weight": "bold"},
    )
    ax.legend(
        wedges,
        labels,
        loc="center left",
        bbox_to_anchor=(1.0, 0.5),
        frameon=False,
        fontsize=7,
        labelcolor=TEXT,
    )
    ax.set_title("language distribution (bytes)", color=TITLE, fontsize=10, fontfamily="monospace", loc="left", pad=8)


def plot_monthly_contributions(ax, monthly):
    if not monthly:
        ax.text(0.5, 0.5, "no data", color=TEXT, ha="center", va="center", transform=ax.transAxes)
        style_axes(ax, "contributions per month")
        return
    keys = sorted(monthly.keys())[-12:]
    values = [monthly[k] for k in keys]
    labels = [f"{calendar.month_abbr[int(k[5:7])]}" for k in keys]
    ax.plot(labels, values, color=ACCENT, marker="o", markersize=4, linewidth=1.5)
    ax.fill_between(range(len(labels)), values, color=ACCENT, alpha=0.12)
    style_axes(ax, "contributions per month (last 12mo)")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", color=GRID, linewidth=0.6, alpha=0.6)


def plot_repo_sizes(ax, repos):
    ranked = sorted(repos, key=lambda r: r.get("size", 0), reverse=True)[:6][::-1]
    if not ranked:
        ax.text(0.5, 0.5, "no data", color=TEXT, ha="center", va="center", transform=ax.transAxes)
        style_axes(ax, "repo size (KB)")
        return
    labels = [r["name"] for r in ranked]
    values = [r.get("size", 0) for r in ranked]
    ax.barh(labels, values, color=ACCENT, height=0.55)
    style_axes(ax, "repo size (KB)")
    ax.set_xlabel("KB", color=TEXT, fontsize=7, fontfamily="monospace")


def plot_weekday_activity(ax, weekday_counts):
    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    values = [weekday_counts.get(i, 0) for i in range(7)]
    if not any(values):
        ax.text(0.5, 0.5, "no data", color=TEXT, ha="center", va="center", transform=ax.transAxes)
        style_axes(ax, "pushes by day of week")
        return
    ax.bar(day_labels, values, color=ACCENT, width=0.6)
    style_axes(ax, "pushes by day of week")


def build_figure(repos, language_bytes, monthly, weekday_counts):
    plt.rcParams["font.family"] = "monospace"
    fig, axes = plt.subplots(2, 2, figsize=(10, 6.2))
    fig.patch.set_facecolor(BG)

    plot_languages(axes[0][0], language_bytes)
    plot_monthly_contributions(axes[0][1], monthly)
    plot_repo_sizes(axes[1][0], repos)
    plot_weekday_activity(axes[1][1], weekday_counts)

    fig.suptitle(
        f"{GITHUB_USERNAME} · repo analytics", color=TITLE, fontsize=12, fontfamily="monospace", x=0.02, ha="left"
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig


def main():
    repos = fetch_repos()
    language_bytes = fetch_language_bytes(repos)
    monthly = fetch_monthly_contributions()
    weekday_counts = fetch_weekday_activity()

    fig = build_figure(repos, language_bytes, monthly, weekday_counts)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, format="svg", facecolor=BG)
    print(f"Generated repo analytics at {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
