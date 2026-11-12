# Releasing Qleo

Maintainer notes. Users do not need any of this — see the
[README](README.md) to install, and [CONTRIBUTING](CONTRIBUTING.md) to
contribute.

Qleo is a branding layer, so a release is mostly a matter of pointing at the
right versions of two upstreams and letting CI assemble them:

```
exaqt-rs  ──► cudaq-integration ──► (CUDA-Q backends, 6 files) ┐
                                                               ├──► qleo wheels
exaqt-python (mimiq-exaqt, GitLab PyPI registry) ──────────────┘
```

## What CI does, and when

| Event | Jobs |
|---|---|
| Merge request to `main`/`devel` | `test`, `docs:site` |
| Push to `main`/`devel` | `test`, `docs:site` |
| Tag `vX.Y.Z` | `test`, `docs:site`, `cudaq:fetch`, `wheel`, `publish:registry` |
| Push to `main` | `pages` |

Merge requests and branch pushes run checks only. All release work is
tag-only, and `publish:registry` waits on `test` transitively through
`wheel`, so **a failing test stops the upload** rather than following it.

Two wheels are published per release:

```
qleo-X.Y.Z-py3-none-any.whl                    every platform, no CUDA-Q backend
qleo-X.Y.Z-py3-none-manylinux_2_NN_x86_64.whl  Linux x86-64, backend bundled
```

pip prefers the platform wheel on Linux x86-64 and falls back to `any`
everywhere else, so macOS and Windows are unaffected by the Linux-only
backend. `NN` is measured from the payload's real glibc floor by
`cudaq:fetch`, never declared — see `QLEO_PLAT_TAG_POLICY` in
`.gitlab-ci.yml`.

## Prerequisites (one-time)

1. **Job token allowlists.** In each of these projects, add
   `development/qleo/qleo-private` under *Settings → CI/CD → Job token
   permissions*:
   - `development/qleo/cudaq-integration` — so `cudaq:fetch` can download the
     backend
   - `development/exaqt/exaqt-python` — so jobs can install `mimiq-exaqt`
     from its package registry

   Without these, requests return **404, not 403** (GitLab hides existence),
   so a missing allowlist looks like a missing file.

2. **Protected tags.** *Settings → Repository → Protected tags* → protect
   `v*`, so only maintainers can trigger a publish.

3. `RELEASE_TOKEN` must be valid in `cudaq-integration` (its release job uses
   it; nothing in this project needs a stored secret).

## Releasing

### 1. Release the CUDA-Q backend first, if it changed

`qleo` bundles a *tagged* backend build, so the tag has to exist before the
qleo pipeline can fetch it.

```sh
cd cudaq-integration
# Bump all three hand-written copies of the version together; check:version
# fails the pipeline if they disagree, or if the tag does not match them.
#   CMakeLists.txt   project(qleo_cudaq VERSION X.Y.Z ...)
#   pyproject.toml   version = "X.Y.Z"
#   python/qleo_cudaq/__init__.py   __version__ = "X.Y.Z"
git commit -am "chore(version): vX.Y.Z"
git push origin devel            # runs check:version, build, test
git tag vX.Y.Z && git push origin vX.Y.Z
```

The tag pipeline runs `check:version → build → test → release`. `release`
publishes the assets to the generic package registry under
`release-assets/vX.Y.Z/`, which is where this project fetches them from.

Then point Qleo at it — `CUDAQ_INTEGRATION_REF` in `.gitlab-ci.yml`:

```yaml
CUDAQ_INTEGRATION_REF: "vX.Y.Z"
```

This is a deliberate manual bump. Nothing tells Qleo that a new backend
exists, and that is the point: a release ships a frozen artefact, not
whatever `devel` last built.

### 2. Release Qleo

```sh
cd qleo-private
# Update the version and the changelog.
#   pyproject.toml   version = "X.Y.Z"
#   CHANGELOG.md     turn "pending release" into the version and date
git commit -am "chore(version): vX.Y.Z"
git push origin devel            # runs test + docs:site
```

Wait for that pipeline to be green, then:

```sh
git tag vX.Y.Z && git push origin vX.Y.Z
```

### 3. Check the result

```sh
glab ci status --live                                    # watch the pipeline
glab api --hostname gitlab.qperfect.io "projects/20/packages"
```

Or in the web UI:
<https://gitlab.qperfect.io/development/qleo/qleo-private/-/packages>
(**Deploy → Package Registry**). Both wheels and the sdist should appear
under one `qleo` / `X.Y.Z` entry; clicking it lists the individual files and
shows the `pip install` command with the right index URL.

Project ids, for the API and index URLs: **20** `qleo-private`,
**19** `cudaq-integration`, **102** `exaqt-python`.

Confirm pip resolves the right wheel per platform:

```sh
pip download --no-deps -d /tmp/dl \
  --index-url "https://gitlab-ci-token:<token>@gitlab.qperfect.io/api/v4/projects/20/packages/pypi/simple" \
  "qleo==X.Y.Z"
ls /tmp/dl    # manylinux wheel on Linux x86-64, py3-none-any elsewhere
```

## Validating pipeline changes without pushing

`.gitlab-ci.yml` is validated server-side, including `!reference`,
`extends` and anchors — which local YAML parsers do **not** check:

```sh
python3 -c "import json;print(json.dumps({'content':open('.gitlab-ci.yml').read()}))" > /tmp/lint.json
glab api --hostname gitlab.qperfect.io -X POST \
  "projects/development%2Fqleo%2Fqleo-private/ci/lint" \
  --input /tmp/lint.json -H "Content-Type: application/json"
```

Worth running before every CI change. It catches things PyYAML accepts
silently — notably a plain scalar containing `": "`, which YAML turns into a
map instead of a shell command.

## Public PyPI

Deliberately off. `PUBLISH_PYPI` defaults to `"false"` and the tag pipeline
publishes to the GitLab registry only. To publish publicly, set
`PUBLISH_PYPI="true"` **and** a `PYPI_API_TOKEN` CI/CD variable; the job
fails loudly rather than skipping if the flag is on without the token.

A PyPI name-and-version pair can never be reused, so treat this as a
one-way door and check the wheels from a registry release first.

## Building the wheels locally

```sh
uv venv && uv sync && uv pip install -e .
python scripts/build_wheel.py                      # pure wheel + sdist only
python scripts/build_wheel.py --cudaq-payload DIR  # + the platform wheel
```

`DIR` holds the six files of a cudaq-integration build: `libnvqir-qleo.so`,
`libexaqt.so`, `qleo.yml` and their `qleo_gpu` counterparts. The script refuses to finish unless the payload
landed in the platform wheel and nowhere else — not in the `any` wheel, not
in the sdist — and it restores the tree afterwards, so a local build leaves
no staged payload behind.
