import io
import json
import os
import runpy
import tempfile
import unittest
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
        if parsed.path.endswith("/repos"):
            data = [
                {"private": False, "fork": False, "archived": False, "language": "Python", "stargazers_count": 3, "pushed_at": None},
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

    def test_incomplete_search_does_not_write_cards(self):
        def response(request, timeout):
            if urlparse(request.full_url).path.endswith("/repos"):
                return self.response(request, timeout)
            return io.BytesIO(b'{"incomplete_results": true, "total_count": 10}')

        with patch("urllib.request.urlopen", side_effect=response):
            with self.assertRaises(SystemExit):
                runpy.run_path(str(SCRIPT))
        self.assertEqual(list(Path("assets").iterdir()), [])


if __name__ == "__main__":
    unittest.main()
