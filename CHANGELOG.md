# Next version

- **Simulator**: The simulator can now handle the initialization of objects
  - Simply add modules (or any other `PyVObj`) via the new `Simulator.addObj()`
    method
  - Before running the simulation, call the new `Simulator.init()` method to
    initialize the registered modules/objects


# 0.5.0

- **NEW**: Added **ECALL** and **MRET** instructions (#31)
  - Currently, `mret` only sets `pc` to what is stored in `mepc`. It does
    not do anything else. This is not fully compliant to section 3.1.6.1,
    priv. spec. If needed in the future, the missing logic can be added.
- **NEW**: Added **VArray**, **VMap**, and **VContainer** structures.
  - VArray: Groups PyVObj instances in a list-like manner.
  - VMap: Groups PyVObj instances in a dictionary-like manner.
  - These structures wrap around Python's `list` and `dict`, respectively, to ensure proper initialization of elements during simulation initialization.
  - Elements can be accessed using the usual indexing and key access operators.
  - VContainer: Groups PyVObj instances in a class-like manner.
    - Elements are just class members
- **Module**: Removed `process()` method default implemenation from class
  - The port sensitivity list API is not affected by this
- **Registers**: It is now possible to assign sensitive methods to a register output
- **Tests**
  - Added a module `test_utils` which will contain useful utility stuff for writing tests
    - Currently, it has a function `check_port` that can be used to assert the existence and the type of a port


# 0.4.0

- **NEW**: Added **CSR** instructions
  - Basic logic for CSR is implemented
  - Currently, only `misa`, but adding more CSRs is easy
- **NEW**: Added "**on stable**" mechanism
  - How it works: During the current cycle, once all signal values have
    stabilized and _before_ the next clock tick, the simulator will execute all
    registered "on stable" callbacks
  - Callback methods can be registered during module definition, or directly
    in the simulator (see API docs)
  - This is useful if you need to do something but require absolute certainty
    that signal values won't toggle anymore during the current cycle
      - E.g., emitting an event based on the state of certain wires
- **Port**: Sensitive methods will now be added to the simulation queue on Port init
  - This ensures all process methods are run in the first cycle, eliminating
    the need for the "untouched" logic
  - Also, this now allows special cases where a module is only driven by
    `Constant` signals
    - Previously, the corresponding process method(s) would have never been
      executed as constant signals never change, resulting in incorrect
      outputs

# 0.3.0

- Logging:
  - Default log-level is now INFO
    - At this log-level we will only see stable port values
    - At the end of the current cycle (before tick), all port values will be logged
- Serial adder/core has been removed
- ShiftReg stuff has been removed
- Event triggers are now logged at INFO level
- Added shorthand for connecting ports
  - The `<<` operator has been overloaded for the purpose
  - `A << B` is equivalent to `A.connect(B)`
  - Read: "A is driven by B"
    - Or: "A gets its value from B"
- Codebase now adheres to PEP8 guidelines
- Added a requirements.txt to streamline project setup
- Added option to probe specific ports

# 0.2.0

- **Important**:
  - `PortX` and `RegX` have been removed
    - This greatly simplifies the simulation kernel, and tests
    - The recommended way to create a complex port is to use a _dataclass_
    - However, port value can be of any type, so theoretically anything is possible
    - Requirements for custom types:
      - *default value* mechanism
      - *equals* operation
      - *deepcopy* support
- **New**: Implemented `Clock` class to unite handling of registers and memories
  - Write operations on memories and register files will _not_ commit until the next clock tick
    anymore
    - This is to ensure data coherency throughout the current simulation cycle
  - Added `Clocked` class as abstract base case for clocked elements (registers, memories)
- **New**: Added basic logging
  - For logging purposes, the design will be scanned for submodules, ports and registers
    - The instance names of these components is then added as an attribute to each component
- Changes to `Port`:
  - Added **Input** and **Output** ports
  - Ports now have a **type** associated with them
    - Only values of the same type can be written to the port
    - The type is a mandatory parameter when creating a new port
    - There is runtime type checking in place, e.g., when connecting to ports, their types have to match
  - Ports now have a default value (instead of `None`)
    - The port's type's default value is used
    - As suggested in #4, a forced propagation shall happen at the very first write of any port
  - Calling of the onchange handler is not restricted to non-root ports anymore
  - _Input_ ports now have an optional **sensitivity list**
    - The list contains all process methods which should be triggered when the value of the port changes
    - The sensitivity list is passed in the port constructor
    - When the value of the port changes, all methods from the sensitivity list are added to the simulation queue
    - If no sensitvity list was given, the parent module's `process()` method will be taken as the default
    - The `Module.onPortChange()` method is now obsolete and has been removed
    - This feature closes issue #10
  - Directly reading an _output_ port now issues a warning to the user
    - For more details, see issue #5
  - Removed module reference from ports
    - In case no sensitivity list is given, the Module.init() method will add the default `process()` method
- Changes to **Memories/Register files**:
  - Illegal indeces (aka address) for memories and register files, will no longer cause an `IndexError` exception (see issue #6)
    - When a module is processed multiple times during a cycle, it could happen that an unstable port
      value is used as a memory address/register index. As we can assume that the value will eventually stablize, we temporarily allow that access by catching the `IndexError` and returning 0 as the read value.
    - If the address is indeed illegal, that should be handled synchronously (not implemented yet)
      - Register indeces cannot become illegal during regular program flow, because the decoder will only pass 5 bit indeces
  - Removed the `setWe()` method
    - The `we` attribute can be accessed directly instead
  - **New**: Added a **read enable** (`re`) attribute to `MemBase`
    - This is to enable illegal read access exception handling (not implemented yet)
      - The handling is planned to happen synchronously in `_tick()`
      - `Memory` now also remembers the last read address, for later illegal access detection
    - ⚠️ The designer must ensure that the `re` is defaulted to 0 when no read is intended
    - `Regfile` does not make use of `re` (because usually no exceptions need to be handled here)
- **New**: Added **exceptions**
  - Illegal instruction
    - Will throw an actual Python exception
  - Instruction address misaligned
    - Will throw an actual Python exception
  - Load/store address misaligned
    - Will only generate a log message for now
    - In Py-V it's not a big deal to access misaligned locations
- **New**: Added **synchronous resets**
  - Registers now have a second input port `rst`
    - If asserted, the register will be reset to its `resetVal` with the next tick
- **New**: Added **Events**
  - An event can be posted in absolute or relative time
  - An event triggers when the current cycle matches the event time
  - Upon trigger a user-defined callback function will be called
- Changes to **Simulator**
  - Added `step()` method
    - This method advanced the simulation by one cycle
  - Removed custom log
- Changes to **Modules**:
  - Two ports can now be connected via the standard assignment operator
  - `process()` method is no longer mandatory
    - The facilitates having wrapper modules without their own logic
- Registers now only tick when next value is different from current value

# 0.1.0

- Implemented a whole new simulation model

  - This model now follows a similar event-driven
    approach as used in traditional HDL simulators - However, we only care about cycles, i.e. no arbitrary event timestamps - In Py-V any change at the _inputs_ of a module is considered an event - The corresponding module(s) will be added to the simulation queue - The simulator will process each module in the queue, until the queue becomes empty -> The cycle is then considered as done
  - Separated CPU model and simulator
  - Ports now have a direction property
  - Registers can now be reset
  - Changed default (reset) values for PC and IR of `IFStage` module:
    - PC will start at -4, so with the first clock tick, the instruction at address 0 will be latched into the IR
    - IR resets to a NOP instruction
      - This is to prevent any unwanted stuff to happen after the reset got applied

- Added serial components:

  - serial register
    - serial adder
    - ⚠️ These components might be unstable!

- Added API documentation (created using [pdoc](https://pdoc.dev))!
