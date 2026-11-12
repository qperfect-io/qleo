# Qiskit Interoperability

Qleo runs [Qiskit](https://www.ibm.com/quantum/qiskit) circuits through
**[`mimiq-qiskit`](https://docs.qperfect.io/mimiq-qiskit/)**, the Qiskit
bridge for MIMIQ. Its `MimiqBackend` is a Qiskit `BackendV2` that accepts
any MIMIQ backend, and `QleoQCS` is one — so a `QuantumCircuit` runs on
the Qleo state-vector core without leaving the Qiskit ecosystem, and
without a cloud connection.

Install the bridge together with Qleo through the `qiskit` extra:

```bash
pip install qleo[qiskit]
```

## Wrapping Qleo as a Qiskit backend

Hand an `QleoQCS` instance to `MimiqBackend` and use it wherever a Qiskit
backend is expected:

```python
from qiskit import QuantumCircuit
from mimiq_qiskit import MimiqBackend
from qleo import QleoQCS

# `num_qubits` is the width advertised to Qiskit's transpiler, not a cap on
# `run`: a simulator is limited by memory, not by a coupling map. Set it wide
# enough to cover the circuits you transpile against this backend.
backend = MimiqBackend(QleoQCS(), name="qleo", num_qubits=24)

qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])

result = backend.run(qc, shots=1000, seed=42).result()
print(result.get_counts())      # {'00': 526, '11': 474}
```

`run` returns a `qiskit.result.Result`, so `get_counts()`,
`get_memory()`, and the rest of the Qiskit result API behave exactly as
they would on Aer or an IBM device.

Every constructor option of `QleoQCS` still applies — it is the object
doing the simulating. Pass a seed for a reproducible instance, and tune
qubit reordering per job:

```python
from qleo import QleoQCS
from mimiq_qiskit import MimiqBackend

# Instance-level seed, so every job on this backend is reproducible.
backend = MimiqBackend(QleoQCS(seed=1234))

# Reordering disabled for this job, for a like-for-like comparison
# against another simulator.
job = backend.run(qc, reorderqubits=False)
```

## Batching

MIMIQ accepts a list of circuits per job, and the bridge uses that: a list
handed to `run` becomes **one** submission, evolved circuit by circuit.

```python
from qiskit import QuantumCircuit
from mimiq_qiskit import MimiqBackend
from qleo import QleoQCS

backend = MimiqBackend(QleoQCS(seed=7))

ghz = QuantumCircuit(3, 3)
ghz.h(0)
ghz.cx(0, 1)
ghz.cx(1, 2)
ghz.measure([0, 1, 2], [0, 1, 2])

flip = QuantumCircuit(3, 3)
flip.x(1)
flip.measure([0, 1, 2], [0, 1, 2])

job = backend.run([ghz, flip], shots=200)
result = job.result()

print(result.get_counts(0))      # {'000': ~100, '111': ~100}
print(result.get_counts(1))      # {'010': 200}
```

## Transpiling for Qleo

**Usually you should not.** There is no coupling map, no SWAP insertion,
and no basis a simulator must be lowered to, so a transpiler pass buys
nothing here — and it can cost you a great deal.

The converter no longer needs help with coverage either. A gate outside
the bridge's `Target` is decomposed through its own Qiskit `definition`,
and a `ControlledGate` becomes a **native MIMIQ `Control`** rather than
being synthesised away. That matters, because applying multi-controlled
gates directly, without a CX ladder, is exactly what Qleo is good at:

```python
from qiskit import QuantumCircuit, transpile
from mimiq_qiskit import MimiqBackend
from mimiq_qiskit.converter import qiskit_to_mimiq
from qleo import QleoQCS

backend = MimiqBackend(QleoQCS(), num_qubits=8)

qc = QuantumCircuit(6)
qc.h(0)
qc.mcx([0, 1, 2, 3, 4], 5)

# Straight through the converter: the 5-control X stays one instruction.
print(sum(1 for _ in qiskit_to_mimiq(qc)))                       # 2 — H, C5X

# Transpiled first: the same gate is shattered into the Target basis.
print(sum(transpile(qc, backend=backend).count_ops().values()))  # ~160
```

Reach for `transpile` only when you actually want the circuit expressed in
the `Target` gate set — comparing against another backend, say. The
`Target` is still advertised, so `transpile(qc, backend=backend)` works
whenever you do want it.

!!! warning "The transpiler may permute your qubits"

    Qiskit elides permutations (`SWAP`s, and the ones inside `QFT`) into
    the layout rather than emitting them. The transpiled circuit then acts
    on relabelled qubits, and an observable written against the *original*
    circuit no longer lines up. Apply the layout before measuring it:

    ```python
    tqc = transpile(qc, backend=backend)
    observable = observable.apply_layout(tqc.layout)
    ```

    Counts from `run` are unaffected — measurements are transpiled along
    with the circuit. This is standard Qiskit behaviour, not specific to
    Qleo, but it is the most common source of "the expectation value is
    wrong" reports.

## Primitives

The bridge ships native Qiskit V2 primitives. Prefer them over Qiskit's
generic `BackendSamplerV2` / `BackendEstimatorV2`, which would round-trip
through counts and hex strings.

### Sampling

`MimiqSamplerV2` reads MIMIQ's sampled bitstrings straight into a
per-register `BitArray`:

```python
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from mimiq_qiskit import MimiqBackend, MimiqSamplerV2
from qleo import QleoQCS

sampler = MimiqSamplerV2(MimiqBackend(QleoQCS(seed=5)), default_shots=1024)

theta = Parameter("theta")
qc = QuantumCircuit(1, 1)
qc.rx(theta, 0)
qc.measure(0, 0)

# One binding per row: Rx(0) leaves |0>, Rx(pi) drives it to |1>.
result = sampler.run([(qc, [[0.0], [np.pi]])]).result()[0]
print(result.data.c[0].get_counts())      # {'0': 1024}
print(result.data.c[1].get_counts())      # {'1': 1024}
```

Each `ClassicalRegister` becomes its own field on `result.data`, named
after the register.

### Expectation values

`MimiqEstimatorV2` is **exact**. It converts each observable to a MIMIQ
`Hamiltonian`, pushes it as an expectation-value instruction, and reads the
result back — no measurement sampling, so no shot noise and reported
standard deviations of zero.

```python
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import SparsePauliOp
from mimiq_qiskit import MimiqBackend, MimiqEstimatorV2
from qleo import QleoQCS

estimator = MimiqEstimatorV2(MimiqBackend(QleoQCS()))

theta = Parameter("theta")
qc = QuantumCircuit(1)
qc.ry(theta, 0)

# <Z> sweeps from +1 to -1 as Ry rotates |0> to |1>.
result = estimator.run([(qc, SparsePauliOp("Z"),
                         [[0.0], [np.pi / 2], [np.pi]])]).result()[0]
print(np.round(result.data.evs, 12))      # [ 1.  0. -1.]
print(result.data.stds)                   # [0. 0. 0.] — exact, not sampled
```

Weighted sums work as expected, and land on Qleo's native Pauli-string
kernel rather than a dense matrix:

```python
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from mimiq_qiskit import MimiqBackend, MimiqEstimatorV2
from qleo import QleoQCS

estimator = MimiqEstimatorV2(MimiqBackend(QleoQCS()))

bell = QuantumCircuit(2)
bell.h(0)
bell.cx(0, 1)

op = SparsePauliOp(["ZZ", "XX", "YY", "II"], [1.0, 0.5, -0.25, 2.0])
print(estimator.run([(bell, op)]).result()[0].data.evs)      # 3.7500000000000004
```

Because Qleo declares the `expectation_paulistring` capability, a Pauli
term of any width is evaluated by the mask-based kernel in `O(2**n)` — the
cost is set by the state size, not by the length of the Pauli string. Give
the estimator circuits **without** final measurements; it needs the state,
not samples.

Qleo also declares `expectation_state`, which says it can be asked for a
term directly rather than through the circuit. `MimiqEstimatorV2` reads that
and takes the shorter route on a deterministic circuit: one evolution, then
one query per term, instead of one `ExpectationValue` operation per term
pushed onto the circuit and read back out of the z-register. Nothing changes
in what you write or in the numbers you get — only in how many operations are
built and walked to produce them, which is why it pays most where the terms
are many and the state is small. A circuit that ends in an ensemble (a
mid-circuit measurement, a reset, a noise channel) still needs an evolution
per trajectory and takes the portable route.

You can read the same values yourself, off a state you evolved:

```python
import mimiqcircuits as mc
from qleo import QleoQCS

sim = QleoQCS()

bell = mc.Circuit()
bell.push(mc.GateH(), 0)
bell.push(mc.GateCX(), 0, 1)

state = sim.build_state(2)
state, _fidelity = sim.evolve(state, sim.compile(bell))

# Char k of the string acts on the k-th qubit given, so this is <Z0 Z1>.
print(sim.expectation(state, mc.PauliString("ZZ"), 0, 1).real)   # 1.0000000000000002
print(sim.expectation(state, mc.PauliString("XX"), 0, 1).real)   # 1.0000000000000002
```

The state is left untouched, so one evolution answers as many terms as you
care to ask.

## Mid-circuit measurement and feed-forward

A measurement followed by a single conditional gate maps onto MIMIQ's
`IfStatement`, which puts Qleo into trajectory mode — each shot evolves a
fresh state:

```python
from qiskit import QuantumCircuit
from mimiq_qiskit import MimiqBackend
from qleo import QleoQCS

backend = MimiqBackend(QleoQCS(seed=11))

qc = QuantumCircuit(2, 2)
qc.h(0)
qc.measure(0, 0)
with qc.if_test((qc.clbits[0], 1)):
    qc.x(1)                     # flip qubit 1 only when qubit 0 read 1
qc.measure(1, 1)

# The two qubits are correlated through the classical bit, never anti-.
print(backend.run(qc, shots=400).result().get_counts())   # {'00': ~200, '11': ~200}
```

`reset` and `barrier` pass through too. Trajectory mode costs one full
evolution per shot, so keep `shots` modest on wide circuits.

## Reproducibility

Seeds reach Qleo's `Rng` unchanged, so a seeded run is bit-for-bit
repeatable:

```python
from qiskit import QuantumCircuit
from mimiq_qiskit import MimiqBackend
from qleo import QleoQCS

backend = MimiqBackend(QleoQCS())

qc = QuantumCircuit(3, 3)
qc.h([0, 1, 2])
qc.measure(range(3), range(3))

first = backend.run(qc, shots=300, seed=42).result().get_counts()
again = backend.run(qc, shots=300, seed=42).result().get_counts()
assert first == again
```

A per-call `seed=` overrides the instance seed given to
`QleoQCS(seed=...)`. With neither, every run draws fresh OS entropy.

## Conventions

Qiskit and MIMIQ order qubits differently in places, and the bridge
reconciles them so that **Qiskit semantics are what you get**:

- **Counts strings** follow Qiskit: the leftmost character is the
  highest-numbered clbit. Measuring qubit 2 of three into clbit 2 yields
  `'100'`.
- **Pauli labels** follow Qiskit: rightmost character is qubit 0.
  `SparsePauliOp("IZ")` is `Z` on qubit 0.
- **Matrices** for `UnitaryGate` follow Qiskit's little-endian wire order.
  The bridge converts to MIMIQ's convention on the way in.

Qleo's own low-level API keeps its native conventions, described in
[Getting Started](getting-started.md); they only matter if you bypass the
bridge and drive `QleoSV` yourself.

## What the bridge does not convert

These raise `UnsupportedGateError` with an actionable message rather than
producing a wrong answer:

| Construct | Why, and what to do |
| --- | --- |
| Conditional bodies with more than one gate | MIMIQ's `IfStatement` holds a single operation; split into consecutive conditionals. |
| `if_test` with an `else` branch | Express as two conditionals on complementary values. |
| Unbound `Parameter`s | Call `assign_parameters`, or pass bindings through a primitive pub. |
| `while_loop`, `for_loop`, `switch_case` | Not lowered; unroll them in Qiskit first. |

Ordinary gates are no longer a limit: anything outside the `Target` is
decomposed through its Qiskit `definition`, so `initialize`, open control
states, and blocks built with `QuantumCircuit.to_gate()` all convert.

Two further limits are worth knowing:

- **Global phase is dropped.** It changes no measurement statistic or
  expectation value, which is all this path computes.
- **Cloud-only run options are rejected**, with a `ValueError` naming the
  backend and the option (`bonddim`, `entdim`, `mpscutoff`, `timelimit`,
  `noisemodel`, `label`, …). The preparation flags — `fuse`,
  `fuse_threshold`, `canonicaldecompose`, `reorderqubits` — are forwarded
  to `QleoQCS.execute` and adjust its pipeline for that run, so
  `backend.run(qc, reorderqubits=False)` turns reordering off for one job.

Noise is a case of that last point: Qleo simulates noise well, but the
bridge has no Qiskit syntax for a MIMIQ noise model. To use it, build the
circuit with `mimiqcircuits` and call
[`QleoQCS.execute`](execute.md#noise) directly.

!!! note "Bridge version"

    This page describes **`mimiq-qiskit` 0.3.2 or later**, which the
    `qiskit` extra installs: it is the first release that works with
    `mimiqcircuits` 0.28. On 0.1.1 a `UnitaryGate` spanning two or more
    qubits was also applied with its wires reversed — wrong results, no error.

## Where to go next

- **[Circuit Execution](execute.md)** — the native path: noise, amplitudes,
  execution passes, and the knobs the bridge does not expose.
- **[API Reference](api.md)** — `QleoQCS` and the rest of the public
  surface.
- **[mimiq-qiskit documentation](https://docs.qperfect.io/mimiq-qiskit/)**
  — the bridge itself, including the MIMIQ cloud path.
