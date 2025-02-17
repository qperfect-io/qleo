Simulating Circuits
===================

This page provides information on how **QLEO (by MIMIQ)** simulates quantum circuits.

Contents
========
.. contents::
   :local:
   :depth: 2
   :backlinks: entry

State Vector
------------
.. _state-vector:

The pure quantum state of a system of `N` qubits can be represented exactly by `2N` 
complex numbers. The state vector method consists in explicitly storing the full state of the system and 
evolving it exactly as described by the given quantum algorithm. The method can be considered **exact** up to 
machine precision errors (due to the finite representation of complex numbers on a computer). 
Since every added qubit doubles the size of the state, this method is practically impossible to 
be used on systems > 50 qubits. On a laptop with 8GB of free RAM, only 28-29 qubits can be simulated.

On our current remote service, we can simulate circuits 
of up to 32 qubits with this method. Premium plans and on-premises solutions are designed to 
increase this limit. If you are interested, contact us at contact@qperfect.io.

Our state vector simulator is highly optimized for simulation on a single CPU, 
delivering a significant speedup with respect to publicly available alternatives.

**Performance Tips:**

The efficiency of the state vector simulator can depend on the specific way that the circuit is implemented. 
Specifically, it depends on how gates are defined by the user. The most important thing is to 
avoid using [:class:`~qleo.GateCustom`] whenever possible, and instead use specific gate 
implementations. For example, use :class:`~qleo.GateX` instead of `GateCustom(Matrix([[0,1], [1,0]]))`, 
and use `CU(...)` instead of `GateCustom(matrix_of_GateCU)`.


Understanding Sampling
----------------------
.. _understanding-sampling:

When running a circuit with **QLEO**** we compute and return measurement samples, among other quantities (see :doc:`Cloaud Execution </manual/remote_execution>` section). Which measurement samples are returned depends on the type of circuit 
executed. There are three fundamental cases based on the presence of 
:doc:`non-unitary operations </manual/non_unitary_ops>` such as measurements (:class:`~qleo.Measure`...), resets (:class:`~qleo.Reset`...), if statements (:class:`~qleo.IfStatement`), or :doc:`noise </manual/noise>`.

**No Non-Unitary Operations**

In this case the circuit is executed only once and the final state is sampled as many times as specified by the  number of samples (`nsamples`) parameter of the execution. The sampled value of all the qubits is returned (in the obvious ordering).

**No Mid-Circuit Measurements or Non-Unitary Operations**

In this case the circuit is executed only once again, and the final state is sampled as many times as specified by `nsamples`, but only 
the sampled value of all the classical bits used in the circuit is returned (usually the targets of the measurements at the end of the circuit).

**Mid-Circuit Measurements or Non-Unitary Operations**

In this case the circuit is executed `nsamples` times, and the final state is sampled only once per run. The sampled value of all the classical bits used in the circuit is returned.
