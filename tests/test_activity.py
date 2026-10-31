import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("activity", Path(__file__).parents[1] / "scripts/update-activity.py")
activity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(activity)


def event(repo, kind, payload, date="2026-10-28T10:58:26Z"):
    return {"repo": {"name": repo}, "type": kind, "payload": payload, "created_at": date}


class ActivityTests(unittest.TestCase):
    def test_groups_repositories_and_skips_profile_and_merge_noise(self):
        events = [
            event("Raghav-56/Raghav-56", "PushEvent", {"head": "profile"}),
            event("user/one", "PushEvent", {"head": "merge"}),
            event("user/one", "PushEvent", {"head": "real"}),
            event("user/one", "PushEvent", {"head": "duplicate"}),
            event("user/two", "PullRequestEvent", {"action": "merged", "number": 42}),
            event("user/three", "WatchEvent", {}),
        ]
        replies = {
            "/repos/user/one/commits/merge": {"commit": {"message": "Merge upstream v1"}},
            "/repos/user/one/commits/real": {"commit": {"message": "Fix [rendering]\nDetails"}},
            "/repos/user/two/pulls/42": {"title": "Improve checks"},
        }
        self.assertEqual(activity.render(events, replies.__getitem__), "\n".join([
            r"- **[user/one](https://github.com/user/one)** · Pushed [Fix \[rendering\]](https://github.com/user/one/commit/real) · Oct 28, 2026",
            "- **[user/two](https://github.com/user/two)** · Merged [Improve checks](https://github.com/user/two/pull/42) · Oct 28, 2026",
        ]))

    def test_empty_activity(self):
        self.assertEqual(activity.render([], lambda _: None), "No recent public GitHub activity to show.")

    def test_fetch_failure_does_not_render_partial_output(self):
        events = [event("user/repo", "PushEvent", {"head": "x"})]
        def fail(_):
            raise OSError("API failed")
        with self.assertRaises(OSError):
            activity.render(events, fail)


if __name__ == "__main__":
    unittest.main()
