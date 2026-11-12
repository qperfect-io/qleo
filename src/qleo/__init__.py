# Copyright (c) 2025-2026 QPerfect. All Rights Reserved.
# Proprietary and confidential.

"""Qleo — SIMD-accelerated state-vector quantum simulator.

Qleo is the Quobly-branded distribution of QPerfect's Exaqt simulator: the
same Rust core, the same behaviour, and the same API under Qleo names. Every
public name below is the engine's own type re-exported — ``QleoQCS`` *is*
``exaqt.ExaqtQCS`` — so anything written against one runs on the other.

- :class:`QleoSV` — dense quantum state-vector (rust-backed handle).
- :class:`QleoState` — composite state (qubits + classical bits + z-vars).
- :class:`QleoQCS` — simulator. Subclass of
  :class:`mimiqcircuits.backends.LocalBackend`; inherits the full
  ``execute(...)`` driver. Construct one and call
  ``QleoQCS().execute(circuit, ...)``.
- :class:`Rng` — seeded PRNG handle for measurements / sampling.

``mimiqcircuits`` is re-exported, so ``from qleo import *`` brings in the
circuit API — ``Circuit``, the gates, ``QCSResults`` — alongside the
simulator. This is the one place Qleo diverges from Exaqt, which leaves
that import to the caller.

On Linux the engine also carries its NVIDIA GPU backend, and two more names
appear: :class:`QleoSVGpu` and :class:`QleoQCSGpu`. They need an NVIDIA
driver and the CUDA libraries, which ``pip install "qleo[gpu]"`` brings in;
:func:`gpu_available` reports whether this host can run them.
"""

from pathlib import Path

from mimiqcircuits import *  # noqa: F401,F403
import mimiqcircuits as _mc

from exaqt import (
    ExaqtSV as QleoSV,
    ExaqtState as QleoState,
    ExaqtQCS as _ExaqtQCS,
    ExaqtReorderQubitsPass as QleoReorderQubitsPass,
    ExaqtError as QleoError,
    Rng,
    ExaqtFlattenContainersPass as QleoFlattenContainersPass,
    evolve,
    apply_instruction,
    is_container,
    default_fuse_threshold,
    gpu_available,
    GateShapeError,
    QubitIndexError,
    DegenerateStateError,
    NonUnitaryError,
)


class QleoQCS(_ExaqtQCS):
    """State-vector quantum circuit simulator.

    The engine's simulator, reporting itself as Qleo. Only the advertised
    identity is overridden — `QCSResults.simulator` and progress output
    then carry the Qleo brand; behaviour, options and capabilities are the
    engine's, unchanged.
    """

    @property
    def name(self) -> str:
        return "Qleo"

    @property
    def version(self) -> str:
        return __version__

    @staticmethod
    def qcsname() -> str:
        return "Qleo"


# The GPU names exist only in an engine built with its `gpu` feature, which
# the Linux wheels are; macOS and Windows wheels have none, and neither does
# Qleo there.
try:
    from exaqt import (
        ExaqtSVGpu as QleoSVGpu,
        ExaqtQCSGpu as _ExaqtQCSGpu,
        CudaError,
        CudaUnavailableError,
    )
except ImportError:  # pragma: no cover - depends on the engine build
    _HAS_GPU = False
else:
    _HAS_GPU = True

    class QleoQCSGpu(_ExaqtQCSGpu):
        """GPU state-vector simulator (CUDA / cuStateVec).

        The engine's GPU simulator, reporting itself as QleoGpu; as with
        :class:`QleoQCS`, only the advertised identity is overridden.
        """

        @property
        def name(self) -> str:
            return "QleoGpu"

        @property
        def version(self) -> str:
            return __version__

        @staticmethod
        def qcsname() -> str:
            return "QleoGpu"


try:
    from importlib.metadata import PackageNotFoundError, version as _pkg_version

    __version__ = _pkg_version("qleo")
except (ImportError, PackageNotFoundError):  # pragma: no cover - source tree
    __version__ = "0.0.0+unknown"


def docs_dir() -> Path:
    """Path to the HTML documentation bundled with the package.

    Returns the directory holding the built documentation site
    (``index.html`` and assets) that ships inside the wheel. Open it with
    the ``qleo docs`` console command. The directory is absent in builds
    made without the documentation site, in which case the online copy at
    https://docs.qperfect.io/qleo/ applies.
    """
    return Path(__file__).resolve().parent / "_docs"


__all__ = [
    # Core types
    "QleoSV",
    "QleoState",
    "QleoQCS",
    "Rng",
    # Per-instruction primitives
    "evolve",
    "apply_instruction",
    "is_container",
    # Compilation passes
    "QleoFlattenContainersPass",
    "QleoReorderQubitsPass",
    "default_fuse_threshold",
    # Package metadata
    "__version__",
    "docs_dir",
    "gpu_available",
    # Exceptions
    "QleoError",
    "GateShapeError",
    "QubitIndexError",
    "DegenerateStateError",
    "NonUnitaryError",
    # The circuit API, re-exported for `from qleo import *`.
    *_mc.__all__,
]
if _HAS_GPU:
    __all__ += ["QleoSVGpu", "QleoQCSGpu", "CudaError", "CudaUnavailableError"]
