#!/usr/bin/env python3
# Copyright (c) 2025-2026 QPerfect. All Rights Reserved.
# Proprietary and confidential.

"""Build the published Qleo wheels, documentation and CUDA-Q backend included.

Usage:
    python scripts/build_wheel.py [--cudaq-payload DIR] [--plat-name TAG]

Differs from a plain `python -m build` in two ways.

**Documentation.** The mkdocs site is built first and staged under
`src/qleo/_docs/`, so setuptools packs it into the wheel and it installs to
`site-packages/qleo/_docs/`. That is where `qleo.docs_dir()` and the
`qleo docs` console command look for it. Building the docs needs `qleo`
importable (mkdocstrings imports the package to autodoc it), which makes this
a two-pass build in a clean environment: install the package first, then run
this script. An existing `public/` is reused rather than rebuilt, so CI can
pass the docs job's artifact straight in.

**Two wheels.** With `--cudaq-payload`, this emits both:

    qleo-X.Y.Z-py3-none-any.whl                        no backend
    qleo-X.Y.Z-py3-none-manylinux_2_28_x86_64.whl      backends included

The CUDA-Q backends (CPU: `libnvqir-qleo.so`, `libexaqt.so`, `qleo.yml`;
GPU: `libnvqir-qleo_gpu.so`, `libexaqt_gpu.so`, `qleo_gpu.yml` — all six
built by the cudaq-integration project) are Linux x86_64 only, so they
cannot go in a `py3-none-any` wheel that macOS and Windows users would
also download. pip prefers the more specific platform tag on Linux
x86_64 and falls back to `any` everywhere else, so each platform gets a
wheel that works. Neither backend needs a CUDA toolkit or a GPU to
*build* — `qleo_gpu`'s engine dlopens CUDA/cuStateVec at first real use —
so this wheel is built the same way regardless of which backends the
build host can actually run.

Without `--cudaq-payload` only the pure wheel and the sdist are built, which
is the right thing for a local build — the payload comes from a CI artifact.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Staged into the package by `stage_cudaq_payload`; must match `_LIBS` and
# `_TARGET_CONFIGS` in src/qleo/cudaq.py, which is what reads them back out.
CUDAQ_FILES = (
    "libnvqir-qleo.so",
    "libexaqt.so",
    "qleo.yml",
    "libnvqir-qleo_gpu.so",
    "libexaqt_gpu.so",
    "qleo_gpu.yml",
)
CUDAQ_STAGE = REPO / "src" / "qleo" / "_cudaq"

# Default platform tag for the wheel carrying the backend. manylinux_2_28 is
# RHEL/Rocky/Alma 8 and up — the same floor CUDA-Q's own wheels claim.
#
# This is a *promise* about the shared libraries inside, not a measurement of
# them. cudaq-integration's build job records their real glibc / libstdc++
# floor in an `abi.env` artifact and its consuming CI job fails if the payload
# needs more than this tag allows; see that project's .gitlab-ci.yml.
DEFAULT_PLAT_NAME = "manylinux_2_28_x86_64"


def run(argv: list[str | Path]) -> None:
    """Run a command, echoing it, and abort the build if it fails."""
    print("    $ " + " ".join(str(a) for a in argv), flush=True)
    subprocess.run([str(a) for a in argv], check=True)


def build_docs(site: Path) -> None:
    """Build the mkdocs site into `site` (mkdocs' configured site_dir)."""
    if (site / "index.html").is_file():
        print(f"[1/5] reusing docs site at {site}/")
        return
    if shutil.which("mkdocs") is None:
        sys.exit(
            f"error: no docs site at {site}/ and mkdocs is not installed.\n"
            "       Install the docs toolchain with `uv sync` (see the dev "
            "dependency group)."
        )
    print("[1/5] mkdocs build")
    run(["mkdocs", "build"])


def stage_package_docs(site: Path) -> None:
    """Copy the docs site into the package, where package-data ships it.

    Emptied first so a rebuild cannot carry stale pages over.
    """
    print("[2/5] staging package data (docs)")
    stage = REPO / "src" / "qleo" / "_docs"
    shutil.rmtree(stage, ignore_errors=True)
    stage.mkdir(parents=True)
    shutil.copytree(site, stage, dirs_exist_ok=True)


def clear_cudaq_stage() -> None:
    """Empty `src/qleo/_cudaq/`, leaving only the tracked `.gitkeep`."""
    CUDAQ_STAGE.mkdir(parents=True, exist_ok=True)
    for path in CUDAQ_STAGE.iterdir():
        if path.name != ".gitkeep":
            path.unlink()
    (CUDAQ_STAGE / ".gitkeep").touch()


def stage_cudaq_payload(payload: Path) -> None:
    """Copy the six backend files (CPU + GPU) into the package."""
    missing = [f for f in CUDAQ_FILES if not (payload / f).is_file()]
    if missing:
        sys.exit(
            f"error: {payload}/ is missing {', '.join(missing)}.\n"
            "       Expected a cudaq-integration build: the six files are "
            f"{', '.join(CUDAQ_FILES)}.\n"
            "       In CI they arrive as the `cudaq:fetch` artifact."
        )
    clear_cudaq_stage()
    for name in CUDAQ_FILES:
        shutil.copy2(payload / name, CUDAQ_STAGE / name)
        print(f"    staged {name}")


def clean_build_dir() -> None:
    """Remove setuptools' `build/` tree.

    Load-bearing, not hygiene. `bdist_wheel` copies sources into `build/lib/`
    and only ever *adds* to it: a file that has disappeared from the source
    tree stays behind. So the payload staged for the platform wheel survives
    in `build/lib/qleo/_cudaq/` and gets packed into the *pure* wheel of the
    next build — shipping a Linux shared library to macOS and Windows users.
    Two consecutive local builds are enough to hit it, as is any CI runner
    with a cached working directory.
    """
    shutil.rmtree(REPO / "build", ignore_errors=True)


def build_pure(out: Path) -> None:
    """Build the sdist and the pure `py3-none-any` wheel.

    Must run before the payload is staged. `build` with both targets builds
    the sdist first and then the wheel *from the unpacked sdist*, so a payload
    already on disk would end up in the sdist too.
    """
    print("[3/5] python -m build (sdist + pure wheel)")
    shutil.rmtree(out, ignore_errors=True)
    clear_cudaq_stage()
    clean_build_dir()
    run([sys.executable, "-m", "build", "--sdist", "--wheel", "-o", out])


def build_platform(out: Path, payload: Path, plat_name: str) -> None:
    """Build the platform wheel carrying the CUDA-Q backend."""
    print(f"[4/5] python -m build --wheel (plat-name {plat_name})")
    stage_cudaq_payload(payload)
    clean_build_dir()
    # `--plat-name` on an otherwise pure project yields exactly
    # `py3-none-<plat>`: the interpreter tag stays `py3` and
    # `Root-Is-Purelib` stays true, so the payload installs to purelib next to
    # the rest of `qleo` — which is where `qleo/cudaq.py` looks for it.
    #
    # Passed through `build` as a `bdist_wheel` argument. If a future
    # setuptools drops `--build-option`, the equivalent is a retag pass with
    # `wheel tags --platform-tag <plat>` (wheel >= 0.42) over a second build.
    run(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "-o",
            out,
            f"-C--build-option=--plat-name={plat_name}",
        ]
    )


def verify(out: Path, plat_name: str, expect_payload: bool) -> None:
    """Check each wheel carries exactly the payload it should.

    The whole point of two wheels is that one has the backend and the other
    does not. Getting that backwards ships a Linux `.so` to macOS users, or a
    Linux wheel whose `qleo cudaq install` has nothing to install — neither of
    which any other check would catch.
    """
    print("[5/5] verifying wheel contents")
    payload_members = {f"qleo/_cudaq/{name}" for name in CUDAQ_FILES}
    wheels = sorted(out.glob("*.whl"))
    if not wheels:
        sys.exit(f"error: no wheels in {out}/")

    seen_pure = seen_plat = False
    for wheel in wheels:
        with zipfile.ZipFile(wheel) as zf:
            names = set(zf.namelist())
        found = sorted(names & payload_members)
        if plat_name in wheel.name:
            seen_plat = True
            if set(found) != payload_members:
                sys.exit(
                    f"error: {wheel.name} should carry the backend but has "
                    f"{found or 'none of it'}"
                )
        else:
            seen_pure = True
            if found:
                sys.exit(
                    f"error: {wheel.name} is the pure wheel but carries {found}"
                )
        print(f"    {wheel.name}: {len(found)} payload file(s)")

    if not seen_pure:
        sys.exit("error: no pure py3-none-any wheel was built")
    if expect_payload and not seen_plat:
        sys.exit(f"error: no {plat_name} wheel was built")

    # An sdist must never carry the payload either: it is a build input, not
    # source, and a source build on another platform would pick it up.
    for sdist in out.glob("*.tar.gz"):
        import tarfile

        with tarfile.open(sdist) as tf:
            bad = [n for n in tf.getnames() if "/_cudaq/" in n and not n.endswith(".gitkeep")]
        if bad:
            sys.exit(f"error: {sdist.name} carries {bad}")
        print(f"    {sdist.name}: clean")


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="build_wheel.py",
        description="Build the published Qleo wheels.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--cudaq-payload",
        metavar="DIR",
        type=Path,
        help=(
            "Directory holding the cudaq-integration build "
            f"({', '.join(CUDAQ_FILES)}). Omit to build only the pure wheel "
            "and the sdist."
        ),
    )
    parser.add_argument(
        "--plat-name",
        default=DEFAULT_PLAT_NAME,
        help=f"Platform tag for the payload wheel (default: {DEFAULT_PLAT_NAME}).",
    )
    args = parser.parse_args()

    # A typo here would produce a wheel pip silently ignores rather than an
    # error, so refuse anything that is not a Linux platform tag.
    if not args.plat_name.startswith(("manylinux", "linux_", "musllinux")):
        parser.error(
            f"--plat-name {args.plat_name!r} is not a Linux platform tag; the "
            "CUDA-Q backend is Linux x86_64 only"
        )

    out = REPO / "dist"
    site = REPO / "public"  # mkdocs site_dir (mkdocs.yml)

    build_docs(site)
    stage_package_docs(site)
    build_pure(out)
    if args.cudaq_payload:
        build_platform(out, args.cudaq_payload, args.plat_name)
    else:
        print("[4/5] no --cudaq-payload given; skipping the platform wheel")
    verify(out, args.plat_name, expect_payload=bool(args.cudaq_payload))

    # Leave the tree as we found it: a staged payload would otherwise leak
    # into the next local build, and `git status` would show a dirty package.
    clear_cudaq_stage()

    print("artefacts in dist:")
    for f in sorted(out.iterdir()):
        print(f"    {f.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
