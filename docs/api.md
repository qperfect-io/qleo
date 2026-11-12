# API Reference

For a guided tour see [Getting Started](getting-started.md) and
[Circuit Execution](execute.md).

!!! note "Gate / operator matrix inputs"
    Methods that take a 1- or 2-qubit gate or operator (`apply_gate_1q`,
    `apply_gate_2q`, `expectation_1q`, `expectation_2q`, `apply_kraus_*`,
    `apply_mixed_unitary_*`) expect a numpy `complex128` array: a `(2, 2)`
    array for a 1-qubit gate, a `(4, 4)` array for a 2-qubit gate, and a
    `(n_ops, dim, dim)` stack for a set of Kraus / mixed-unitary operators.

!!! note "Qubit / bitstring ordering"
    Qleo is **little-endian by qubit index**: qubit 0 is the
    least-significant bit of the amplitude index, so `bs[0]` is qubit 0.
    This matches Qiskit's little-endian ordering and MimiqCircuitsBase,
    the Julia implementation.

## State vector — `QleoSV`

The dense quantum register. Amplitudes are `complex128`, indexed
little-endian (qubit 0 = LSB).

**Constructors:**

| Method | Description |
|--------|-------------|
| `QleoSV.zero(num_qubits)` | `\|0...0>` state on `num_qubits` qubits |
| `QleoSV.from_bitstring(bits)` | Product state from a 0/1 sequence (qubit 0 = LSB) |
| `QleoSV.from_amplitudes(num_qubits, arr)` | State from a `complex128` amplitude array |

There is no fixed cap on `num_qubits`. Host memory is what binds — an
amplitude is 16 bytes, so a 30-qubit state is 16 GiB — and that limit is
reported rather than predicted: `zero` raises `MemoryError` when the
buffer cannot be reserved. The only absolute bound is arithmetic, at 60
qubits on a 64-bit host (16 TiB), which no machine approaches.

**Properties & inspection:**

| Member | Returns |
|--------|---------|
| `sv.num_qubits` | `int` — number of qubits |
| `sv.len` / `len(sv)` | `int` — number of amplitudes, `2**num_qubits` |
| `sv.get(idx)` | `complex` — amplitude of basis state `idx` |
| `sv.probability(idx)` | `float` — probability of basis state `idx` |
| `sv.amplitudes()` | `complex128` numpy array of all amplitudes |
| `sv.summary(k)` | `(indices, amplitudes, p1, norm_squared)` — the `k` most probable basis states (most probable first), `P(1)` of every qubit and the squared norm, in one pass and without copying the state |
| `sv.norm_squared()` | `float` — squared norm |
| `sv.normalize()` | `float` — norm before normalising; renormalises in place |
| `sv.reset_to_zero()` | Reset to `\|0...0>` in place |
| `sv.clone()` | Deep copy |

**Single-qubit gates** (target qubit last, angles first):

| Method | Description |
|--------|-------------|
| `sv.apply_x/y/z(target)` | Pauli gates |
| `sv.apply_h(target)` | Hadamard |
| `sv.apply_s/sdg/t/tdg/sx(target)` | Phase / T / SX gates |
| `sv.apply_p(lmbda, target)` | Phase gate `P(lambda)` |
| `sv.apply_rx/ry/rz(angle, target)` | Rotation gates |
| `sv.apply_u(theta, phi, lmbda, target)` | General `U` gate |
| `sv.apply_gate_1q(gate, target)` | Arbitrary 1-qubit unitary, `(2, 2)` `complex128` |

**Two-qubit gates:**

| Method | Description |
|--------|-------------|
| `sv.apply_cx/cy/cz(a, b)` | Controlled Pauli gates |
| `sv.apply_swap/iswap(q1, q2)` | (i)SWAP |
| `sv.apply_cp(lmbda, q1, q2)` | Controlled phase |
| `sv.apply_crx/cry/crz(angle, control, target)` | Controlled rotations |
| `sv.apply_rxx/ryy/rzz(theta, q1, q2)` | Two-qubit rotations |
| `sv.apply_gate_2q(gate, q1, q2)` | Arbitrary 2-qubit unitary, `(4, 4)` `complex128` |

**Multi-controlled gates:**

| Method | Description |
|--------|-------------|
| `sv.apply_mcx(controls, target)` | Multi-controlled X |
| `sv.apply_controlled_gate_1q(gate, controls, target)` | Controlled 1-qubit unitary |
| `sv.apply_controlled_gate_2q(gate, controls, q1, q2)` | Controlled 2-qubit unitary |

**Measurement & sampling** (all take a seeded `Rng`):

| Method | Returns |
|--------|---------|
| `sv.prob_zero(target)` | `float` — probability of measuring `0` on `target` |
| `sv.measure_qubit(target, rng)` | `int` — outcome, collapses the state |
| `sv.reset_qubit(target, rng)` | `int` — pre-reset outcome, resets qubit to `\|0>` |
| `sv.sample_bitstring(rng)` | `uint8` array — one sampled bitstring |
| `sv.sample(rng, nsamples)` | `(nsamples, num_qubits)` `uint8` array |

**Noise channels** (each takes a seeded `Rng`):

| Method | Description |
|--------|-------------|
| `sv.apply_kraus_1q(kraus_ops, target, rng)` | 1-qubit Kraus channel, `(n_ops, 2, 2)` |
| `sv.apply_kraus_2q(kraus_ops, q1, q2, rng)` | 2-qubit Kraus channel, `(n_ops, 4, 4)` |
| `sv.apply_mixed_unitary_1q(unitaries, probs, target, rng)` | 1-qubit mixed-unitary channel |
| `sv.apply_mixed_unitary_2q(unitaries, probs, q1, q2, rng)` | 2-qubit mixed-unitary channel |

**Expectation values:**

| Method | Returns |
|--------|---------|
| `sv.expectation_1q(op, target)` | `complex` — `<psi\|O\|psi>` for a `(2, 2)` operator |
| `sv.expectation_2q(op, q1, q2)` | `complex` — `<psi\|O\|psi>` for a `(4, 4)` operator |
| `sv.expectation_pauli(paulis, qubits)` | `complex` — expectation of a Pauli string (e.g. `"ZZZ"`) |

---

## Simulator — `QleoQCS`

::: qleo.QleoQCS
    options:
      show_root_heading: true
      members:
        - __init__
        - execute
        - evolvezerostate
        - evolve
        - compile
        - expectation
        - capabilities

---

## GPU simulator — `QleoSVGpu` / `QleoQCSGpu`

!!! warning "Linux, NVIDIA GPU and the `gpu` extra"
    The published Linux wheels carry the GPU backend, and it runs once the
    CUDA libraries are installed:

    ```sh
    pip install "qleo[gpu]"   # CUDA 12 runtime, cuBLAS, cuStateVec
    ```

    Only the NVIDIA driver has to come from the system. A system CUDA and
    cuQuantum install on the loader path (`LD_LIBRARY_PATH`) works too. The
    macOS and Windows wheels do not carry the backend.

    Probe at runtime with `qleo.gpu_available()`, which is `True` when the
    libraries load and a device answers. `QleoSVGpu`, `QleoQCSGpu`,
    `CudaError` and `CudaUnavailableError` exist in every build that carries
    the backend; without the libraries, constructing a state raises
    `CudaUnavailableError`.

    These members are documented by hand rather than generated, precisely
    because they are absent from a CPU-only build.

`QleoSVGpu` is a state vector living in device memory, backed by NVIDIA's
cuStateVec. Every method it has is named and shaped exactly like its
`QleoSV` counterpart — same gate set, same little-endian qubit order, same
column-major matrix convention — and `QleoQCSGpu` advertises the same
capability set as `QleoQCS`. Any circuit that runs on one runs on the other.

```python
import qleo

if qleo.gpu_available():
    results = qleo.QleoQCSGpu().execute(circuit, nsamples=1000)
```

**Reproducible across backends.** Every stochastic operation — measurement,
reset, sampling, Kraus and mixed-unitary branch selection — draws from the
same seeded Xoshiro256++ stream in the same order and count as the CPU core.
So `QleoQCSGpu(seed=n)` and `QleoQCS(seed=n)` follow the same trajectory,
and a run can be reproduced on a laptop without a GPU.

The one place exact agreement is not guaranteed by construction is `sample`:
cuStateVec searches its own cumulative array, so an exact tie between two
basis states can in principle resolve differently in the last bit. The
distribution is identical either way.

**How wide a state may be.** There is no fixed qubit cap — the card's
free memory decides, and `QleoSVGpu.max_qubits_on_device()` reports it:
the widest state the current device will hold right now, `0` if not even
one qubit fits.

The constructors check the same thing before allocating. A state is
`2**n * 16` bytes, so 30 qubits needs 16 GiB and fits a 24 GB card, while
an 80 GB card reaches 32. A request the device has no room for raises
`MemoryError` naming the byte counts, rather than a bare CUDA status.

The figure is a snapshot, not a constant — memory held by an existing
state, or by another process on the same card, lowers it. Reading it also
creates and destroys a CUDA context, so it measures the device as a
constructor leaves it; that makes it a capability query rather than
something to call in a loop.

Nothing is padded onto the measurement. A margin would be a guess, and a
guess in that direction refuses states that would have run; the marginal
case is left to `cudaMalloc`, which reports rather than crashing.

The minimum is 1 qubit, unlike `QleoSV`: cuStateVec has no 0-qubit state.

**Three shape differences from `QleoSV`:**

| Member | Description |
|--------|-------------|
| `sv.synchronize()` | GPU-only. Block until queued kernels finish — gate calls only *enqueue* work, so any timing loop needs this. |
| `sv.set_amplitude(idx, value)` | GPU-only. Overwrite one amplitude in place (no re-normalisation). |
| `sv.clone()` | Can raise `CudaError`. Device memory is scarcer than host memory, so a failed allocation reports rather than aborting. |

`sv.amplitudes()` exists but copies the whole buffer back to the host — 16
bytes per amplitude, so 4 GiB at 28 qubits. Prefer `sv.get(idx)`.

`expectation_pauli` returns a value whose imaginary part is exactly zero,
where the CPU version carries floating-point noise of order 1e-16: cuStateVec
computes a Pauli product's expectation as a real number. Compare with a
tolerance, not for equality.

**Differences in `QleoQCSGpu`'s default pipeline.** Fusion runs at *every*
circuit size, with no cache-derived qubit threshold: on a GPU a fused block
costs one pass over the state whatever its width, so fusing *n* gates is worth
about *n*×. Qubit reordering is omitted — `QleoReorderQubitsPass` scores the
CPU's per-slot SIMD kernels, which say nothing about cuStateVec. `EXAQT_FUSE`,
`EXAQT_FUSE_THRESHOLD` and `EXAQT_FUSE_MAX_SUPPORT` are honoured as on the CPU.

**Errors.** Failures that come from the shared core (a bad qubit index, a
malformed gate matrix) raise the same exceptions as the CPU backend, so
`except` clauses stay backend-agnostic. Two are GPU-specific: `CudaError`
(a CUDA or cuStateVec call returned a non-success status) and
`CudaUnavailableError` (the extension carries the feature but was built
without a CUDA runtime). Both derive from `QleoError`. A state too wide
for the card raises plain `MemoryError` — the same exception the CPU
backend raises for a host allocation it cannot make, so one `except`
covers both.

---

## Composite state — `QleoState`

::: qleo.QleoState
    options:
      show_root_heading: true
      members:
        - zero
        - one
        - product
        - amplitude
        - sample
        - reset

---

## Per-instruction primitives

::: qleo.evolve
    options:
      show_root_heading: true

::: qleo.apply_instruction
    options:
      show_root_heading: true

---

## Compilation passes

::: qleo.QleoFlattenContainersPass
    options:
      show_root_heading: true

::: qleo.QleoReorderQubitsPass
    options:
      show_root_heading: true

---

## Random number generator — `Rng`

`Rng(seed)` is a seeded PRNG handle used by every measurement, sampling,
and noise-channel method. The same seed reproduces the same Xoshiro256++
stream across the Rust core and the Python and Julia wrappers.

```python
from qleo import Rng
rng = Rng(seed=42)
```

---

## Plotting — `qleo.visualization`

Needs the `visualization` extra (`pip install 'qleo[visualization]'`);
`import qleo` alone never loads matplotlib.

For a guided tour, see [Visualization](visualization.md).

::: qleo.visualization.plotstate
    options:
      show_root_heading: true

::: qleo.visualization.StateWindow
    options:
      show_root_heading: true
      members: [update]

---

## Package metadata

| Member | Returns |
|--------|---------|
| `qleo.__version__` | `str` — installed version of the `qleo` distribution |

::: qleo.docs_dir
    options:
      show_root_heading: true

---

## Exceptions

All exceptions subclass `QleoError` (itself a `RuntimeError`):

| Exception | Raised when |
|-----------|-------------|
| `GateShapeError` | a gate matrix has the wrong shape or layout |
| `QubitIndexError` | a qubit index is out of bounds, or duplicated |
| `DegenerateStateError` | sampling a state with zero / non-finite norm |
