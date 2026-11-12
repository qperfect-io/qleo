# Changelog

All notable changes to `qleo` are documented here — including the ones that
arrive through the simulation engine.

Qleo is a thin branding layer over QPerfect's Exaqt (`mimiq-exaqt`), so most
of what changes for a user is engine behaviour: new features, changed
defaults, and occasionally a break. Each release therefore names the engine
version it pins and summarises what that version brings. The engine's own
changelog carries the full detail and the measurements.

This file follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and Qleo versions follow [Semantic Versioning](https://semver.org/).

## [0.24.0] — 2026-11-12

The engine moves to **Exaqt 0.5.1** (`mimiq-exaqt>=0.5.1,<0.6`, was 0.2.1),
and the CUDA-Q backends to qleo-cudaq v0.3.0 (exaqt-rs 0.4.0, exaqt-gpu
0.5.0). See the engine's changelog for 0.3.0 to 0.5.1 in full.

### Breaking

- `QleoQCS(reorderqubits=...)` is gone: choose reordering per call with
  `sim.execute(c, reorderqubits=False)` or `"sa"`.
- `mimiqcircuits` 0.31 is required (was 0.27), and the `qiskit` extra needs
  `mimiq-qiskit` 0.4.2.
- The CUDA-Q backend is built for **CUDA-Q 0.16.0.post1** (was 0.14). The
  plugin ABI changed, so the backend no longer loads on 0.14 or 0.15, and
  crashes on 0.16.0 without the `.post1`.

### Added

- **GPU simulation is back**: `QleoQCSGpu` and `QleoSVGpu` on NVIDIA GPUs
  (cuStateVec), with `gpu_available()`, `CudaError` and
  `CudaUnavailableError`. The Linux wheel carries the backend;
  `pip install "qleo[gpu]"` adds the CUDA libraries.
- `qleo.visualization`: `plotstate` and `StateWindow` for state vectors,
  behind the `visualization` extra, which now goes through the engine's.
- `is_container` and `QleoFlattenContainersPass`, from the engine.
- `execute` takes `fuse`, `fuse_threshold`, `canonicaldecompose`,
  `reorderqubits`, `remove_swaps` and `reorderqubits_seed`.
- `QleoQCS(max_num_threads=n)` caps the threads a run uses.
- `QleoQCS` runs `CircuitTesterExperiment`s and, through `mimiqcircuits`,
  `optimize(...)` for `OptimizationExperiment`s.
- `QFT`, `PhaseGradient` and `Diffusion` run; they used to raise an
  unsupported-operation error.
- The CUDA-Q backend is built on exaqt-rs 0.4.0, whose k-qubit kernel uses
  every thread wherever its targets sit.
- CUDA-Q: kernels can start a register from a state,
  `cudaq.qvector(cudaq.State.from_data(...))`.
- CUDA-Q: a GPU target, `cudaq.set_target("qleo_gpu")`, running the same
  operation set as `qleo` on the engine's GPU state-vector core
  (cuStateVec). Needs `pip install "qleo[gpu]"` and `import qleo` before
  `set_target`, so the CUDA/cuStateVec libraries are already loaded (see
  the CUDA-Q docs page). `qleo cudaq install`/`status`/`uninstall` now
  manage both backends.

## [0.23.0] — 2026-09-11

The simulation engine changed: Qleo is now a branding layer over QPerfect's
**Exaqt** (`mimiq-exaqt` 0.2.1) rather than Quantanium. The public API is
Exaqt's, name for name, with `Exaqt*` renamed `Qleo*` — which makes this a
breaking release.

### Breaking

- `Qleo` → `QleoQCS`.
- **GPU simulation is gone from this release**, and with it
  `Qleo(use_gpu=True)`, the `QleoGPU` CUDA-Q target, and the `QleoSVGpu` /
  `QleoQCSGpu` / `CudaError` / `CudaUnavailableError` names. Qleo exposes what
  the released engine exposes, and the engine's CUDA backend is not in any
  published `mimiq-exaqt` wheel. `qleo.gpu_available()` is removed rather than
  left to return `False` for a capability that cannot be reached. The
  `introduction/Basics/gpu_accelerated_sim` notebook is removed with them, as
  is the CUDA/cuQuantum stack it pulled into `notebooks/requirements.txt`.
  GPU support is planned to return once the engine ships it.
- `qleo.visualization` is gone; use `mimiqcircuits.visualization` (still
  behind the `visualization` extra).
- Python 3.10 or later is required (was 3.9).
- `mimiqcircuits` 0.27.0 or later is required (was 0.18).
- The CUDA-Q target is renamed `qleo` (was `Qleo`), and its files with it:
  `libnvqir-qleo.so` + `libexaqt.so` + `qleo.yml`, replacing
  `libnvqir-Qleo.so` + `Qleo.yml`. Update `cudaq.set_target("Qleo")` to
  `cudaq.set_target("qleo")`.
- The CUDA-Q target is **no longer active on install**. 0.22.x dropped its
  files into the environment as a side effect of `pip install`; that only
  worked when CUDA-Q happened to be the wheel in the same `site-packages`,
  and it baked the build interpreter's Python version into the paths. Run
  **`qleo cudaq install`** once per environment instead — see
  [CUDA-Q Interoperability](https://docs.qperfect.io/qleo/cudaq/).
- The CUDA-Q backend now ships only in the Linux x86-64 wheel. macOS,
  Windows and other architectures get the pure-Python `py3-none-any` wheel,
  where `qleo cudaq install` reports that there is no backend to install.
- `qleo.visualization.generate_animation` is gone — it was a Quantanium
  feature with no Exaqt or `mimiqcircuits` equivalent. The
  `usecases/teaching/grover_animated` notebook is removed with it.

### Added

- `QleoSV` / `QleoState`, the low-level state-vector and composite-state
  handles, plus `evolve` / `apply_instruction` for per-instruction control.
- `QleoReorderQubitsPass`, `default_fuse_threshold`.
- `QleoError` and its subclasses `GateShapeError`, `QubitIndexError`,
  `DegenerateStateError`, `NonUnitaryError`.
- `from qleo import *` still re-exports the `mimiqcircuits` circuit API, as
  in 0.22.x — the one place Qleo diverges from Exaqt.
- `qleo docs` console command and `qleo.docs_dir()` — the wheel bundles the
  documentation site.
- `qleo cudaq install` / `uninstall` / `status`, and the `qleo.cudaq` API
  behind them, for enabling Qleo as a CUDA-Q target. CUDA-Q has no plugin
  search path, so the backend has to be copied into its installation;
  `$CUDA_QUANTUM_PATH` picks the target when a system install and the
  `cudaq` wheel are both present.
- A `qiskit` extra: `pip install qleo[qiskit]` pulls in `mimiq-qiskit`, which
  wraps `QleoQCS` as a Qiskit `BackendV2`.
- Documentation moved from Sphinx to MkDocs (`mkdocs.yml`, `docs/`).

### Engine (mimiq-exaqt 0.2.1, qleo-cudaq backend v0.2.0)

What the new engine does that the Quantanium-backed 0.22.x did not:

- **SIMD state-vector core** in Rust, with runtime AVX-512 / AVX2 / NEON
  dispatch and specialised kernels for the common gates.
- **Gate fusion on by default** above the qubit count where the state vector
  spills the last-level cache (`default_fuse_threshold()`, ~20–21 qubits).
  Retune with `EXAQT_FUSE` (`auto` / `always` / `never`),
  `EXAQT_FUSE_THRESHOLD` and `EXAQT_FUSE_MAX_SUPPORT`, or pass
  `execute(..., passes=...)`.
- **Qubit reordering on by default** at 13 qubits and up, landing gates on
  the fastest kernels. Governed by `QleoQCS(reorderqubits=...)`.
- **Multi-qubit Pauli-string expectation values** through a native `O(2^n)`
  mask-based path, `QleoSV.expectation_pauli`.
- **`QleoSV.apply_gate_kq`** for dense 1–5 qubit unitaries.
- `QCSResults.simulator` reads `Qleo` (was `Quantanium StateVector`).
- Fixed in the engine, and inherited here: `Add` and `Multiply` z-register
  operations **assign** their result rather than accumulating into the
  destination, which silently corrupted coefficient-scaled folded
  expectation values.

## [0.22.1] and earlier

Wrapper over the Quantanium simulator. See the git history up to the
`v0.22.1` tag.
