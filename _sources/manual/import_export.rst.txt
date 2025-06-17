
Import and export circuits
==============================

.. doctest:: import_export

    from qleo import *

In this section we introduce different options to import and export circuits.
In particular, **QLEO (by MIMIQ)** allows to import circuits in well-known languages such as OpenQASM and Stim, as well as save and import circuits using its own Protobuf structure.

Contents
========
.. contents::
   :local:
   :depth: 2
   :backlinks: entry

Protobuf
-----------------

Export Protobuf files
~~~~~~~~~~~~~~~~~~~~~

After building a circuit, you can export it into a Protobuf format using the :func:`~qleo.Circuit.saveproto` function. You need to give it two arguments, the name of the file to create (`.pb` format) and the circuit to save.

.. doctest:: import_export

    results.saveproto("my_circuit.pb")


The same method allows you to save your simulation results in a Protobuf file.

.. doctest:: import_export

    # get the results
    results = conn.get_results(job)
    # save the results
    results.saveproto("my_results.pb")

.. note::

    Protobuf is a serialized file format developed by google. It is very lightweight and efficient to parse. Check the  `Protobuf repository <https://github.com/protocolbuffers/protobuf>`_` for more information.

.. note::

    You can only export a circuit into Protobuf format and cannot export an OpenQASM file in the current version of the framework..


Import Protobuf files
~~~~~~~~~~~~~~~~~~~~~

You can import MIMIQ's Protobuf circuit files using the :func:`~qleo.Circuit.loadproto` function and import Protobuf results file using :func:`~qleo.QCSResults.loadproto`.
With this function you can get previously saved circuit or get previous simulation results.
You need to give this function the name of the file to parse and the type of object to parse.

.. doctest:: import_export


    # Import circuit from Protobuf
    circuit = Circuit.loadproto("my_circuit.pb")

    # Import results from Protobuf
    results = QCSResults.loadproto("my_results.pb")

The circuit imported with :meth:`~qleo.Circuit.loadproto` can be manipulated like any other circuit. To add or insert gates, see :doc:`circuit <circuits>` page.

OpenQASM
-----------------

Open Quantum Assembly Language is a programming language designed for describing quantum circuits and algorithms for execution on quantum computers. It is a very convenient middle ground for different quantum computer architectures to interpret and execute circuits.

Execute OpenQASM files
~~~~~~~~~~~~~~~~~~~~~~

The `~qleo.Qleo` can process and execute OpenQASM files, thanks to fast and feature-complete C++ parsers and interpreters.

Here is a simple comprehensive example of executing a QASM file.


.. doctest:: import_export
    :hide:

    >>> from qleo import *
    >>> import os

.. doctest:: import_export

    >>> qasm = """
    ... // Implementation of Deutsch algorithm with two qubits for f(x)=x
    ... // taken from https://github.com/pnnl/QASMBench/blob/master/small/deutsch_n2/deutsch_n2.qasm
    ... OPENQASM 2.0;
    ... include "qelib1.inc";
    ... qreg q[2];
    ... creg c[2];
    ... x q[1];
    ... h q[0];
    ... h q[1];
    ... cx q[0],q[1];
    ... h q[0];
    ... measure q[0] -> c[0];
    ... measure q[1] -> c[1];
    ... """

    # Write the OPENQASM as a file
    >>> with open("/tmp/deutsch_n2.qasm", "w") as file:
    ...     file.write(qasm)
    308

    # actual execution of the QASM file
    >>> res = Q().execute("/tmp/deutsch_n2.qasm")
    >>> res.histogram()
    {frozenbitarray('10'): 530, frozenbitarray('11'): 470}
    >>> from qleo.visualization import *

    # Visualizing the result
    >>> plothistogram(res)
    <Figure size 960x720 with 1 Axes>

The result will be plotted as follows:

.. image:: ../manual/hist2.png
   :alt: Alternative Text

For more informations, read the documentation of :meth:`~qleo.MimiqConnection.execute`.

Behaviour of include files
^^^^^^^^^^^^^^^^^^^^^^^^^^

A common file used by many QASM files is the `qelib1.inc` file.
This file is not defined as being part of OpenQASM 2.0, but its usage is so widespread that it might be considered as de-facto part of the specifications.

.. admonition:: details

    We remind the careful reader that OpenQASM 2.0 specifications only define 6 operations:
    `U`, `CX`, `measure`, `reset`, `barrier` and `if`.

If we were to parse every file together with `qelib1.inc`, we would have at the end just a list of simple `U` and `CX` gates, leaving behind any speed improvement that we would gain by using more complex gates as blocks. For this reason, if you don't explicitly provide the include files, the `~qleo.Qleo` will not parse the usual `qelib1.inc` file but will instead use a simplified version of it, where almost all gate definitions are replaced by `opaque` definitions. These opaque definitions will be converted to the corresponding gates listed in :meth:`~qleo.Circuit.`GATES`.

Another alternative is to use the `mimiqlib.inc` directly in your file. For now it's almost a copy of the modified `qelib1.inc` but in the future it will be extended to contain more gates and operations, diverging from `qelib1.inc`.


Relations between OpenQASM registers and indices
------------------------------------------------------

During the parsing of the QASM file, we will assign a unique index to each qubit
and classical bit. This index will be used to identify the qubit or bit in the
algorithms or simulations.

The indices are assigned in the following way:

- The first qubit is assigned index `0` (Python), the second `1`, and so on.
- All registers retain the same ordering as in the QASM file.
- Qubits and classical bits behave similarly but have they have each other its
  own sequence from indices, starting from `0`.

A simple example will clarify this behaviour:

.. code::

    OPENQASM 2.0;
    qreg q[2];
    creg m[10];
    qreg a[10];
    creg g[2];

Will be parsed as:

========= =========== =========
QASM name Qubit index Bit index
========= =========== =========
``q[0]``  ``0``
``q[1]``  ``1``
``a[0]``  ``2``
``a[1]``  ``3``
…         …           …
``a[9]``  ``11``
``m[0]``              ``0``
``m[1]``              ``1``
…         …           …
``m[9]``              ``0``
``g[0]``              ``10``
``g[1]``              ``11``
========= =========== =========

