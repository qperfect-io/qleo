# QLEO (Quobly Logical Emulator Online)

**QLEO** is a Python library for building, simulating and analysing quantum
circuits on [Quobly](https://quobly.io/) hardware models. It is the
Quobly-branded distribution of **Exaqt** by
**[QPerfect](https://qperfect.io/)** — a SIMD-accelerated state-vector
simulator with a Rust core.

Same engine, same API, Qleo names: `QleoQCS` *is* `exaqt.ExaqtQCS`, so
anything written against one runs unchanged on the other. This repository
holds only the branding layer; the engine is the `mimiq-exaqt` dependency.

> **Migrating from qleo 0.22.x?** The simulator class is now `QleoQCS`
> (was `Qleo`), and `Qleo(use_gpu=True)` becomes `QleoQCSGpu()`.
> `from qleo import *` still gives you the circuit API. See
> [CHANGELOG.md](CHANGELOG.md).

## Install (release wheel)

```sh
pip install qleo
pip install qleo[visualization]   # + matplotlib, for plothistogram & co.
```

The wheel bundles the documentation. Read it offline, without a network round
trip, with:

```sh
qleo docs                  # open the bundled site in a browser
qleo docs --print-path     # or just print where it lives
```

## Install (development checkout)

```sh
cd qleo
uv venv && uv sync
uv pip install -e .
.venv/bin/python -m pytest -q tests/
```

An editable install carries no bundled docs, so `qleo docs` has nothing to
open — run `mkdocs serve` instead. To produce the wheel exactly as CI
publishes it, documentation included, run `python scripts/build_wheel.py`.

## GPU

The Linux wheel carries an NVIDIA GPU backend, `QleoQCSGpu`, on
cuStateVec. It needs the NVIDIA driver and the CUDA libraries, which the
`gpu` extra installs:

```sh
pip install "qleo[gpu]"
```

```python
from qleo import *

sim = QleoQCSGpu() if gpu_available() else QleoQCS()
```

`QleoQCSGpu(seed=n)` follows the same trajectory as `QleoQCS(seed=n)`, so a
GPU run can be reproduced on a CPU.

## Quick example

```python
import numpy as np
from qleo import QleoSV, Rng

sv = QleoSV.zero(3)
sv.apply_h(0)
sv.apply_cx(0, 1)
sv.apply_cx(0, 2)
print(sv.amplitudes())          # numpy complex128 array, length 2**3

# Multi-qubit Pauli expectation (no need to build a 2^k × 2^k matrix).
print(sv.expectation_pauli("XXX", [0, 1, 2]))   # +1 for the GHZ state

# Sampling.
r = Rng(seed=42)
shots = sv.sample(r, nsamples=1000)             # shape (1000, 3) uint8
```

## mimiqcircuits integration

`qleo` re-exports the `mimiqcircuits` circuit API, so one import is enough:

```python
from qleo import *

c = Circuit()
c.push(GateH(), 0)
c.push(GateCX(), 0, 1)

sim = QleoQCS()
result = sim.execute(c, nsamples=1000)   # returns a mimiqcircuits.QCSResults
print(result)
```

Explicit imports work just as well, and are what the documentation uses:

```python
import mimiqcircuits as mc
from qleo import QleoQCS

result = QleoQCS().execute(mc.Circuit(), nsamples=1000)
```

## Conventions

- **Qubit ordering.** Qubit 0 is the **least-significant bit** of the
  basis-state index (matches Qiskit and MimiqCircuitsBase).
- **2-qubit gate basis.** For `apply_gate_2q(M, q1, q2)`, `q1` is the
  **most significant** bit of the gate's local 2×2-bit basis. See the
  Rust crate's docs for the precise layout.
- **Cross-language reproducibility.** The same `Rng(seed)` produces the
  same Xoshiro256++ stream in the Rust core, the Python wrapper, and
  the Julia wrapper.

## Errors

The wrapper raises Python exception subclasses of `QleoError`:

- `GateShapeError` — gate matrix has the wrong shape or layout.
- `QubitIndexError` — qubit index out of bounds, or duplicate qubits.
- `DegenerateStateError` — sampling a state with zero / non-finite norm.
- `NonUnitaryError` — only raised when the Rust crate is built with the
  `unitary-checks` feature; flags a non-unitary user matrix.

`MemoryError` is raised for state-vector allocations that won't fit
(e.g. `QleoSV.zero(40)`) — instead of aborting the process.

## Documentation

Full documentation: [docs.qperfect.io/qleo](https://docs.qperfect.io/qleo/).
The `mimiqcircuits` circuit API it builds on is documented at
[docs.qperfect.io/mimiqcircuits-python](https://docs.qperfect.io/mimiqcircuits-python/).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Maintainers cutting a release should
read [RELEASING.md](RELEASING.md).

## Contact

- **Suggestions**: [contact (Quobly)](https://quobly.io/) or [contact (QPerfect)](https://qperfect.io/#contact)
- **Email**: [support (QPerfect)](mailto:mimiq.support@qperfect.io)
