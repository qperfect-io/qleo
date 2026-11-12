"""Qleo is a rebranding of the engine, so the API must match name-for-name.

If the engine grows or renames a public name, this fails until `qleo`
re-exports it too.
"""

import exaqt
import mimiqcircuits as mc

import qleo


def _brand(name: str) -> str:
    return name.replace("Exaqt", "Qleo")


def test_public_api_matches_engine():
    # Qleo adds one thing to the engine's API: the circuit API, re-exported
    # so `from qleo import *` is enough to build and run a circuit.
    assert set(qleo.__all__) == {_brand(n) for n in exaqt.__all__} | set(mc.__all__)


def test_star_import_brings_in_the_circuit_api():
    ns = {}
    exec("from qleo import *", ns)
    assert ns["Circuit"] is mc.Circuit
    assert ns["GateH"] is mc.GateH
    assert ns["QleoQCS"] is qleo.QleoQCS


def test_exported_names_are_the_engine_objects():
    for name in exaqt.__all__:
        if name == "__version__":
            continue
        engine = getattr(exaqt, name)
        branded = getattr(qleo, _brand(name))
        # The simulator classes are branded subclasses (they report
        # "Qleo" / "QleoGpu" in QCSResults); docs_dir is Qleo's own, pointing at the
        # docs bundled in this wheel. Everything else is the engine
        # object itself, not a copy of it.
        if name in ("ExaqtQCS", "ExaqtQCSGpu"):
            assert issubclass(branded, engine)
        elif name == "docs_dir":
            assert callable(branded)
        else:
            assert branded is engine


def test_results_are_branded():
    c = mc.Circuit()
    c.push(mc.GateH(), 0)
    c.push(mc.Measure(), 0, 0)

    res = qleo.QleoQCS(seed=1).execute(c, nsamples=10)
    assert res.simulator == "Qleo"
    assert res.version == qleo.__version__


def test_execute_runs_a_circuit():
    c = mc.Circuit()
    c.push(mc.GateH(), 0)
    c.push(mc.GateCX(), 0, 1)
    c.push(mc.Measure(), 0, 0)
    c.push(mc.Measure(), 1, 1)

    res = qleo.QleoQCS(seed=1).execute(c, nsamples=100)
    assert set(res.histogram()) <= {mc.BitString("00"), mc.BitString("11")}


if __name__ == "__main__":
    test_public_api_matches_engine()
    test_star_import_brings_in_the_circuit_api()
    test_exported_names_are_the_engine_objects()
    test_results_are_branded()
    test_execute_runs_a_circuit()
    print("ok")
