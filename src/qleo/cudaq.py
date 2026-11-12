# Copyright (c) 2025-2026 QPerfect. All Rights Reserved.
# Proprietary and confidential.

"""Copy the Qleo NVQIR backend(s) into the active CUDA-Q installation.

CUDA-Q discovers simulators by name inside its own install tree, with no
search path to extend, so enabling a third-party backend means putting
files there:

    <install>/lib/libnvqir-qleo.so       the CPU backend
    <install>/lib/libexaqt.so            the CPU engine it links
    <install>/targets/qleo.yml           the CPU target config
    <install>/lib/libnvqir-qleo_gpu.so   the GPU backend
    <install>/lib/libexaqt_gpu.so        the GPU engine it links
    <install>/targets/qleo_gpu.yml       the GPU target config

`<install>` is the directory holding CUDA-Q's own `lib/` and `targets/`:
site-packages for the `cudaq` wheel, or `$CUDA_QUANTUM_PATH` (typically
/opt/nvidia/cudaq) for a system install.

Driven from the command line as `qleo cudaq install` / `uninstall` /
`status`; the functions here are the supported API behind it.

Both backends ship only in the Linux x86_64 wheel
(`py3-none-manylinux_2_28_x86_64`). On every other platform pip installs
the pure `py3-none-any` wheel, which carries no backend, and these
functions raise `InstallError` saying so.

The GPU backend additionally needs CUDA/cuStateVec loadable in the
process at `cudaq.set_target("qleo_gpu")` time — it does not look for
them itself. `import qleo` (which this package already does on behalf of
its `ExaqtQCSGpu` support) makes them resident via `exaqt`'s
`_preload_cuda_wheels()`, as long as Qleo was installed with the `[gpu]`
extra; no extra step is needed here beyond that ordering.

This module is a port of `qleo_cudaq.install` from the cudaq-integration
project, which builds the files in the first place and ships them
standalone as the `qleo-cudaq` wheel. The file names and the install
layout are deliberately identical, so the two cannot disagree about
where the backend goes.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

# Files staged into the package at build time (see scripts/build_wheel.py,
# which copies them out of a cudaq-integration release).
_BACKEND_DIR = Path(__file__).resolve().parent / "_cudaq"
_LIBS = ("libnvqir-qleo.so", "libexaqt.so", "libnvqir-qleo_gpu.so", "libexaqt_gpu.so")
_TARGET_CONFIGS = ("qleo.yml", "qleo_gpu.yml")

__all__ = ["InstallError", "cudaq_install_dir", "install", "uninstall", "status"]


class InstallError(RuntimeError):
    """Raised when there is nothing to install, or nowhere to install it."""


def cudaq_install_dir() -> Path:
    """The CUDA-Q installation to install into.

    Prefers `$CUDA_QUANTUM_PATH` when set — a machine with both a system
    install and the wheel should follow the explicit choice — and falls
    back to the importable `cudaq` package.
    """
    env = os.environ.get("CUDA_QUANTUM_PATH") or os.environ.get("CUDAQ_INSTALL_PATH")
    if env:
        candidate = Path(env)
        if not (candidate / "targets").is_dir():
            raise InstallError(
                f"{candidate} does not look like a CUDA-Q installation "
                "(no targets/ directory)."
            )
        return candidate

    try:
        # Absolute import: this resolves to the top-level `cudaq` package,
        # not to this module. Do not "fix" it to a relative import.
        import cudaq  # noqa: F401  (imported for its location only)
    except ImportError as exc:
        raise InstallError(
            "CUDA-Q is not installed in this environment. Install it "
            "(`pip install cudaq`) or point CUDA_QUANTUM_PATH at a system "
            "installation."
        ) from exc

    # <site-packages>/cudaq/__init__.py -> <site-packages>, which is where
    # the wheel puts lib/ and targets/.
    install_dir = Path(cudaq.__file__).resolve().parent.parent
    if not (install_dir / "targets").is_dir():
        raise InstallError(
            f"Found cudaq at {install_dir}, but no targets/ directory next "
            "to it. Set CUDA_QUANTUM_PATH to the CUDA-Q installation."
        )
    return install_dir


def _staged_files() -> list[Path]:
    files = [_BACKEND_DIR / name for name in (*_LIBS, *_TARGET_CONFIGS)]
    missing = [f.name for f in files if not f.is_file()]
    if missing:
        raise InstallError(
            "This copy of Qleo carries no backend to install (missing "
            f"{', '.join(missing)}). Both backends ship only in the Linux "
            "x86_64 wheel; on that platform, reinstall with "
            "`pip install --force-reinstall qleo` to pick it up."
        )
    return files


def install(install_dir: Path | None = None) -> list[Path]:
    """Copy the backend in. Returns the paths written."""
    target = install_dir or cudaq_install_dir()
    written = []
    for src in _staged_files():
        dest_dir = target / ("targets" if src.suffix == ".yml" else "lib")
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / src.name
        shutil.copy2(src, dest)
        written.append(dest)
    return written


def uninstall(install_dir: Path | None = None) -> list[Path]:
    """Remove the files `install()` wrote. Returns the paths removed."""
    target = install_dir or cudaq_install_dir()
    removed = []
    for name in (*_LIBS, *_TARGET_CONFIGS):
        path = target / ("targets" if name.endswith(".yml") else "lib") / name
        if path.is_file():
            path.unlink()
            removed.append(path)
    return removed


def status(install_dir: Path | None = None) -> dict[str, bool]:
    """Which of the backend's files are in place, keyed by file name."""
    target = install_dir or cudaq_install_dir()
    return {
        name: (
            target / ("targets" if name.endswith(".yml") else "lib") / name
        ).is_file()
        for name in (*_LIBS, *_TARGET_CONFIGS)
    }
