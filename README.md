# Py-V: A Cycle-accurate RISC-V CPU Simulator written in Python
🚧 This README is still under construction 🚧

Py-V is a cycle-accurate simulator for RISC-V CPUs. Py-V is written purely in Python.

Why Py-V?
- Yes, it won't be performant
- But:
    - It's not just a binary simulator (like Spike or similar): Simulator and CPU model are the _same_
        - (I will explain what "same" means here in the future!)
    - Cycle-accurate
    - Helps to learn about CPU architecture
        - Like a real hardware design, the CPUs are made from different modules that are connected with each other
    - Python makes writing core models faster
- I am doing this more as an experiment, to design an easy to use _hardware description language_ (HDL) where the simulator is inherently linked to the design.
    - A CPU was an obvious choice to test this idea
    - However, my goal is totally different from existing solutions, such as [MyHDL](https://www.myhdl.org/)
        - I have not even planned yet on how to convert a Py-V model into Verilog/VHDL, but that might be something interesting for the future

## Core models
As of now, there are the following core models:

- Classic 5-stage RISC CPU (`SingleCycle`)
    - Single-cycle
    - 8 KiB memory
    - Pipelined version planned

## Running a test program
**Prerequisites**:
* RISC-V toolchain
* python3

First, navigate to the `programs` directory, and compile the programs:
```
make
```

Then, navigate to the `pyv` directory, and start the simulation by running:
```
python3 pyv.py
```
By default, this will simulate the `fibonacci` and `loop_acc` test programs. The output should look something like this:
```
$ python3 pyv.py                                                                  
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

### Adding custom programs
You can add your own programs by following the examples in `programs/`. To simulate, refer to `pyv/pyv.py` to see how the example programs are run. I know that having a command line interface here would be nice, but I didn't have time to implement that, but it's definitely on my wishlist!

## Feature wishlist
Unordered (and probably incomplete) list of things I plan to integrate in the (near) future:

- [ ] Pipelined core model
- [ ] Exceptions
- [ ] Branch predictor
- [ ] Caches
- [ ] Logging capabilities
- [ ] ...

---

## Under the hood
This section is intended to explain how Py-V (and the language behind it) works internally. 🚧 I am still working on a proper documentation for Py-V, so currently there is no ETA on when this section will be finished.   



### Source files
`pyv/`. This is where the source files of Py-V are located.
* `isa.py`: Contains definitions for RISC-V ISA (opcodes, etc.)
* `mem.py`: Contains a simple behavioral memory model
* `models.py`: In this file, the different core models are defined
    * Currently only `SingleCycle`
* `module.py`: Abstract base class for all modules
* `port.py`: Contains definitions for ports
    * Currently: single value `Port` and bus/interface `PortX`
* `pyv.py`: Main file
    * Currently runs simulation using example binaries
* `reg.py`: Contains definitions for register modules
    * Also defines register file
* `stages.py`: Module definitions for the various pipeline stages
* `util.py`: Contains helper functions, and variables/constants

`test/`. Here you can find [pytest](pytest.org)-based unit tests.

`programs/`. This directory contains test programs that can be compiled, and later executed on a core model.
* `common/`: Common source files needed for compiling
* `fibonacci/`: A non-recursive version of the Fibonacci algorithm.
* `loop_acc/`: An assembly program that counts from 0 to 1000.

`doc/`. Contains documentation resources.