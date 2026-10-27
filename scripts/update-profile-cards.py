from pathlib import Path
from xml.etree import ElementTree

output = Path("profile-summary-card-output/github_dark")
cards = {
    "0-profile-details.svg": "GitHub contribution history",
    "1-repos-per-language.svg": "Repositories by primary language",
    "3-stats.svg": "GitHub statistics",
}

for filename in cards:
    path = output / filename
    try:
        root = ElementTree.parse(path).getroot()
    except (OSError, ElementTree.ParseError) as error:
        raise SystemExit(f"Card {path} is missing or invalid: {error}") from error
    if root.tag != "{http://www.w3.org/2000/svg}svg":
        raise SystemExit(f"Card {path} is not an SVG")

readme = Path("README.md")
start = "<!-- PROFILE_CARDS:START -->"
end = "<!-- PROFILE_CARDS:END -->"
content = readme.read_text(encoding="utf-8")
if content.count(start) != 1 or content.count(end) != 1 or content.index(start) >= content.index(end):
    raise SystemExit("Profile card markers are missing, duplicated, or out of order")

section = f"{start}\n## GitHub activity\n\n<div align=\"center\">\n"
section += f'  <img src="{output / "0-profile-details.svg"}" alt="{cards["0-profile-details.svg"]}" />\n'
section += f'  <img src="{output / "1-repos-per-language.svg"}" alt="{cards["1-repos-per-language.svg"]}" />\n'
section += f'  <img src="{output / "3-stats.svg"}" alt="{cards["3-stats.svg"]}" />\n'
section += f"</div>\n{end}"
readme.write_text(content[:content.index(start)] + section + content[content.index(end) + len(end):], encoding="utf-8")

for path in output.iterdir():
    if path.is_file() and path.name not in cards:
        path.unlink()
