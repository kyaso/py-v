# Py-V: A Cycle-accurate RISC-V CPU Simulator written in Python

<p align="center">
    <img src="https://img.shields.io/github/v/tag/kyaso/py-v">
    <img src="https://img.shields.io/github/license/kyaso/py-v">
</p>

Py-V is a cycle-accurate simulator for RISC-V CPUs. Py-V is written purely in Python.

## Why Py-V?

- Yes, it won't be performant
- But:
  - It's not just a binary simulator: it implements an actual CPU down to _register-transfer level_ (RTL)
  - Cycle-accurate
  - Helps to learn about CPU architecture
    - Like a real hardware design, the CPUs are made from different modules that are connected with each other
  - Python makes writing core models faster
- I am doing this more as an experiment, to design an easy to use _hardware prototyping framework_ (HPF) with an integrated simulator
  - A CPU was an obvious choice to test this idea
  - Py-V is intended for _rapid prototyping_: High-level design flexibility by leveraging the language features of Python, with the possibility to go as low-level as Verilog/VHDL
    - Similar projects are [MyHDL](https://www.myhdl.org/), [nMigen](https://github.com/m-labs/nmigen) and [PyMTL](https://github.com/pymtl/pymtl3)
  - I have not yet planned on how to convert a Py-V model into Verilog/VHDL, but that might be something interesting for the future
  - Once the hardware modelling framework behind Py-V is mature enough, I will put it into a separate library, and Py-V will just use the new library.

## Core models

As of now, there are the following core models:

- Classic 5-stage RISC CPU (`SingleCycle`)
  - Single-cycle
  - 8 KiB memory
  - Pipelined version planned

## Running a test program

**Prerequisites**:

- RISC-V toolchain
- python3

First, navigate to the `programs` directory, and compile the programs:

```
make
```

Then, navigate back to the top-level directory, and start the simulation by running:

```
python3 main.py
```

By default, this will simulate the `fibonacci` and `loop_acc` test programs. The output should look something like this:

```
$ python3 main.py
===== LOOP_ACC =====
* Creating core instance...
* Loading binary...
* Starting simulation...

Simulation done at cycle 3000 after 0.11450981599773513s.

x1 = 1000
x2 = 1000
x5 = 4096
pc = 0x20
mem@4096 =  ['0xe8', '0x3', '0x0', '0x0']

===== FIBONACCI =====
* Creating core instance...
* Loading binary...
* Starting simulation...

Simulation done at cycle 3000 after 0.12019554300059099s.

Result =  ['0x37', '0x0', '0x0', '0x0']
```

_Note_: The simulation times can vary from machine to machine. Also, in the meantime (as of Jan 2022), I added logging which could additionally slow down the simulation. There still some work to do when it comes to runtime optimiztions!

### Adding custom programs

You can add your own programs by following the examples in `programs/`. To simulate, refer to `main.py` to see how the example programs are run. I know that having a command line interface here would be nice, but I didn't have time to implement that, but it's definitely on my wishlist!

## Feature wishlist

Unordered (and probably incomplete) list of things I plan to integrate in the (near) future:

- [ ] Pipelined core model
- [ ] Exceptions
- [ ] Branch predictor
- [ ] Caches
- [ ] Logging capabilities
  - Partially implemented already!
- [ ] ...

## API documentation

➔ https://kyaso.github.io/py-v/.

---

## Under the hood

This section is intended to explain how Py-V (and the language behind it) works internally. 🚧 I am still working on a proper documentation for Py-V, so currently there is no ETA on when this section will be finished.

- Modules
- Ports
  - Connections
- process method
- Registers
- Simulation
  - topological sort
  - How to deal with issues when bi-directional data exchange in same cycle

### Ports

Like in any HDL, a module can have an arbitrary number of input and/or output ports. Ports of different modules can be connected using the `connect()` method. For simulation purposes it is sufficient to know for each port who it's driver (another port) is. [[8op3ac]]

### Process method

Each module has to implement a `process()` method. The `process` method is where the behavior of the _combinatorial_ part of the module is described.

### Source files

`pyv/`. This is the package where the source files of Py-V are located.

- `clocked.py`: Contains base definitions of all clocked elements (e.g., memories, registers)
- `defines.py`: Contains common definitions, constants, etc.
- `isa.py`: Contains definitions for RISC-V ISA (opcodes, etc.)
- `log.py`: Contains a basic logger
- `mem.py`: Contains a simple behavioral memory model
- `models/`: Contains different core models
  - `model.py`: Base class for core models
- `module.py`: Abstract base class for all modules
- `port.py`: Contains definitions for ports
  - Currently: single value `Port` and bus/interface `PortX`
- `reg.py`: Contains definitions for register modules
  - Also defines register file
- `simulator.py`: Contains the simulator
- `stages.py`: Module definitions for the various pipeline stages
- `util.py`: Contains helper functions, and variables/constants

`test/`. Here you can find [pytest](pytest.org)-based unit tests.

`programs/`. This directory contains test programs that can be compiled, and later executed on a core model.

- `common/`: Common source files needed for compiling
- `fibonacci/`: A non-recursive version of the Fibonacci algorithm.
- `loop_acc/`: An assembly program that counts from 0 to 1000.

`main.py`. Main execution file

- Currently runs simulation using example binaries

`doc/`. Contains documentation resources.
