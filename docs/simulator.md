# How the simulator advances a cycle

A Py-V model has one implicit clock. A port change can schedule combinational work
within a cycle. Registers and clocked memories commit the inputs they sampled at
the clock edge. Understanding the distinction helps explain why a value read before
an edge can differ from the value read after it.

## From a port write to the next edge

1. **Apply scheduled inputs.** The simulator runs callbacks posted for the current
   cycle before processing combinational changes. Use `post_event_abs(cycle, callback)`
   for an absolute cycle number or `post_event_rel(offset, callback)` for an offset
   from the current cycle. Both require a future cycle. The simulator doesn't
   guarantee insertion order for callbacks scheduled at the same cycle. Combine
   dependent operations into one callback when their order matters.
2. **Settle combinational logic.** An input's driver notifies that input's sensitive
   methods when its value changes. By default an input is sensitive to the owning
   module's `process()`, if it has one. The simulator drains a queue of these
   methods. A method can schedule more work by changing another output. The same
   method isn't added twice while it is waiting in the queue, but can be scheduled
   again after it runs. Design combinational feedback to settle before the clock.
3. **Observe settled signals.** Callbacks registered with
   `Module.register_stable_callbacks()` run after the combinational queue is empty.
   Use them to read current and next values together.
4. **Advance the clock.** The simulator samples the register and memory inputs before
   updating either kind of element, so one register's update can't change what another
   samples at that edge. Then the cycle counter increments. Output changes that
   result from the edge can schedule more combinational work.

After the last edge, `run(n)` processes events, settles signals and runs stable
callbacks once more at the resulting cycle. This final pass does not commit another
edge. `step()` likewise performs one edge and a final settling pass.

## Trace a counter

From the repository root, run this example with Python 3.10 or later. Keep the
example on its own, since the simulator maintains shared registries for elements
such as ports and registers.

```python
from pyv.module import Module
from pyv.port import Input
from pyv.reg import Reg
from pyv.simulator import Simulator


class Counter(Module):
    def __init__(self):
        super().__init__("counter")
        self.delta = Input(int)
        self.total = Reg(int)
        self.register_stable_callbacks([self.observe])

    def process(self):
        self.total.next.write(self.total.cur.read() + self.delta.read())

    def observe(self):
        print(sim.get_cycles(), self.delta.read(),
              self.total.cur.read(), self.total.next.read())


sim = Simulator()
counter = Counter()
sim.addObj(counter)
sim.init()
counter.delta.write(1)
sim.post_event_abs(1, lambda: counter.delta.write(3))
sim.run(2)
```

Each row shows the cycle, input delta, current register value and next value:

```text
0 1 0 1
1 3 1 4
2 3 4 4
```

At cycle 1 the input event sets the delta to 3 before `process()` computes the next
total. The clock edge commits 4. The row for cycle 2 is the final observation and
doesn't commit the next value again.

`run()` resets clocked state by default. Use `run(n, reset_regs=False)` to continue
with the current register and memory state. Resetting clocked state does not reset
the cycle counter. When building another independent model in the same process,
`Simulator.clear()` clears the shared registries. Construct a new simulator and model
for the new run.
