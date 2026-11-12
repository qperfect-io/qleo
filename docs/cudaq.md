# CUDA-Q Interoperability

Qleo runs [CUDA-Q](https://nvidia.github.io/cuda-quantum/) kernels as a
native **NVQIR simulator backend**, so `cudaq.sample`, `cudaq.observe`,
`cudaq.run` and `cudaq.get_state` all execute on the Qleo state-vector
core:

```python
import cudaq

cudaq.set_target("qleo")

@cudaq.kernel
def ghz(qubit_count: int):
    q = cudaq.qvector(qubit_count)
    h(q[0])
    for i in range(qubit_count - 1):
        x.ctrl(q[i], q[i + 1])
    mz(q)

print(cudaq.sample(ghz, 24, shots_count=1000))
```

GHZ on 24 qubits, 1000 shots: **0.52 s against 20.8 s** on CUDA-Q's own
`qpp-cpu` simulator.

A second target, `qleo_gpu`, runs the same operation set on Qleo's GPU
engine (cuStateVec) instead:

```python
import qleo  # before set_target("qleo_gpu") — see the note below
import cudaq

cudaq.set_target("qleo_gpu")
print(cudaq.sample(ghz, 24, shots_count=1000))
```

## Enabling the target

CUDA-Q discovers simulators by name *inside its own installation* and
offers no plugin search path, so the backend has to be copied there. That
is one command, once per environment:

```bash
pip install cudaq          # if you do not have it already
qleo cudaq install
```

`install` copies up to six files into the CUDA-Q installation — the CPU
backend always, the GPU backend if this copy of Qleo was built with one
(see the platform note below):

| File | Destination | Role |
|---|---|---|
| `libnvqir-qleo.so` | `<install>/lib/` | the CPU NVQIR backend |
| `libexaqt.so` | `<install>/lib/` | the CPU simulation engine it links |
| `qleo.yml` | `<install>/targets/` | the CPU target config |
| `libnvqir-qleo_gpu.so` | `<install>/lib/` | the GPU NVQIR backend |
| `libexaqt_gpu.so` | `<install>/lib/` | the GPU simulation engine it links |
| `qleo_gpu.yml` | `<install>/targets/` | the GPU target config |

`<install>` is the directory holding CUDA-Q's own `lib/` and `targets/`:
site-packages for the `cudaq` wheel, or `$CUDA_QUANTUM_PATH` (typically
`/opt/nvidia/cudaq`) for a system-wide install. Set that variable to
choose explicitly when you have both.

Two more commands round it out:

```bash
qleo cudaq status       # report which files are in place
qleo cudaq uninstall    # remove them again
```

The functions behind them are available as [`qleo.cudaq`](api.md) if you
would rather drive the install from Python.

!!! note "Linux x86-64 only"

    Both backends are compiled shared libraries, and they ship only in
    the Linux x86-64 wheel. On macOS, Windows and other architectures pip
    installs the pure-Python wheel, where `qleo cudaq install` reports
    that there is nothing to install. Everything else about Qleo works
    normally on those platforms.

!!! note "GPU: install with the `[gpu]` extra, and import qleo first"

    `qleo_gpu` additionally needs CUDA and cuStateVec loadable in the
    process, and `cudaq.set_target("qleo_gpu")` does not look for them
    itself — install with `pip install qleo[gpu]` and make sure
    `import qleo` (or `import exaqt`) runs *before* `set_target`, which is
    what makes those libraries resident. `qleo.ExaqtQCSGpu` already
    relies on the same preload, so if that already works in your
    environment, `qleo_gpu` will too. `cudaq.get_targets()` reports
    `qleo_gpu` as unavailable (rather than failing on first use) on a
    host with no GPU.

## Supported operations

Identical on both targets — `qleo_gpu` is not a reduced version of
`qleo`, it is the same operation set on a different engine:

|  |  |
|---|---|
| 1-qubit gates | all, including `u3` and custom unitaries |
| 2-qubit gates | all, including custom unitaries |
| 3–5 qubit custom unitaries | applied natively |
| controlled gates | any number of controls on 1- or 2-qubit targets |
| measurement | mid-circuit, reset, measurement feed-forward |
| `observe` | exact, from the engine's Pauli-string kernel — not sampled |
| `get_state` | full state vector (fp64) |

Anything wider — a custom unitary on more than 5 qubits, or a controlled
gate with more than 2 targets — raises a `RuntimeError` naming the
operation rather than silently producing a wrong answer.

**Noise channels are not wired up.** A CUDA-Q noise model is ignored,
with the warning CUDA-Q prints for any simulator that does not accept
one — the same behaviour as its own `qpp` state-vector target, where
noise needs `density-matrix-cpu` instead. The engine does have Kraus and
mixed-unitary channels, so this is missing plumbing rather than a limit
of the simulator — true of both `qleo` and `qleo_gpu`.

The old `QleoGPU` target, which went through a different C++ GPU core
and a Python-only engine binding, is unrelated history — `qleo_gpu` is a
fresh integration against the engine's GPU state-vector core, not a
revival of that path.

## Version coupling

The NVQIR plugin ABI is not stable across CUDA-Q releases, nor even across
post releases. Both backends are built and tested against **CUDA-Q
0.16.0.post1**, which is what `pip install cudaq` installs; any other
version, 0.16.0 included, may install cleanly and then crash when a kernel
runs. If `cudaq.set_target("qleo")` or `cudaq.set_target("qleo_gpu")`
errors after a CUDA-Q upgrade, run `qleo cudaq install` again from a Qleo
built against the matching series.
