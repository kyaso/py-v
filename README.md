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
- I am doing this more as an experiment, to design an easy to use "hardware prototyping framework" with an integrated simulator
  - A CPU was an obvious choice to test this idea
  - Py-V can be used for _rapid prototyping_: High-level design flexibility by leveraging the language features of Python, with the possibility to go as low-level as Verilog/VHDL
    - Similar projects are [PyRTL](https://ucsbarchlab.github.io/PyRTL/), [MyHDL](https://www.myhdl.org/), [nMigen](https://github.com/m-labs/nmigen), and [PyMTL](https://github.com/pymtl/pymtl3)
  - I have not yet planned on how to convert a Py-V model into Verilog/VHDL, but that might be something interesting for the future
  - Once the hardware modelling framework behind Py-V is mature enough, I am planning to put it into a separate library, and Py-V will just use the new library.
    - For now, if you want to use the library to design your own systems, the easiest way to get started is to just clone this repo

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
  - Partial support implemented
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

On the other hand, you can have a look into the source code as I tried to reduce complexity as much as possible, so the code should be almost self-documenting (otherwise please let me know!).

### Source files

`pyv/`. This is the package where the source files of Py-V are located.

- `clocked.py`: Contains base definitions of all clocked elements (e.g., memories, registers)
- `defines.py`: Contains common definitions, constants, etc.
- `isa.py`: Contains definitions for RISC-V ISA (opcodes, etc.)
- `log.py`: Contains a basic logger
- `mem.py`: Contains a simple behavioral memory model
- `models/`: Contains different core models
  - `model.py`: Base class for core models
  - `singlecycle.py`: A basic 5-stage single-cycle RISC-V CPU
- `module.py`: Abstract base class for all modules
- `port.py`: Contains definitions for ports (Inputs, Outputs, Wires)
- `reg.py`: Contains definitions for registers
  - Also defines register file
- `simulator.py`: Contains the simulator
- `stages.py`: Module definitions for the various pipeline stages
- `util.py`: Contains helper functions, and variables/constants

`test/`. Here you can find [pytest](pytest.org)-based unit tests.

`programs/`. This directory contains test programs that can be compiled, and later executed on a core model.

- `common/`: Common source files needed for compiling
- `endless_loop/`: As the name suggests
  - Execution time is limited in `main.py` (see below)
- `fibonacci/`: A non-recursive version of the Fibonacci algorithm.
- `loop_acc/`: An assembly program that counts from 0 to 1000.

`main.py`. Main execution file

- Runs simulation using compiled binaries from `programs/`

`doc/`. Contains documentation resources.
