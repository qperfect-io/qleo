# Getting Started

This page covers installing Qleo and driving the low-level `QleoSV`
state vector directly. To run `mimiqcircuits.Circuit` objects and collect
`QCSResults`, see [Circuit Execution](execute.md).

## Requirements

- Python 3.10 or later
- [`mimiqcircuits`](https://docs.qperfect.io/mimiqcircuits-python/) 0.31
  and NumPy 1.26 or later — both installed automatically with the
  wheel

## Installation

Qleo is installed and imported as **`qleo`**:

```bash
pip install qleo
```

The simulation engine ships as pre-built wheels for Linux (x86-64), macOS
(Apple silicon), and Windows (x86-64) — one `abi3` wheel per platform,
covering Python 3.10 and every later version, so no compiler or Rust
toolchain is needed. On any other platform, see
[Other platforms](#other-platforms).

The plots in `qleo.visualization` need matplotlib, which the base install
leaves out. The `visualization` extra adds it:

```bash
pip install 'qleo[visualization]'
```

Verify the install:

```python
import qleo

print(qleo.__version__)
print(qleo.QleoSV.zero(2).amplitudes())   # [1+0j, 0j, 0j, 0j]
```

### Other platforms

Need a platform without a published wheel — Linux aarch64 or Intel macOS,
for example? [Contact QPerfect](https://www.qperfect.io/contact/).

## Reading the documentation offline

The wheel ships this documentation site inside it, so the version you read
always matches the version you installed:

```bash
qleo docs                  # open the bundled site in a browser
qleo docs --print-path     # or print the path to its index.html
```

`qleo.docs_dir()` returns the same directory from Python. The online copy
lives at <https://docs.qperfect.io/qleo/>.

## The state vector

`QleoSV` is the dense quantum register. Amplitudes are stored in
little-endian order: index `i` of the amplitude array is the basis state
whose bit `k` is set when qubit `k` is `|1>`. Qubit 0 is therefore the
least-significant bit.

```python
import numpy as np
from qleo import QleoSV

# Allocate |000> — three qubits, 2**3 = 8 amplitudes.
sv = QleoSV.zero(3)
print(sv.num_qubits)            # 3
print(len(sv))                  # 8

# Build a GHZ state: H on qubit 0, then fan out with CX.
sv.apply_h(0)
sv.apply_cx(0, 1)
sv.apply_cx(0, 2)

# Read the full amplitude vector (numpy complex128, length 2**3).
amps = sv.amplitudes()
print(amps[0], amps[7])         # (0.707..+0j) (0.707..+0j) — |000> and |111>

# Probability of a single basis state, without materialising the vector.
print(sv.probability(0))        # 0.5
print(sv.probability(7))        # 0.5
```

### Gates

Common gates have dedicated methods; the target qubit is always the last
positional argument, and rotation angles come first.

```python
import math
from qleo import QleoSV

sv = QleoSV.zero(2)

# Non-parametric single-qubit gates.
sv.apply_x(0)                   # Pauli-X on qubit 0
sv.apply_h(1)                   # Hadamard on qubit 1

# Parametric single-qubit gates: angle(s) first, target last.
sv.apply_rx(math.pi / 2, 0)     # RX(pi/2) on qubit 0
sv.apply_u(math.pi, 0.0, math.pi, 1)   # U(theta, phi, lambda) on qubit 1

# Two-qubit gates.
sv.apply_cx(0, 1)               # control 0, target 1
sv.apply_rzz(math.pi / 4, 0, 1) # RZZ(pi/4) on qubits 0 and 1
```

For any unitary not covered by a named method, pass the matrix as a numpy
`complex128` array:

```python
import numpy as np
from qleo import QleoSV

sv = QleoSV.zero(1)

# Hadamard as an explicit 2x2 matrix.
h = np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2)
sv.apply_gate_1q(h, 0)

# A 4x4 array goes to apply_gate_2q(gate, q1, q2).
```

### Expectation values

Compute `<psi|O|psi>` without mutating the state. Pass 1- or 2-qubit
operators as numpy matrices, or a Pauli string spanning any number of
qubits.

```python
import numpy as np
from qleo import QleoSV

sv = QleoSV.zero(3)
sv.apply_h(0)
sv.apply_cx(0, 1)
sv.apply_cx(0, 2)               # GHZ state

# Pauli-string expectation — no need to build a 2**k x 2**k matrix.
# XXX is a GHZ stabiliser, so its expectation is +1.
print(sv.expectation_pauli("XXX", [0, 1, 2]))   # (1+0j)

# 1-qubit operator expectation from a matrix.
z = np.array([[1, 0], [0, -1]], dtype=np.complex128)
print(sv.expectation_1q(z, 0))                   # (0+0j) — <Z> = 0 on qubit 0
```

### Measurement and sampling

Sampling and measurement draw from a seeded `Rng`. The same seed always
reproduces the same stream.

```python
from qleo import QleoSV, Rng

sv = QleoSV.zero(2)
sv.apply_h(0)
sv.apply_cx(0, 1)               # Bell state

rng = Rng(seed=42)

# Draw 1000 shots at once — shape (1000, 2), dtype uint8, qubit 0 first.
shots = sv.sample(rng, nsamples=1000)
print(shots.shape)              # (1000, 2)

# A single destructive measurement of one qubit (collapses the state).
outcome = sv.measure_qubit(0, rng)
print(outcome)                  # 0 or 1
```

### Plotting a state

With the `visualization` extra, `plotstate` draws the most probable basis
states of a state, with colour for the phase, and `StateWindow` follows a state
as you evolve it:

```python
from qleo.visualization import plotstate

fig = plotstate(state)   # state: an QleoState, such as the one qleo.evolve returns
```

See [Visualization](visualization.md) for how to read the plots and use the
window.

## Errors

The wrapper raises subclasses of `QleoError`:

- `GateShapeError` — a gate matrix has the wrong shape or layout.
- `QubitIndexError` — a qubit index is out of bounds, or duplicated.
- `DegenerateStateError` — sampling a state with zero / non-finite norm.

A `MemoryError` is raised (instead of aborting the process) for
state-vector allocations that will not fit — for example
`QleoSV.zero(40)`.

## Next steps

- [Circuit Execution](execute.md) — run whole `mimiqcircuits` circuits.
- [Visualization](visualization.md) — plot a state, or watch it evolve.
- [API Reference](api.md) — the complete public surface.
