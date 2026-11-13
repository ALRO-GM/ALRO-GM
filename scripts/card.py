"""Render the neofetch-style hero card (card-dark.svg, card-light.svg) with live GitHub data."""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from html import escape

USER = os.environ["GH_USER"]
TOKEN = os.environ["GH_TOKEN"]
OUT = sys.argv[1] if len(sys.argv) > 1 else "dist"
SINCE = date(2024, 7, 29)  # GitHub account creation

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar { totalContributions }
    }
    repositories(first: 100, ownerAffiliations: OWNER) { totalCount nodes { name } }
  }
}
"""

THEMES = {
    "dark": dict(bg="#0d1117", border="#30363d", text="#c9d1d9", key="#ffa657", value="#a5d6ff",
                 muted="#6e7681", accent="#0aa5a8", add="#3fb950", dele="#f85149",
                 hull="#c9d1d9", flame1="#ff7b00", flame2="#ffd166"),
    "light": dict(bg="#ffffff", border="#d0d7de", text="#24292f", key="#953800", value="#0a3069",
                  muted="#8c959f", accent="#087f80", add="#1a7f37", dele="#cf222e",
                  hull="#24292f", flame1="#e85d04", flame2="#f4a100"),
}

ROCKET = [
    ("hull", r"              /\              "),
    ("hull", r"             /  \             "),
    ("hull", r"            / /\ \            "),
    ("hull", r"           / /  \ \           "),
    ("hull", r"          |  ____  |          "),
    ("hull", r"          | |    | |          "),
    ("hull", r"          | |    | |          "),
    ("hull", r"          | |____| |          "),
    ("hull", r"          |   42   |          "),
    ("hull", r"          |  MAD   |          "),
    ("hull", r"         /|        |\         "),
    ("hull", r"        / |        | \        "),
    ("hull", r"       /  |        |  \       "),
    ("hull", r"      /___|________|___\      "),
    ("hull", r"          /_/_/\_\_\          "),
    ("flame1", r"          ( ) )( ( )          "),
    ("flame2", r"           ( )  ( )           "),
    ("flame1", r"            ) () (            "),
    ("flame2", r"             (  )             "),
    ("flame1", r"              ()              "),
]


def api(url, body=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode() if body else None,
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        raw = r.read()
        return r.status, (json.loads(raw) if raw.strip() else None)


def lines_of_code(repos):
    added = deleted = 0
    for name in repos:
        for _ in range(8):  # GitHub computes these stats lazily and answers 202 meanwhile
            try:
                status, data = api(f"https://api.github.com/repos/{USER}/{name}/stats/contributors")
            except urllib.error.HTTPError:
                data = None
                break
            if status == 200 and isinstance(data, list):
                break
            time.sleep(3)
        for c in data or []:
            if (c.get("author") or {}).get("login") == USER:
                added += sum(w["a"] for w in c["weeks"])
                deleted += sum(w["d"] for w in c["weeks"])
    return added, deleted


def uptime():
    today = date.today()
    months = (today.year - SINCE.year) * 12 + today.month - SINCE.month
    days = today.day - SINCE.day
    if days < 0:
        months -= 1
        prev = date(today.year, today.month, 1).toordinal() - 1
        days += date.fromordinal(prev).day
    y, m = divmod(months, 12)
    plural = lambda n, w: f"{n} {w}{'' if n == 1 else 's'}"
    return f"{plural(y, 'year')}, {plural(m, 'month')}, {plural(days, 'day')}"


def build_lines(data):
    u = data["user"]
    cc = u["contributionsCollection"]
    commits = cc["totalCommitContributions"] + cc["restrictedContributionsCount"]
    repos = [n["name"] for n in u["repositories"]["nodes"]]
    added, deleted = lines_of_code(repos)
    return [
        ("title", f"alberto@{USER.lower()}"),
        ("rule", ""),
        ("kv", "Role", "Software Developer · Product Builder"),
        ("kv", "School", "42 Madrid (albrodri)"),
        ("kv", "Building", "peer4u.app · solo, idea → production"),
        ("kv", "Location", "Madrid, Spain"),
        ("kv", "Uptime", uptime()),
        ("gap",),
        ("kv", "Mindset", "Ship · Measure · Own it end-to-end"),
        ("kv", "Stack.Web", "TypeScript, React 19, Fastify, Three.js"),
        ("kv", "Stack.AI", "Local LLMs, RAG, constrained decoding"),
        ("kv", "Stack.Ops", "Docker, Caddy, CI-gated deploys, €0 infra"),
        ("gap",),
        ("section", "Contact"),
        ("kv", "Email", "ajrd91@gmail.com"),
        ("kv", "Web", "peer4u.app · labtory.peer4u.app"),
        ("status", "Status", "Open to work & collaborations"),
        ("gap",),
        ("section", "GitHub Stats"),
        ("pair", ("Repos", f"{u['repositories']['totalCount']}"), ("Followers", f"{u['followers']['totalCount']}")),
        ("pair", ("Commits", f"{commits:,}"), ("Contributions", f"{cc['contributionCalendar']['totalContributions']:,}")),
        ("loc", added - deleted, added, deleted),
    ]


COLS = 58  # characters available in the info column


def dots(key, value):
    return "." * max(2, COLS - len(key) - len(value) - 3)


def render(lines, t):
    lh, x0, y0 = 21, 390, 34
    out = []
    for i, ln in enumerate(lines):
        y = y0 + i * lh
        delay = f"{0.25 + i * 0.07:.2f}s"
        kind = ln[0]
        if kind == "gap":
            continue
        g = f'<text x="{x0}" y="{y}" class="ln" style="animation-delay:{delay}">'
        if kind == "title":
            out.append(g + f'<tspan class="a">{escape(ln[1])}</tspan></text>')
        elif kind == "rule":
            out.append(g + f'<tspan class="m">{"─" * (COLS - 1)}</tspan></text>')
        elif kind == "section":
            out.append(g + f'<tspan class="m">─ </tspan><tspan class="a">{escape(ln[1])}</tspan>'
                       f'<tspan class="m"> {"─" * (COLS - len(ln[1]) - 4)}</tspan></text>')
        elif kind in ("kv", "status"):
            _, k, v = ln
            vv = ("● " + v) if kind == "status" else v
            dot_cls = "ok pulse" if kind == "status" else "v"
            body = (f'<tspan class="k">{escape(k)}</tspan>:<tspan class="m">{dots(k, vv)}</tspan> ')
            if kind == "status":
                body += f'<tspan class="{dot_cls}">●</tspan><tspan class="v"> {escape(v)}</tspan>'
            else:
                body += f'<tspan class="v">{escape(v)}</tspan>'
            out.append(g + body + "</text>")
        elif kind == "pair":
            (k1, v1), (k2, v2) = ln[1], ln[2]
            half = COLS // 2 - 2
            d1 = "." * max(2, half - len(k1) - len(v1) - 3)
            d2 = "." * max(2, COLS - half - 2 - len(k2) - len(v2) - 3)
            out.append(g + f'<tspan class="k">{k1}</tspan>:<tspan class="m">{d1}</tspan> <tspan class="v">{v1}</tspan>'
                       f'<tspan class="m"> | </tspan><tspan class="k">{k2}</tspan>:<tspan class="m">{d2}</tspan> '
                       f'<tspan class="v">{v2}</tspan></text>')
        elif kind == "loc":
            _, net, a, d = ln
            tail = f"{net:,} ( +{a:,}, -{d:,} )"
            out.append(g + f'<tspan class="k">Lines of Code</tspan>:<tspan class="m">{dots("Lines of Code", tail)}</tspan> '
                       f'<tspan class="v">{net:,}</tspan> ( <tspan class="add">+{a:,}</tspan>, '
                       f'<tspan class="del">-{d:,}</tspan> )<tspan class="cur">█</tspan></text>')

    rocket = []
    for i, (cls, row) in enumerate(ROCKET):
        rocket.append(f'<tspan x="22" y="{58 + i * 20}" class="{cls}">{escape(row)}</tspan>')

    height = y0 + len(lines) * lh + 10
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="985" height="{height}" viewBox="0 0 985 {height}" font-family="'JetBrains Mono','Fira Code',Consolas,'Courier New',monospace" font-size="15" role="img" aria-label="Alberto — profile card">
<style>
  text, tspan {{ white-space: pre; }}
  .k {{ fill: {t['key']}; }} .v {{ fill: {t['value']}; }} .m {{ fill: {t['muted']}; }}
  .a {{ fill: {t['accent']}; font-weight: 700; }} .add {{ fill: {t['add']}; }} .del {{ fill: {t['dele']}; }}
  .ok {{ fill: {t['add']}; }}
  .ln {{ fill: {t['text']}; opacity: 0; animation: in .45s ease-out forwards; }}
  .hull {{ fill: {t['hull']}; }} .flame1 {{ fill: {t['flame1']}; }} .flame2 {{ fill: {t['flame2']}; }}
  .flame1, .flame2 {{ animation: flicker .35s steps(2) infinite alternate; }}
  .flame2 {{ animation-delay: .17s; }}
  .rocket {{ animation: hover 3s ease-in-out infinite; }}
  .pulse {{ animation: pulse 1.6s ease-in-out infinite; }}
  .cur {{ fill: {t['accent']}; animation: blink 1s steps(1) infinite; }}
  @keyframes in {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
  @keyframes flicker {{ from {{ opacity: 1; }} to {{ opacity: .35; }} }}
  @keyframes hover {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-7px); }} }}
  @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: .25; }} }}
  @keyframes blink {{ 50% {{ opacity: 0; }} }}
</style>
<rect x="1" y="1" width="983" height="{height - 2}" rx="14" fill="{t['bg']}" stroke="{t['border']}" stroke-width="1.5"/>
<g class="rocket"><text>{''.join(rocket)}</text></g>
{chr(10).join(out)}
</svg>
"""


def main():
    _, data = api("https://api.github.com/graphql", {"query": QUERY, "variables": {"login": USER}})
    if data.get("errors"):
        raise SystemExit(data["errors"])
    lines = build_lines(data["data"])
    os.makedirs(OUT, exist_ok=True)
    for name, theme in THEMES.items():
        with open(os.path.join(OUT, f"card-{name}.svg"), "w", encoding="utf-8") as f:
            f.write(render(lines, theme))
    print("ok")


if __name__ == "__main__":
    main()
