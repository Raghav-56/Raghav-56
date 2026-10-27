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
from copy import deepcopy

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
        if count:
            bars.append(f'<text x="{x + 8.5}" y="{143 - height}" fill="#c9d1d9" font-size="9" text-anchor="middle">{count}</text>')
    description = ", ".join(f"{month:%b %Y}: {count}" for month, count in zip(months, counts))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="340" height="303" viewBox="0 0 340 303" role="img" aria-label="{escape('Merged public pull requests by month. ' + description + '. Median open-to-merge time outside my account: ' + median_duration, quote=True)}">
<rect x="1" y="1" width="338" height="301" rx="9" fill="#0d1117" stroke="#30363d"/>
<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">
<text x="24" y="31" fill="#e6edf3" font-size="18" font-weight="600">Merge timeline</text>
<text x="24" y="53" fill="#8b949e" font-size="12">Public PRs per month · current month is partial</text>
<path d="M18 148H330" stroke="#30363d"/>
{''.join(bars)}
<text x="24" y="194" fill="#c9d1d9" font-size="12">Median open-to-merge outside account: {escape(median_duration)}</text>
</g></svg>\n'''


def history_card(joined, years, repo_counts, merge_counts):
    peak = max(repo_counts + merge_counts + [1])
    bars = []
    spacing = 300 / max(len(years), 1)
    for i, (year, repos_created, prs_merged) in enumerate(zip(years, repo_counts, merge_counts)):
        x = 24 + i * spacing
        for delta, count, color in [(0, repos_created, "#58a6ff"), (12, prs_merged, "#bc8cff")]:
            height = round(count / peak * 92)
            bars.append(f'<rect x="{x + delta:.1f}" y="{227 - height}" width="10" height="{height}" rx="2" fill="{color}"/>')
            if count:
                bars.append(f'<text x="{x + delta + 5:.1f}" y="{223 - height}" fill="#c9d1d9" font-size="9" text-anchor="middle">{count}</text>')
        bars.append(f'<text x="{x + 11:.1f}" y="246" fill="#8b949e" font-size="10" text-anchor="middle">{year}</text>')
    description = "; ".join(f"{year}: {repos_created} public original repositories created, {prs_merged} public pull requests merged" for year, repos_created, prs_merged in zip(years, repo_counts, merge_counts))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="340" height="303" viewBox="0 0 340 303" role="img" aria-label="{escape('Joined GitHub ' + joined + '; ' + description, quote=True)}">
<rect x="1" y="1" width="338" height="301" rx="9" fill="#0d1117" stroke="#30363d"/>
<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">
<text x="24" y="31" fill="#e6edf3" font-size="18" font-weight="600">GitHub history</text>
<text x="24" y="53" fill="#8b949e" font-size="12">Joined {escape(joined)} · public work by year</text>
<rect x="24" y="72" width="9" height="9" fill="#58a6ff"/><text x="39" y="81" fill="#c9d1d9" font-size="11">Original repos created</text>
<rect x="186" y="72" width="9" height="9" fill="#bc8cff"/><text x="201" y="81" fill="#c9d1d9" font-size="11">PRs merged</text>
<path d="M24 228H320" stroke="#30363d"/>
{''.join(bars)}
<text x="24" y="276" fill="#8b949e" font-size="11">Current public repos only · up to six years</text>
</g></svg>\n'''


profile = get_json(f"/users/{quote(username, safe='')}", {})
joined = parse_time(profile["created_at"])
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

years = list(range(max(joined.year, now.year - 5), now.year + 1))
repo_years = Counter(parse_time(repo["created_at"]).year for repo in original)
merge_years = Counter(parse_time(pr["pull_request"]["merged_at"]).year for pr in merged)
repo_counts = [repo_years[year] for year in years]
merge_counts = [merge_years[year] for year in years]

cards = [
    svg_card("Collaboration", "Public GitHub activity · all time", collaboration, "; ".join(f"{label}: {value}" for label, value in collaboration)),
    svg_card("Repository details", "Public repositories owned by this account", projects, "; ".join(f"{label}: {value}" for label, value in projects)),
    history_card(joined.strftime("%b %Y"), years, repo_counts, merge_counts),
    timeline_card(months, counts, duration_label),
]
ElementTree.register_namespace("", "http://www.w3.org/2000/svg")
children = [ElementTree.fromstring(card) for card in cards]
card_height = 303
gap = 8
desktop_width, desktop_height = 688, 2 * card_height + gap
mobile_x, mobile_width, mobile_height = 700, 340, len(children) * card_height + (len(children) - 1) * gap
board = ElementTree.Element("{http://www.w3.org/2000/svg}svg", {
    "viewBox": f"0 0 {desktop_width} {desktop_height}",
    "role": "img", "aria-label": "; ".join(child.get("aria-label", "") for child in children),
})
ElementTree.SubElement(board, "{http://www.w3.org/2000/svg}view", {"id": "desktop", "viewBox": f"0 0 {desktop_width} {desktop_height}"})
ElementTree.SubElement(board, "{http://www.w3.org/2000/svg}view", {"id": "phone", "viewBox": f"{mobile_x} 0 {mobile_width} {mobile_height}"})
for i, child in enumerate(children):
    desktop = deepcopy(child)
    desktop.set("x", str((i % 2) * (340 + gap)))
    desktop.set("y", str((i // 2) * (card_height + gap)))
    board.append(desktop)
    phone = deepcopy(child)
    phone.set("x", str(mobile_x))
    phone.set("y", str(i * (card_height + gap)))
    board.append(phone)
ElementTree.ElementTree(board).write("assets/github-trophies.svg", encoding="unicode", xml_declaration=False)
