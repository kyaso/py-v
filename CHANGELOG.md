# 0.1.0

- Implemented a whole new simulation model
    - This model now follows a similar event-driven
    approach as used in traditional HDL simulators
        - However, we only care about cycles, i.e. no arbitrary event timestamps
        - In Py-V any change at the _inputs_ of a module is considered an event
        - The corresponding module(s) will be added to the simulation queue
        - The simulator will process each module in the queue, until the queue becomes empty -> The cycle is then considered as done
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

- Added API documentation (created using [pdoc](https://pdoc3.github.io/pdoc/)!
