# general-workflows
About GitHub action general workflows

| Name                                                                                                                               | Description                                                                 |
|------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| [jlab-deploy-app.yaml](https://github.com/JeffersonLab/general-workflows/blob/main/.github/workflows/jlab-deploy-app.yaml)         | Deploy an app given an app name, environment and version                    |
| [user-guide-build.yaml](https://github.com/JeffersonLab/general-workflows/blob/main/.github/workflows/user-guide-build.yaml)       | Build a Markdown user guide into a website with Zensical, for CI            |
| [user-guide-publish.yaml](https://github.com/JeffersonLab/general-workflows/blob/main/.github/workflows/user-guide-publish.yaml)   | Publish that website to GitHub Pages for a release, with a folder per release |

## User guide website
[Publishing a user guide website](https://github.com/JeffersonLab/general-workflows/blob/main/docs/user-guide/README.md) describes what a repository provides and how it calls the two `user-guide` workflows. That guide is itself a small Zensical website ([zensical.toml](zensical.toml)), which [CI](https://github.com/JeffersonLab/general-workflows/blob/main/.github/workflows/ci.yaml) builds with `user-guide-build.yaml` to try it. The [tests](tests) run `user-guide-publish.yaml`'s front page step against a made-up `gh-pages` branch, without publishing. With [uv](https://docs.astral.sh/uv/getting-started/installation/) installed:
```
uv run --locked zensical build --strict
uv run --locked --with-requirements tests/requirements.txt python -m unittest discover -s tests -v
```

## Release
Callers pin a major version, such as `@v2`. To release, tag `main` with the next [semantic version](https://semver.org/), such as `v2.1.0`, and move the major tag to it:
```
git tag v2.1.0
git tag -f v2
git push origin v2.1.0
git push -f origin v2
```

## See Also
- [Other workflows](https://github.com/search?q=org%3Ajeffersonlab+topic%3Agh-action-workflow&type=repositories)
