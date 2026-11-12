# Circuit Execution

The high-level way to run a circuit is `QleoQCS`, a simulator that
subclasses `mimiqcircuits.backends.LocalBackend`. You build a circuit with
`mimiqcircuits`, call `execute()`, and receive the same `QCSResults`
object MIMIQ uses everywhere else.

```python
import mimiqcircuits as mc
from qleo import QleoQCS

# Build a Bell-state circuit with measurements.
c = mc.Circuit()
c.push(mc.GateH(), 0)
c.push(mc.GateCX(), 0, 1)
c.push(mc.Measure(), 0, 0)
c.push(mc.Measure(), 1, 1)

sim = QleoQCS()
results = sim.execute(c, nsamples=1000)

print(results.histogram())          # e.g. {bs"00": 498, bs"11": 502}
print(results.fidelities[0])        # 1.0 — state-vector evolution is exact
print(results.timings)              # timing breakdown, e.g. apply / sample
```

## How it works

`QleoQCS.execute()` walks the `mimiqcircuits.Circuit` and dispatches
each instruction to the native `QleoSV` state vector:

1. **Dispatch** — every supported gate is applied natively. Named gates
   (`GateH`, `GateCX`, `GateRX`, …) hit specialised kernels; multi-controlled
   gates go through the direct multi-control path; anything else that is a
   1- or 2-qubit unitary falls back to a generic dense-matrix apply.
2. **Evolve** — the state vector is advanced instruction by instruction.
3. **Sample / measure** — measurement outcomes are collected into the
   classical registers and returned as `QCSResults`.

The simulator is exact per trajectory, so `results.fidelities` is always
`1.0`.

## Execution modes

`execute()` selects one of two modes automatically, based on circuit
content:

### Sampling mode

Used when every non-unitary instruction is a **trailing** measurement.
The state is evolved **once** and the final distribution is sampled
`nsamples` times — fast, because the expensive evolution happens only
once.

```python
import mimiqcircuits as mc
from qleo import QleoQCS

c = mc.Circuit()
c.push(mc.GateH(), 0)
c.push(mc.GateCX(), 0, 1)
c.push(mc.Measure(), 0, 0)
c.push(mc.Measure(), 1, 1)

results = QleoQCS().execute(c, nsamples=1000)
print(results.histogram())          # {bs"00": ~500, bs"11": ~500}
```

### Trajectory mode

Used when the circuit contains mid-circuit measurements, resets,
classically conditioned operations (`IfStatement`), or noise channels
(`krauschannel`). Each of the `nsamples` shots evolves a **fresh** state
through the whole circuit independently.

```python
import mimiqcircuits as mc
from qleo import QleoQCS

c = mc.Circuit()
c.push(mc.GateH(), 0)
c.push(mc.Measure(), 0, 0)          # mid-circuit measurement -> trajectory mode
c.push(mc.GateX(), 1)
c.push(mc.GateCX(), 1, 2)
c.push(mc.Measure(), 1, 1)
c.push(mc.Measure(), 2, 2)

results = QleoQCS().execute(c, nsamples=100)
print(len(results.fidelities))      # 100 — one per trajectory
```

## Reproducibility

`execute()` takes mutually exclusive `seed=` and `rng=` entropy sources;
pass at most one. With neither, the simulator's instance seed (set at
construction) is used, falling back to fresh OS entropy.

```python
from qleo import QleoQCS

# Reproducible from a per-call seed ...
results = QleoQCS().execute(c, nsamples=1000, seed=1234)

# ... or make the whole instance reproducible.
sim = QleoQCS(seed=1234)
results = sim.execute(c, nsamples=1000)
```

## Amplitudes and expectation values

Non-destructive observations are requested with in-circuit ops that write
into the results. An `Amplitude` op records a single basis-state amplitude
into `results.zstates`; an `ExpectationValue` op records `<psi|O|psi>`.

```python
import mimiqcircuits as mc
from qleo import QleoQCS

c = mc.Circuit()
c.push(mc.GateH(), 0)
c.push(mc.GateCX(), 0, 1)

# Record the amplitude of |00> into z-variable 0.
c.push(mc.Amplitude(mc.BitString("00")), 0)

results = QleoQCS().execute(c, nsamples=1)
print(results.zstates[0][0])        # (0.707..+0j)
```

`ExpectationValue` supports 1- and 2-qubit operators. For a Pauli-string
expectation on more than two qubits, drop to the low-level
[`QleoSV.expectation_pauli`](api.md) method on the state vector.

## Noise

Kraus and mixed-unitary channels (for example `Depolarizing`,
`PauliNoise`, `AmplitudeDamping`) are sampled per trajectory. Adding any
noise channel puts `execute()` into trajectory mode, so run enough
`nsamples` to gather ensemble statistics.

```python
import mimiqcircuits as mc
from qleo import QleoQCS

c = mc.Circuit()
c.push(mc.GateH(), 0)
c.push(mc.GateCX(), 0, 1)
c.push(mc.Depolarizing1(0.05), 0)   # 5% depolarising noise on qubit 0
c.push(mc.Measure(), 0, 0)
c.push(mc.Measure(), 1, 1)

results = QleoQCS().execute(c, nsamples=1000, seed=7)
print(len(results.cstates))         # 1000 — one measurement record per shot
print(list(results.cstates[0]))     # e.g. [0, 0] or [1, 1]
```

## Composite gates

`GateDecl` blocks — what `push_suzukitrotter`, `push_lietrotter` and the
`mimiq-openfermion` UCCSD builders emit — stand for a sub-circuit, not for a
matrix. So do `Block`, `Repeat`, `Parallel` and `PauliString`. Qleo expands
them into the gates they hold and runs those; nothing needs decomposing by
hand first:

```python
import mimiqcircuits as mc
from qleo import QleoQCS

h = mc.Hamiltonian()
h.push(1.0, mc.PauliString("ZZ"), 0, 1)
h.push(0.5, mc.PauliString("X"), 0)

c = mc.Circuit()
c.push(mc.GateH(), 0)
c.push_suzukitrotter(h, (0, 1), t=1.0, steps=2)   # three GateDecl blocks

results = QleoQCS().execute(c, nsamples=1000)
```

Expansion happens in the pipeline, as `QleoFlattenContainersPass` — the
first pass `execute()` runs. Doing it there rather than at apply time is what
lets gate fusion and qubit reordering see the real gates: on a 24-qubit
Trotter circuit that is worth about 2.9x. A container that escapes the pass
(a custom `passes=` pipeline that leaves it out) still expands when it is
applied, so results never depend on the pass being present.

## Qubit reordering

Gate throughput depends on which qubit indices a gate touches. Because the
backend is all-to-all, qubits can be relabelled exactly — no SWAP gates,
no approximation — to land gates on the fastest kernels. Results are mapped
back to your original qubit frame, so you see identical outcomes, just
faster.

This runs **by default** for circuits of 13 or more qubits, the point past
which the state vector outgrows the cache and the per-slot kernel-cost gap
starts to matter. It is the state-vector analogue of the `reorderqubits` flag
tensor-network backends use. With `dynamic_qubits=True` the default leaves it
out: first-touch slot assignment overrides the relabelling, so the search
would cost time and buy nothing.

Reordering is chosen per call, through `execute`:

```python
from qleo import QleoQCS

sim = QleoQCS()
sim.execute(c)                          # reorder wide circuits (the default)
sim.execute(c, reorderqubits=False)     # no reordering for this call
sim.execute(c, reorderqubits="sa")      # simulated-annealing search, any width
```

Every flag (`fuse`, `fuse_threshold`, `canonicaldecompose`, `reorderqubits`,
`reorderqubits_seed`) defaults to `None`, meaning "Qleo decides", and adjusts
the default pipeline rather than replacing it: `False` drops that pass, any
other value replaces it with Qleo's own pass of that kind, and the rest
stands. So `sim.execute(c, reorderqubits=False)` keeps flattening and fusion
and drops only the reorder.

The replacement is built by the backend, so a flag never swaps in a generic
pass. `fuse=True` keeps Qleo's block budgets, and `reorderqubits=True` or a
method name builds an `QleoReorderQubitsPass` that acts on any width, also
under `dynamic_qubits=True`. `QleoQCSGpu` has no reorder pass, so asking it
for one through the flag raises `NotImplementedError`.

For finer control, hand in an `QleoReorderQubitsPass` you configured
yourself, and turn off the default one so the circuit is not reordered twice:

```python
import mimiqcircuits as mc
from mimiqcircuits.backends import PassPipeline
from qleo import QleoQCS, QleoReorderQubitsPass

sim = QleoQCS()
# Only reorder circuits of 20+ qubits, with a fixed seed for the search.
mine = QleoReorderQubitsPass(method="sa", seed=7, qubit_threshold=20)
results = sim.execute(c, nsamples=1000, reorderqubits=False,
                      passes=PassPipeline([mine]))
```

Passes given that way are appended after Qleo's own, as given; nothing is
deduplicated. An empty `PassPipeline()` appends nothing: preparing a circuit
with nothing at all means setting every flag to `False`, and container
flattening still runs, since it is structural and no flag names it.

## Driving evolution manually

For incremental control, use the module-level `evolve` and
`apply_instruction` helpers on an `QleoState`. This is the same
machinery `execute()` drives internally.

```python
import mimiqcircuits as mc
from qleo import QleoState, evolve, Rng

c = mc.Circuit()
c.push(mc.GateH(), 0)
c.push(mc.GateCX(), 0, 1)

state = QleoState.zero(num_qubits=2)
state, fidelity = evolve(state, c, rng=Rng(seed=42))
print(state.q.amplitudes())         # the underlying QleoSV amplitudes
```

See the [API Reference](api.md) for the full signatures.
