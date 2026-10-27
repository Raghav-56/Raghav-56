import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from statistics import median
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

username = os.environ["GITHUB_USER"]
token = os.environ["GITHUB_TOKEN"]
headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {token}",
    "User-Agent": "profile-metrics-workflow",
}


def get_json(path, params):
    url = f"https://api.github.com{path}?{urlencode(params)}"
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        return json.load(response)


def search(query, *, items=False):
    page = 1
    results = []
    while True:
        response = get_json("/search/issues", {"q": query, "per_page": 100 if items else 1, "page": page})
        total = response.get("total_count")
        if response.get("incomplete_results") is not False or type(total) is not int:
            raise SystemExit("GitHub returned an incomplete search result")
        if not items:
            return total
        if total > 1000:
            raise SystemExit("GitHub Search cannot return more than 1,000 results for this metric")
        batch = response.get("items")
        if not isinstance(batch, list):
            raise SystemExit("GitHub did not return search items")
        results.extend(batch)
        if len(results) >= total:
            return results
        if not batch:
            raise SystemExit("GitHub returned an incomplete search page")
        page += 1


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def svg_card(title, subtitle, rows, description):
    lines = []
    for index, (label, value) in enumerate(rows):
        y = 95 + index * 39
        lines.append(f'''<text x="24" y="{y}" fill="#58a6ff" font-size="21" font-weight="700">{escape(str(value))}</text>
<text x="78" y="{y}" fill="#c9d1d9" font-size="13">{escape(label)}</text>''')
    height = 108 + (len(rows) - 1) * 39
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="340" height="{height}" viewBox="0 0 340 {height}" role="img" aria-label="{escape(description, quote=True)}">
<rect x="1" y="1" width="338" height="{height - 2}" rx="9" fill="#0d1117" stroke="#30363d"/>
<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">
<text x="24" y="31" fill="#e6edf3" font-size="18" font-weight="600">{escape(title)}</text>
<text x="24" y="53" fill="#8b949e" font-size="12">{escape(subtitle)}</text>
{''.join(lines)}
</g></svg>\n'''


def timeline_card(months, counts, median_duration):
    peak = max(counts, default=0)
    bar_height = 74
    bars = []
    for i, (month, count) in enumerate(zip(months, counts)):
        x = 18 + i * 26
        height = round(bar_height * count / peak) if peak else 0
        bars.append(f'''<rect x="{x}" y="{147 - height}" width="17" height="{height}" rx="2" fill="#58a6ff"/>
<text x="{x + 8.5}" y="165" fill="#8b949e" font-size="9" text-anchor="middle">{month:%b}</text>''')
    description = ", ".join(f"{month:%b %Y}: {count}" for month, count in zip(months, counts))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="340" height="220" viewBox="0 0 340 220" role="img" aria-label="{escape('Merged public pull requests by month. ' + description + '. Median open-to-merge time outside my account: ' + median_duration, quote=True)}">
<rect x="1" y="1" width="338" height="218" rx="9" fill="#0d1117" stroke="#30363d"/>
<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">
<text x="24" y="31" fill="#e6edf3" font-size="18" font-weight="600">Merge timeline</text>
<text x="24" y="53" fill="#8b949e" font-size="12">Public PRs per month · current month is partial</text>
<path d="M18 148H330" stroke="#30363d"/>
{''.join(bars)}
<text x="24" y="194" fill="#c9d1d9" font-size="12">Median open-to-merge outside account: {escape(median_duration)}</text>
</g></svg>\n'''


repos = []
page = 1
while True:
    batch = get_json(f"/users/{quote(username, safe='')}/repos", {"type": "owner", "per_page": 100, "page": page})
    if not isinstance(batch, list):
        raise SystemExit("GitHub did not return a repository list")
    repos.extend(repo for repo in batch if repo.get("private") is False)
    if len(batch) < 100:
        break
    page += 1

prs = search(f"author:{username} is:pr is:public", items=True)
merged = [pr for pr in prs if pr["pull_request"]["merged_at"]]
outside = [pr for pr in merged if pr["repository_url"].rstrip("/").split("/")[-2].lower() != username.lower()]
outside_repos = {pr["repository_url"].lower() for pr in outside}
outside_owners = {url.rstrip("/").split("/")[-2] for url in outside_repos}
issues = search(f"author:{username} is:issue is:public -user:{username}")
reviewed = search(f"reviewed-by:{username} is:pr is:public")
original = [repo for repo in repos if repo.get("fork") is False]
forks = [repo for repo in repos if repo.get("fork") is True]
now = datetime.now(timezone.utc)
recent = sum(1 for repo in original if repo.get("pushed_at") and parse_time(repo["pushed_at"]) >= now - timedelta(days=90))
archived = sum(1 for repo in original if repo.get("archived"))
primary_languages = {repo["language"] for repo in original if repo.get("language")}
stars = sum(repo["stargazers_count"] for repo in original)

collaboration = [
    ("Merged pull requests", len(merged)),
    ("Merged outside my account", len(outside)),
    ("Outside repositories reached", len(outside_repos)),
    ("Outside repository owners", len(outside_owners)),
    ("Issues opened outside my account", issues),
    ("Pull requests reviewed", reviewed),
]
projects = [
    ("Original repositories", len(original)),
    ("Forked repositories", len(forks)),
    ("Original repos pushed in 90 days", recent),
    ("Archived original repositories", archived),
    ("Primary languages in originals", len(primary_languages)),
    ("Stars on original repositories", stars),
]
months = []
for offset in reversed(range(12)):
    index = now.year * 12 + now.month - 1 - offset
    months.append(datetime(index // 12, index % 12 + 1, 1, tzinfo=timezone.utc))
merged_months = Counter(parse_time(pr["pull_request"]["merged_at"]).strftime("%Y-%m") for pr in merged)
counts = [merged_months[month.strftime("%Y-%m")] for month in months]
durations = [(parse_time(pr["pull_request"]["merged_at"]) - parse_time(pr["created_at"])).total_seconds() for pr in outside]
if any(duration < 0 for duration in durations):
    raise SystemExit("A pull request has a merge date before its creation date")
if durations:
    hours = median(durations) / 3600
    duration_label = f"{hours:.1f} hours" if hours < 48 else f"{hours / 24:.1f} days"
else:
    duration_label = "not available"

cards = [
    svg_card("Collaboration", "Public GitHub activity · all time", collaboration, "; ".join(f"{label}: {value}" for label, value in collaboration)),
    svg_card("Repository details", "Public repositories owned by this account", projects, "; ".join(f"{label}: {value}" for label, value in projects)),
    timeline_card(months, counts, duration_label),
]
ElementTree.register_namespace("", "http://www.w3.org/2000/svg")
children = [ElementTree.fromstring(card) for card in cards]
height = sum(int(child.get("height")) for child in children) + 16
board = ElementTree.Element("{http://www.w3.org/2000/svg}svg", {
    "width": "340", "height": str(height), "viewBox": f"0 0 340 {height}",
    "role": "img", "aria-label": "; ".join(child.get("aria-label", "") for child in children),
})
y = 0
for child in children:
    child.set("x", "0")
    child.set("y", str(y))
    board.append(child)
    y += int(child.get("height")) + 8
ElementTree.ElementTree(board).write("assets/github-trophies.svg", encoding="unicode", xml_declaration=False)
