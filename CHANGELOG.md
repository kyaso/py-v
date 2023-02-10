# Next release (0.?.0)

- **New**: Implemented abstract `Clocked` class to unite handling of registers and memories
  - Write operations on memories and register files will _not_ commit until the next clock tick
    anymore
    - This is to ensure data coherency throughout the current simulation cycle
- **New**: Added basic logging
  - For logging purposes, the design will be scanned for submodules, ports and registers
    - The instance names of these components is then added as an attribute to each component
- Changes to `Port`:
  - Ports now have default value of 0 (instead of `None`)
    - As suggested in #4, a forced propagation shall happen at the very first write of any port
  - Calling of the onchange handler is not restricted to non-root ports anymore
  - Directly reading an _output_ port now issues a warning to the user
    - For more details, see issue #5
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
