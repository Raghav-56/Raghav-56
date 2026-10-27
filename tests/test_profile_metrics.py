import io
import json
import os
import runpy
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse
from xml.etree import ElementTree

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/generate-trophies.py"


class ProfileMetricsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.previous_dir = Path.cwd()
        self.addCleanup(os.chdir, self.previous_dir)
        os.chdir(self.temp.name)
        Path("assets").mkdir()
        self.environment = patch.dict(os.environ, {"GITHUB_USER": "example", "GITHUB_TOKEN": "test-token"})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def response(self, request, timeout):
        parsed = urlparse(request.full_url)
        query = parse_qs(parsed.query)
        if parsed.path == "/users/example":
            data = {"created_at": "2023-08-13T14:33:25Z"}
        elif parsed.path.endswith("/repos"):
            data = [
                {"private": False, "fork": False, "archived": False, "language": "Python", "stargazers_count": 3, "pushed_at": None, "created_at": "2024-03-01T00:00:00Z"},
                {"private": False, "fork": True, "archived": False, "language": "Rust", "stargazers_count": 9, "pushed_at": None},
                {"private": True, "fork": False, "archived": False, "language": "Go", "stargazers_count": 100, "pushed_at": None},
            ]
        elif "reviewed-by:" in query["q"][0]:
            data = {"incomplete_results": False, "total_count": 4}
        elif "is:issue" in query["q"][0]:
            data = {"incomplete_results": False, "total_count": 2}
        else:
            prs = [
                {"repository_url": "https://api.github.com/repos/other/project", "created_at": "2024-01-01T00:00:00Z", "pull_request": {"merged_at": "2024-01-03T00:00:00Z"}},
                {"repository_url": "https://api.github.com/repos/example/project", "created_at": "2024-01-01T00:00:00Z", "pull_request": {"merged_at": "2024-01-01T01:00:00Z"}},
                {"repository_url": "https://api.github.com/repos/other/project", "created_at": "2024-01-01T00:00:00Z", "pull_request": {"merged_at": None}},
            ]
            data = {"incomplete_results": False, "total_count": len(prs), "items": prs}
        return io.BytesIO(json.dumps(data).encode())

    def test_public_metrics_and_outside_merge_time(self):
        with patch("urllib.request.urlopen", side_effect=self.response):
            runpy.run_path(str(SCRIPT))
        board = ElementTree.parse("assets/github-trophies.svg").getroot().attrib["aria-label"]
        collaboration = projects = timeline = board
        self.assertIn("Merged pull requests: 2", collaboration)
        self.assertIn("Merged outside my account: 1", collaboration)
        self.assertIn("Outside repositories reached: 1", collaboration)
        self.assertIn("Pull requests reviewed: 4", collaboration)
        self.assertIn("Original repositories: 1", projects)
        self.assertIn("Forked repositories: 1", projects)
        self.assertIn("Stars on original repositories: 3", projects)
        self.assertIn("outside my account: 2.0 days", timeline)
        self.assertIn("Joined GitHub Aug 2023", board)
        if datetime.now(timezone.utc).year <= 2029:
            self.assertIn("2024: 1 public original repositories created, 2 public pull requests merged", board)
        root = ElementTree.parse("assets/github-trophies.svg").getroot()
        views = {view.get("id"): view.get("viewBox") for view in root.findall("{http://www.w3.org/2000/svg}view")}
        self.assertEqual(views["desktop"], "0 0 688 614")
        self.assertEqual(views["phone"], "700 0 340 1236")

    def test_incomplete_search_does_not_write_cards(self):
        def response(request, timeout):
            path = urlparse(request.full_url).path
            if path.endswith("/repos") or path == "/users/example":
                return self.response(request, timeout)
            return io.BytesIO(b'{"incomplete_results": true, "total_count": 10}')

        with patch("urllib.request.urlopen", side_effect=response):
            with self.assertRaises(SystemExit):
                runpy.run_path(str(SCRIPT))
        self.assertEqual(list(Path("assets").iterdir()), [])


if __name__ == "__main__":
    unittest.main()
