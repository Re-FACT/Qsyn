# Quality synthesis framework (Qsyn) for eFPGA netlists

Version: see [`VERSION.md`](VERSION.md)

Qsyn is a python-based general-purpose eFPGA netlist synthesis framework.
Qsyn is to solve a fundeme0ntal problem: netlist synthesis methodology for eFPGAs is different than ASICs.

- eFPGA netlists consist of repeatable tiles and subblocks, being highly hierachical
- eFPGA does not have a specific critical path but all the paths should be treated equivalently
Therefore, netlist synthesis should be performed in a hierachical way so that uniform timing can be ensured for all the tiles and subblocks.

Qsyn is the one-stop solution to run synthesis tasks for a complete eFPGA fabric hierarchically and report the result.

Qsyn supports both commercial and open-source simulators

- Yosys
- Synopsys Design Compiler

## Documentation

Full documentatation can be found [here](https://qsyn.readthedocs-io/en/latest//)

## Developer Guidelines

Please read the [contributor_guidelines](https://qsyn.readthedocs.io/en/latest/developer/contributor_guidelines/) if you would like to contribute to the project.
