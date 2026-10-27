import json
import os
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

output = Path("profile-summary-card-output/github_dark")
cards = {
    "1-repos-per-language.svg": "Repositories grouped by primary language",
    "2-most-commit-language.svg": "Commit contributions grouped by repository primary language",
}

for filename in cards:
    path = output / filename
    try:
        root = ElementTree.parse(path).getroot()
    except (OSError, ElementTree.ParseError) as error:
        raise SystemExit(f"Card {path} is missing or invalid: {error}") from error
    if root.tag != "{http://www.w3.org/2000/svg}svg":
        raise SystemExit(f"Card {path} is not an SVG")

username = os.environ["GITHUB_USER"]
token = os.environ["GITHUB_TOKEN"]
base_query = f"author:{username} is:pr is:merged is:public"


def search_count(query):
    params = urlencode({"q": query, "per_page": 1})
    request = Request(
        f"https://api.github.com/search/issues?{params}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "profile-summary-workflow",
        },
    )
    with urlopen(request, timeout=30) as response:
        result = json.load(response)
    if result.get("incomplete_results") is not False or type(result.get("total_count")) is not int:
        raise SystemExit("GitHub returned an incomplete pull request count")
    return result["total_count"]


def search_link(query):
    return "https://github.com/search?" + urlencode({"q": query, "type": "pullrequests"}, quote_via=quote)


all_merged = search_count(base_query)
outside_query = f"{base_query} -user:{username}"
outside_merged = search_count(outside_query)
if outside_merged > all_merged:
    raise SystemExit("Outside-account pull request count exceeds the total")

readme = Path("README.md")
start = "<!-- PROFILE_CARDS:START -->"
end = "<!-- PROFILE_CARDS:END -->"
content = readme.read_text(encoding="utf-8")
if content.count(start) != 1 or content.count(end) != 1 or content.index(start) >= content.index(end):
    raise SystemExit("Profile card markers are missing, duplicated, or out of order")

section = f"""{start}
## GitHub activity

[**{all_merged} merged public pull requests**]({search_link(base_query)}) · [**{outside_merged} in repositories outside my account**]({search_link(outside_query)})

<details>
<summary><b>More GitHub stats</b></summary>

These charts group repositories and commit contributions by each repository's primary language. They are not a measure of proficiency.

<div align="center">
  <img src="{output / '2-most-commit-language.svg'}" alt="{cards['2-most-commit-language.svg']}" />
  <img src="{output / '1-repos-per-language.svg'}" alt="{cards['1-repos-per-language.svg']}" />
</div>
</details>
{end}"""
readme.write_text(content[:content.index(start)] + section + content[content.index(end) + len(end):], encoding="utf-8")

for path in output.iterdir():
    if path.is_file() and path.name not in cards:
        path.unlink()
