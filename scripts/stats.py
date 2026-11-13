"""Render animated GitHub stats cards (stats.svg, languages.svg) for the profile README."""

import json
import os
import sys
import urllib.request
from html import escape

USER = os.environ["GH_USER"]
TOKEN = os.environ["GH_TOKEN"]
OUT = sys.argv[1] if len(sys.argv) > 1 else "dist"

QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    pullRequests { totalCount }
    issues { totalCount }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar { totalContributions }
    }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""

BG, BORDER, TITLE, TEXT, MUTED, ACCENT = "#0d1117", "#1f2937", "#0aa5a8", "#e6edf3", "#8b949e", "#3178c6"
FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', sans-serif"


def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]["user"]


def card(width, height, title, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">
<style>
  .t {{ font: 600 18px {FONT}; fill: {TITLE}; animation: fade .8s ease-out both; }}
  .l {{ font: 400 14px {FONT}; fill: {MUTED}; }}
  .v {{ font: 700 14px {FONT}; fill: {TEXT}; }}
  .row {{ opacity: 0; animation: fade .6s ease-out forwards; }}
  .bar {{ transform-origin: left; transform: scaleX(0); animation: grow 1.1s cubic-bezier(.2,.8,.2,1) forwards; }}
  @keyframes fade {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: none; }} }}
  @keyframes grow {{ to {{ transform: scaleX(1); }} }}
</style>
<rect x=".5" y=".5" rx="10" width="{width - 1}" height="{height - 1}" fill="{BG}" stroke="{BORDER}"/>
<text x="25" y="38" class="t">{escape(title)}</text>
{body}
</svg>"""


def stats_card(u):
    cc = u["contributionsCollection"]
    stars = sum(r["stargazerCount"] for r in u["repositories"]["nodes"])
    rows = [
        ("⭐", "Total stars", stars),
        ("🔥", "Contributions (last year)", cc["contributionCalendar"]["totalContributions"]),
        ("📝", "Commits (last year)", cc["totalCommitContributions"] + cc["restrictedContributionsCount"]),
        ("🔀", "Pull requests", u["pullRequests"]["totalCount"]),
        ("📦", "Public repositories", u["repositories"]["totalCount"]),
        ("👥", "Followers", u["followers"]["totalCount"]),
    ]
    rows = [r for r in rows if r[1] != "Total stars" or r[2] > 0]
    body = ""
    for i, (icon, label, value) in enumerate(rows):
        y = 72 + i * 27
        body += (
            f'<g class="row" style="animation-delay:{0.15 + i * 0.12:.2f}s">'
            f'<text x="25" y="{y}" class="l">{icon}  {escape(label)}</text>'
            f'<text x="330" y="{y}" class="v" text-anchor="end">{value:,}</text></g>\n'
        )
    return card(355, 240, "Alberto's GitHub Stats", body)


def languages_card(u):
    totals = {}
    for repo in u["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            name = e["node"]["name"]
            entry = totals.setdefault(name, [0, e["node"]["color"] or ACCENT])
            entry[0] += e["size"]
    top = sorted(totals.items(), key=lambda kv: -kv[1][0])[:6]
    total = sum(v[0] for _, v in top) or 1
    body = ""
    for i, (name, (size, color)) in enumerate(top):
        pct = size / total * 100
        y = 66 + i * 28
        bar_w = max(2, 305 * pct / 100)
        body += (
            f'<g class="row" style="animation-delay:{0.15 + i * 0.12:.2f}s">'
            f'<text x="25" y="{y}" class="l">{escape(name)}</text>'
            f'<text x="330" y="{y}" class="v" text-anchor="end">{pct:.1f}%</text>'
            f'<rect x="25" y="{y + 6}" width="305" height="6" rx="3" fill="{BORDER}"/>'
            f'<rect class="bar" style="animation-delay:{0.3 + i * 0.12:.2f}s" x="25" y="{y + 6}" '
            f'width="{bar_w:.1f}" height="6" rx="3" fill="{color}"/></g>\n'
        )
    return card(355, 240, "Most Used Languages", body)


def main():
    u = fetch()
    os.makedirs(OUT, exist_ok=True)
    for name, svg in (("stats.svg", stats_card(u)), ("languages.svg", languages_card(u))):
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(svg)
    print("ok")


if __name__ == "__main__":
    main()
