# Qleo

Qleo is a **SIMD-accelerated state-vector quantum circuit
simulator** for [MIMIQ](https://docs.qperfect.io/mimiqcircuits-python/).
It represents the full quantum state as a dense complex vector of
`2**num_qubits` amplitudes and applies gates with a vectorised Rust core
(runtime AVX-512 / AVX2 / NEON dispatch), exposed to Python through PyO3.

The vectorised native extension ships with the package; its public types
are re-exported on the top-level `qleo` package, together with the
`mimiqcircuits` circuit API — so `from qleo import *` gives you `Circuit`,
the gates and `QCSResults` alongside the simulator.

There are two ways to use it:

- **High level** — build a circuit with `mimiqcircuits`, run it with an
  `QleoQCS` simulator, and receive the same `QCSResults` object
  MIMIQ uses elsewhere. See [Circuit Execution](execute.md).
- **Low level** — drive an `QleoSV` state vector directly: allocate
  a state, apply gates by name, and read amplitudes, probabilities,
  expectation values, or samples. See [Getting Started](getting-started.md).
- **From Qiskit** — wrap the simulator as a Qiskit `BackendV2` and run
  `QuantumCircuit`s on it. See
  [Qiskit Interoperability](qiskit.md).

## Quick start

```python
import mimiqcircuits as mc
from qleo import QleoQCS

# Build a Bell-state circuit.
c = mc.Circuit()
c.push(mc.GateH(), 0)
c.push(mc.GateCX(), 0, 1)
c.push(mc.Measure(), 0, 0)
c.push(mc.Measure(), 1, 1)

# Run it on the state-vector simulator — returns a QCSResults object.
sim = QleoQCS()
results = sim.execute(c, nsamples=1000)
print(results.histogram())      # e.g. {bs"00": 512, bs"11": 488}
```

Or work with the state vector directly:

```python
from qleo import QleoSV

sv = QleoSV.zero(3)       # |000>
sv.apply_h(0)
sv.apply_cx(0, 1)
sv.apply_cx(0, 2)
print(sv.amplitudes())          # numpy complex128 array, length 2**3
print(sv.expectation_pauli("XXX", [0, 1, 2]))   # +1 for the GHZ state
```

## Features

- Dense state-vector core written in Rust, exposed through PyO3.
- Runtime SIMD dispatch: AVX-512 / AVX2 on x86-64, NEON on ARM.
- Specialised kernels for the common gates (`X`, `Y`, `Z`, `H`, `S`, `T`,
  `SX`, `P`, `RX`, `RY`, `RZ`, `U`, `CX`, `CY`, `CZ`, `SWAP`, `iSWAP`,
  `CP`, `CRX`, `CRY`, `CRZ`, `RXX`, `RYY`, `RZZ`) plus generic
  `apply_gate_1q` / `apply_gate_2q` escape hatches for any unitary.
- Multi-controlled gates applied directly, without CX decomposition.
- Mid-circuit measurement, reset, and classically conditioned operations.
- Noise simulation via Kraus and mixed-unitary channels (trajectory sampling).
- Observables: single amplitudes, 1- and 2-qubit expectation values, and
  multi-qubit Pauli-string expectations.
- Exact qubit reordering to land gates on the fastest kernels.
- Reproducible sampling through a seeded `Rng` shared across the Rust,
  Python, and Julia wrappers.
- Results returned as MIMIQ `QCSResults` (samples, amplitudes, fidelities,
  timings).

## Installation

Qleo is installed and imported as **`qleo`**:

```bash
pip install qleo
```

The simulation engine ships pre-built for Linux (x86-64), macOS (Apple
silicon), and Windows (x86-64) — no compiler or Rust toolchain needed. The
Qleo wheel also
bundles this documentation: run `qleo docs` to read it offline.

To drive Qleo from Qiskit instead, add the `qiskit` extra, which pulls in
the [`mimiq-qiskit`](https://docs.qperfect.io/mimiq-qiskit/) bridge:

```bash
pip install qleo[qiskit]
```

See [Getting Started](getting-started.md) for the requirements and the
qubit-ordering conventions.

## Where to go next

- **[Getting Started](getting-started.md)** — installation, your first
  state vector, gate application, and reading results.
- **[Circuit Execution](execute.md)** — running a `mimiqcircuits.Circuit`
  with `QleoQCS`: sampling vs. trajectory mode, observables, noise.
- **[Qiskit Interoperability](qiskit.md)** — running Qiskit
  `QuantumCircuit`s on Qleo through the `mimiq-qiskit` bridge, with
  native Qiskit primitives.
- **[API Reference](api.md)** — every public type and function, generated
  from the source docstrings.

## Conventions

- **Qubit ordering.** Qubit 0 is the **least-significant bit** of the
  basis-state index (matches Qiskit's little-endian ordering and
  MimiqCircuitsBase, the Julia implementation). Amplitude index `i` has
  bit `k` set when qubit `k` is in state `|1>`.
- **Gate matrices.** `apply_gate_1q` / `apply_gate_2q` and the
  expectation methods take numpy `complex128` arrays — `(2, 2)` for a
  1-qubit gate, `(4, 4)` for a 2-qubit gate.
- **Reproducibility.** The same `Rng(seed)` produces the same
  Xoshiro256++ stream in the Rust core, the Python wrapper, and the Julia
  wrapper.

## License and support

Qleo is proprietary software. Copyright &copy; 2025&ndash;2026
QPerfect. All rights reserved. Use is governed by your QPerfect licence
agreement.

For licensing, platform requests, or technical support,
[contact QPerfect](https://www.qperfect.io/contact/).
