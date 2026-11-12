"""Run user-guide-publish.yaml's front page step against a made-up gh-pages branch, without
publishing. The step and the Python in it come from the workflow file, so this tests what a
caller runs. Needs bash, git and uv, as the workflow's runner has.
"""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = yaml.safe_load((ROOT / ".github/workflows/user-guide-publish.yaml").read_text())
STEPS = WORKFLOW["jobs"]["publish"]["steps"]
STAGE = next(step for step in STEPS if step.get("id") == "stage")["run"]
SCRIPT = STAGE.split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]

GIT_ENV = {
    "GIT_AUTHOR_NAME": "test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
}


def run(*command, cwd, **env):
    return subprocess.run(
        command,
        cwd=cwd,
        env={**os.environ, **GIT_ENV, **env},
        check=True,
        capture_output=True,
        text=True,
    )


def links(index):
    """The front page's links, in order."""
    return [part.split('"', 1)[0] for part in index.read_text().split('href="')[1:]]


class FrontPageScriptTests(unittest.TestCase):
    """The Python alone, as the step runs it: `python - <output dir> <folder>...`."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        (self.dir / "zensical.toml").write_text('[project]\nsite_name = "Made-up <App> & Guide"\n')

    def front_page(self, *folders):
        subprocess.run(
            ["uv", "run", "--no-project", "--python", ">=3.11", "python", "-", "pages", *folders],
            cwd=self.dir,
            input=SCRIPT,
            check=True,
            capture_output=True,
            text=True,
        )
        return self.dir / "pages/index.html"

    def test_lists_releases_newest_first_by_number(self):
        index = self.front_page("v1.2.0", "v1.10.0", "v1.9.3", "v10.0.0", "v2.0.0")
        self.assertEqual(
            links(index), ["latest/", "v10.0.0/", "v2.0.0/", "v1.10.0/", "v1.9.3/", "v1.2.0/"]
        )

    def test_ignores_other_folders_and_repeats(self):
        index = self.front_page(
            "v1.2.3", "latest", "assets", "v1.2", "1.2.3", "v1.2.3-rc.1", "v1.2.3", "xv1.2.3", ""
        )
        self.assertEqual(links(index), ["latest/", "v1.2.3/"])

    def test_no_releases(self):
        index = self.front_page()
        self.assertEqual(links(index), ["latest/"])

    def test_title_is_the_site_name_escaped(self):
        text = self.front_page("v1.0.0").read_text()
        self.assertIn("<title>Made-up &lt;App&gt; &amp; Guide</title>", text)
        self.assertIn("<h1>Made-up &lt;App&gt; &amp; Guide</h1>", text)

    def test_turns_jekyll_off(self):
        self.front_page("v1.0.0")
        self.assertTrue((self.dir / "pages/.nojekyll").is_file())


class StageStepTests(unittest.TestCase):
    """The whole step, in a clone whose origin has a gh-pages branch from earlier releases."""

    def test_stages_the_release_and_lists_the_published_ones(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        origin = Path(tmp.name) / "origin"
        work = Path(tmp.name) / "work"
        origin.mkdir()
        run("git", "init", "-q", "-b", "main", cwd=origin)
        (origin / "zensical.toml").write_text('[project]\nsite_name = "Made-up Guide"\n')
        run("git", "add", ".", cwd=origin)
        run("git", "commit", "-q", "-m", "main", cwd=origin)
        run("git", "checkout", "-q", "--orphan", "gh-pages", cwd=origin)
        run("git", "rm", "-q", "-rf", ".", cwd=origin)
        for folder in ("latest", "v1.2.0", "v1.10.0", "assets"):
            (origin / folder).mkdir()
            (origin / folder / "index.html").write_text(folder)
        (origin / "index.html").write_text("the old front page")
        (origin / "v9.9.9").write_text("a file, not a release's folder")
        run("git", "add", ".", cwd=origin)
        run("git", "commit", "-q", "-m", "pages", cwd=origin)
        run("git", "checkout", "-q", "main", cwd=origin)
        # As actions/checkout leaves it: the default branch only
        run("git", "clone", "-q", "--depth=1", "--branch", "main", origin.as_uri(), str(work), cwd=tmp.name)
        (work / "site").mkdir()
        (work / "site/index.html").write_text("the new release's guide")

        # As GitHub runs a step with no shell given: bash -e
        run("bash", "-e", "-c", STAGE, cwd=work, SEMVERTAG="v1.11.0")

        self.assertEqual(
            (work / "pages/v1.11.0/index.html").read_text(), "the new release's guide"
        )
        self.assertEqual(
            links(work / "pages/index.html"), ["latest/", "v1.11.0/", "v1.10.0/", "v1.2.0/"]
        )
        self.assertIn("<h1>Made-up Guide</h1>", (work / "pages/index.html").read_text())
        # Only what this release adds: the deploy keeps the rest of the branch (clean: false)
        self.assertEqual(
            sorted(p.name for p in (work / "pages").iterdir()),
            [".nojekyll", "index.html", "v1.11.0"],
        )


if __name__ == "__main__":
    unittest.main()
