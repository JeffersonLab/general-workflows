# Publishing a user guide website

Two reusable workflows turn a repository's Markdown user guide into a website, built with
[Zensical](https://zensical.org) and published to GitHub Pages with a folder for each release:

| Address                                         | Content                                          |
|-------------------------------------------------|--------------------------------------------------|
| `https://<owner>.github.io/<repository>/`        | A front page that links to each release's guide  |
| `https://<owner>.github.io/<repository>/latest/` | The latest release's guide                       |
| `https://<owner>.github.io/<repository>/v1.2.3/` | The guide as it was in release `v1.2.3`          |

- [user-guide-build.yaml](https://github.com/JeffersonLab/general-workflows/blob/main/.github/workflows/user-guide-build.yaml)
  builds the website in CI, and fails on a warning, such as a link to a page or heading that
  doesn't exist.
- [user-guide-publish.yaml](https://github.com/JeffersonLab/general-workflows/blob/main/.github/workflows/user-guide-publish.yaml)
  builds it again for a release and publishes it to the `gh-pages` branch.

## What the repository provides

The workflows hold the steps; the repository holds the guide and pins the tools that build it,
all at its root:

- The guide's Markdown, such as `docs/user-guide`, which stays readable on GitHub. Link within
  the guide by relative path.
- `zensical.toml`: the website's settings. `site_name` is also the front page's title, `docs_dir`
  is the guide's folder, and `site_dir` must be `site`, Zensical's default. Leave `site_url`
  out: each release is published in a folder of its own, so its pages link to each other
  relatively.
- `pyproject.toml` and `uv.lock`: the version of Zensical, pinned for [uv](https://docs.astral.sh/uv/).
  `uv lock` writes `uv.lock`:

    ```toml
    [project]
    name = "myapp-user-guide"
    version = "0.0.0"
    requires-python = ">=3.11"
    dependencies = ["zensical==0.0.69"]

    [tool.uv]
    package = false
    ```

- `.gitignore`: `/site`, `/pages` and `/.venv`, which the build makes.

`uv run --locked zensical build --strict` builds the website into `site/` as the workflows do,
and `uv run --locked zensical serve` previews it at `http://localhost:8000`.

## Build it in CI

```yaml
jobs:
  user-guide:
    uses: jeffersonlab/general-workflows/.github/workflows/user-guide-build.yaml@v2
```

The pull request's check is named `user-guide / build`. The workflow needs no inputs and reads
the repository only (`contents: read`).

## Publish it on release

Call the workflow after the job that makes the release's tag, with the tag as `semvertag`:

```yaml
jobs:
  release:
    permissions:
      contents: write
    uses: jeffersonlab/java-workflows/.github/workflows/gh-release.yaml@v3

  user_guide_publish:
    permissions:
      contents: write
    needs:
      - release
    uses: jeffersonlab/general-workflows/.github/workflows/user-guide-publish.yaml@v2
    with:
      semvertag: ${{ needs.release.outputs.semvertag }}
```

The calling job needs `contents: write`, to push to the `gh-pages` branch. The workflow:

1. Builds the website, with `--strict` as CI does.
2. Replaces `latest/` on `gh-pages` with it, so a page that this release removed goes from
   `latest/` too. The first release creates the branch.
3. Adds the release's folder, named by `semvertag`, and keeps the other releases' folders.
4. Rewrites the front page: a link to `latest/` and one to each folder named like `v1.2.3`,
   newest first. Its title is `zensical.toml`'s `site_name`.

Runs in one repository publish one at a time, in order (the `user-guide-pages` concurrency
group), since each adds to the same branch.

After the first release, turn GitHub Pages on once, in the repository's settings: Pages, "Deploy
from a branch", branch `gh-pages`, folder `/ (root)`.

## Changing the workflows

This guide is also what tries the workflows: this repository's CI builds it with the pull
request's own `user-guide-build.yaml`, and `tests/` runs `user-guide-publish.yaml`'s front page
step against a made-up `gh-pages` branch, without publishing. With uv installed:

```
uv run --locked zensical build --strict
uv run --locked --with-requirements tests/requirements.txt python -m unittest discover -s tests -v
```

Nothing here runs the two steps that push to `gh-pages`: a release of a repository that calls
the workflow is their test.
