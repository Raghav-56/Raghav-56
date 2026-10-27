import json
import os
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

username = os.environ["GITHUB_USER"]
token = os.environ["GITHUB_TOKEN"]
headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {token}",
    "User-Agent": "profile-trophy-workflow",
}


def get_json(path, params):
    url = f"https://api.github.com{path}?{urlencode(params)}"
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        return json.load(response)


def merged_count(query):
    result = get_json("/search/issues", {"q": query, "per_page": 1})
    if result.get("incomplete_results") is not False or type(result.get("total_count")) is not int:
        raise SystemExit("GitHub returned an incomplete pull request count")
    return result["total_count"]


repos = []
page = 1
while True:
    batch = get_json(f"/users/{quote(username, safe='')}/repos", {"type": "owner", "per_page": 100, "page": page})
    if not isinstance(batch, list):
        raise SystemExit("GitHub did not return a repository list")
    repos.extend(repo for repo in batch if repo.get("private") is False and repo.get("fork") is False)
    if len(batch) < 100:
        break
    page += 1

query = f"author:{username} is:pr is:merged is:public"
merged = merged_count(query)
outside = merged_count(f"{query} -user:{username}")
if outside > merged:
    raise SystemExit("Outside-account pull request count exceeds the total")
stars = sum(repo["stargazers_count"] for repo in repos)

badges = [
    ("Merged pull requests", "Public repositories", merged, "#e3b341"),
    ("Community contributions", "Merged outside my account", outside, "#bc8cff"),
    ("Original repositories", "Public, excluding forks", len(repos), "#58a6ff"),
    ("Stars received", "On original public repositories", stars, "#3fb950"),
]

panels = []
for index, (title, subtitle, value, color) in enumerate(badges):
    x = 12 + (index % 2) * 346
    y = 12 + (index // 2) * 130
    panels.append(f'''<g transform="translate({x},{y})">
  <rect width="332" height="116" rx="8" fill="#161b22" stroke="#30363d"/>
  <circle cx="48" cy="54" r="28" fill="{color}" fill-opacity=".13" stroke="{color}"/>
  <path d="M38 39h20v10c0 8-4 13-10 13s-10-5-10-13V39zm0 4h-6v3c0 7 3 10 8 10m18-13h6v3c0 7-3 10-8 10M48 62v7m-8 2h16" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
  <text x="88" y="34" fill="#e6edf3" font-size="15" font-weight="600">{title}</text>
  <text x="88" y="66" fill="{color}" font-size="27" font-weight="700">{value}</text>
  <text x="88" y="90" fill="#8b949e" font-size="12">{subtitle}</text>
</g>''')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="704" height="272" viewBox="0 0 704 272" role="img" aria-labelledby="title description">
<title id="title">GitHub trophy board</title>
<desc id="description">Public GitHub counts for merged pull requests, outside-account contributions, original repositories and stars.</desc>
<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">
{''.join(panels)}
</g>
</svg>
'''
output = Path("assets/github-trophies.svg")
output.write_text(svg, encoding="utf-8")
