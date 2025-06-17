Statistical Operations
======================

Statistical operations are simulator specific mathematical operations allowing
you to compute properties of the simulated quantum state without making it
collapse.

All statistical operations will result in a real or complex number that will be
stored in the Z-Register, and can be accessed from the results of the
simulation through the `zstates` option, see :doc:`circuits` page.

On this page you will find all statistical operations available on QLEO with
explanations and examples.

Contents
========
.. contents::
   :local:
   :depth: 2
   :backlinks: entry


.. doctest:: statistical_op
    :hide:

    >>> from qleo import *
    >>> import numpy as np
    >>> import os
    >>> import math
    <BLANKLINE>


Expectation value
----------------------------------------------------

Mathematical definition
"""""""""""""""""""""""""""

An expectation value for a pure state :math:`| \psi \rangle` is defined as

.. math::

    \langle O \rangle = \langle \psi | O | \psi \rangle

where :math:`O` is an operator. With respect to a density matrix :math:`\rho` it's given by

.. math::

    \langle O \rangle = \mathrm{Tr}(\rho O).


Usage on QLEO
"""""""""""""

First we need to define the operator :math:`O` of which we will compute the expectation value

.. doctest:: python

    >>> op = SigmaPlus()



:class:`~qleo.SigmaPlus` is only one of the many operators available. Of course, every gate can be used as an operator, for example `op = GateZ()`.
However, QLEO also supports many non-unitary operators such as :class:`~qleo.SigmaPlus`, more about this on the :ref:`Operators` page.


To ask QLEO to compute the expectation value for a circuit you can create an :class:`~qleo.ExpectationValue` object and :meth:`~qleo.Circuit.push` it to the circuit like this:

.. doctest:: python

    >>> circuit = Circuit() 
    >>> circuit.push(GateH(), 0)
    1-qubit circuit with 1 instructions:
    └── H @ q[0]
    <BLANKLINE>

    >>> # Ask to compute the expectation value
    >>> ev = ExpectationValue(op)
    >>> circuit.push(ev, 0, 0)
    1-qubit circuit with 2 instructions:
    ├── H @ q[0]
    └── ⟨SigmaPlus(1)⟩ @ q[0], z[0]
    <BLANKLINE>



| As for all statistical operations, the arguments to give to the :meth:`~qleo.Circuit.push` function always follow the order of quantum register index first, classical register second (none in this case), and Z-register index last.
| In the example above, the first ``0`` is the index for the first qubit of the quantum register and the second ``0`` is the index of the Z-Register.

Notice that the expectation value will be computed with respect to the quantum state of the system at the point in the circuit where the :class:`~qleo.ExpectationValue` is added.


Amplitude
----------------------------------------------------

| With QLEO you can extract quantum state amplitudes in the computational basis at any point in the circuit using :class:`~qleo.Amplitude`.
| You will need to give the :class:`~qleo.Amplitude` function the :class:`~qleo.BitString` matching the state for which you want the amplitude.
| For more information on :class:`~qleo.BitString` check the :ref:`BitString <BitString>` documentation page.

You can add the :class:`~qleo.Amplitude` object to the circuit exactly like any other gate:

.. doctest:: python

    >>> mystery_circuit = Circuit() 
    >>> mystery_circuit.push(GateH(), range(0, 3)) 
    3-qubit circuit with 3 instructions:
    ├── H @ q[0]
    ├── H @ q[1]
    └── H @ q[2]
    <BLANKLINE>

    >>> # Define the Amplitude operator
    >>> amp = Amplitude(BitString("101"))

    >>> # Add the amplitude operator to the circuit and write the result in the first complex number of the Z-Register
    >>> mystery_circuit.push(amp, 0)
    3-qubit circuit with 4 instructions:
    ├── H @ q[0]
    ├── H @ q[1]
    ├── H @ q[2]
    └── Amplitude(bs"101") @ z[0]
    <BLANKLINE>


This will extract the amplitude of the basis state :math:`\ket{101}`. When adding the amplitude operation you do not need to give it any specific qubit target, the only index needed is for the Z-register to use for storing the result.
