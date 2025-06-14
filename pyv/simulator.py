from pyv.port import PortList
from collections import deque
from pyv.log import logger
from pyv.clocked import Clock
from pyv.util import PyVObj
from queue import PriorityQueue
from typing import TypeAlias, Callable
import uuid
from datetime import datetime

Event: TypeAlias = tuple[int, uuid.UUID, Callable]


class _EventQueue:
    def __init__(self):
        self._queue = PriorityQueue()

    def _get_num_events(self):
        return len(self._queue.queue)

    def add_event(self, time_abs, callback):
        if time_abs < 0:
            raise Exception("Invalid event time.")

        event: Event = (time_abs, uuid.uuid4(), callback)
        self._queue.put(event)

    def get_next_event(self) -> Event:
        return self._queue.get(False)

    def next_event_time(self) -> int:
        if self._get_num_events() > 0:
            return self._queue.queue[0][0]
        else:
            return -1


class Simulator:
    globalSim = None
    """This is a static pointer to the currently instantiated
    simulator. It can be accessed from anywhere without
    the need to know about the specific simulator instance.
    """

    _stable_callbacks: list[Callable] = []

    def __init__(self):
        Simulator.globalSim = self

        self._objs = []
        self._change_queue = deque()
        self._event_queue = _EventQueue()
        self._cycles = 0

    def init(self):
        """Initialize the simulator.
        This method initializes all objects that have been added to the
        simulator. It should be called before running the simulation.
        """
        for obj in self._objs:
            obj._init(self)

    def addObj(self, obj: PyVObj):
        """Add an object to the simulator.

        Args:
            obj (PyVObj): The object to add to the simulator.
        Raises:
            TypeError: If the object is not an instance of PyVObj.
        """
        if isinstance(obj, PyVObj):
            self._objs.append(obj)
        else:
            raise TypeError(f"Object {obj} is not a PyVObj instance.")

    def set_probes(self, probes: list[str] = []):
        """Setup probes for ports.

        Only ports whose full hierarchical name match at least one element from
        `probes` will be logged during simulation. If `probes` is empty, ALL
        ports will be logged.

        Args:
            probes (list[str]): List of strings to match ports to probe
        """
        PortList.filter(probes)

    def _log_cycle(self):
        logger.info(f"\n**** Cycle {self._cycles} ****")

    def _log_ports(self):
        PortList.log_ports()

    def _log(self):
        self._log_cycle()
        self._log_ports()

    def tick(self):
        """Advance simulation to next cycle. Applies clock tick to registers
        and memories.
        """
        self._log()
        logger.debug("** Clock tick **")
        Clock.tick()
        self._cycles += 1
        return self

    def run_comb_logic(self):
        """Runs combinatorial logic for the current cycle.

        Returns:
            The current simulator instance to allow dot-chaining multiple
            commands.
        """
        self._process_changes()
        self._process_onstable_callbacks()
        return self

    def _cycle(self):
        self._process_events()
        self.run_comb_logic()
        self.tick()

    def step(self):
        """Peform a single simulation step (cycle).
        This is method is intended for use in tests.
        """
        self._cycle()
        self._process_remaining()
        return self

    def _process_remaining(self):
        self._process_events()
        self.run_comb_logic()
        self._log()

    def reset(self):
        """Applies global reset (registers, memories).
        """
        Clock.reset()

    def run(self, num_cycles=1, reset_regs: bool = True):
        """Runs the simulation.

        Args:
            num_cycles (int, optional): Number of cycles to execute. Defaults
                to 1.
            reset_regs (bool, optional): Whether to reset registers before the
                simulation. Defaults to True.
        """
        current_time = datetime.now().strftime("%A, %b %d, %Y at %H:%M:%S")
        logger.info(f"**** Simulation started on {current_time} ****\n")

        if reset_regs:
            self.reset()

        for i in range(0, num_cycles):
            self._cycle()
        self._process_remaining()

    @staticmethod
    def clear():
        """Clear list of registers, memories and ports"""
        Clock.clear()
        PortList.clear()
        Simulator._stable_callbacks = []

    def _process_changes(self):
        while len(self._change_queue) > 0:
            nextFn = self._change_queue.popleft()
            logger.debug(f"Running {nextFn.__qualname__}")
            nextFn()

    def _events_pending(self):
        return self._cycles == self._event_queue.next_event_time()

    def _process_events(self):
        while self._events_pending():
            event: Event = self._event_queue.get_next_event()
            callback = event[2]
            logger.info(f"Triggering event -> {callback.__qualname__}()")
            callback()

    def _process_onstable_callbacks(self):
        for cb in Simulator._stable_callbacks:
            cb()

    def _add_to_change_queue(self, fn):
        """Add a function to the simulation queue.

        Args:
            fn (function): The function we want to add to the queue.
        """
        if fn not in self._change_queue:
            logger.debug(f"Adding {fn.__qualname__} to queue.")
            self._change_queue.append(fn)
        else:
            logger.debug(f"{fn.__qualname__} already in queue.")

    def get_cycles(self):
        """Returns the current number of cycles.

        Returns:
            int: The current number of cycles.
        """
        return self._cycles

    def post_event_abs(self, time_abs, callback):
        """Post an event into the future with *absolute* time.

        Args:
            time_abs (int): Absolute time of event
            callback (function): Callback function to call on event trigger

        Raises:
            Exception: Event time is less then or equal to current cycle.
        """
        if time_abs <= self._cycles:
            raise Exception("Error: Event must lie in the future!")

        self._event_queue.add_event(time_abs, callback)

    def post_event_rel(self, time_rel, callback):
        """Post an event into the future with *relative* time.

        Args:
            time_rel (int): Relative time of event (wrt current cycle)
            callback (function): Callback function to call on event trigger

        Raises:
            Exception: Resulting event time is less then or equal to current
                cycle.
        """
        self.post_event_abs(self._cycles + time_rel, callback)

    @staticmethod
    def register_stable_callback(callback: Callable):
        """Register a callback method to be called once signal values have
        stabilized during the current cycle, and before the next clock tick
        happens.

        Args:
            callback (Callable): The callback method
        """
        Simulator._stable_callbacks.append(callback)
