from pyv.reg import RegBase
import pyv.module as module
from collections import deque
import pyv.log as log
from pyv.clocked import Clock
from queue import PriorityQueue
from typing import TypeAlias, Callable
import uuid

Event: TypeAlias = tuple[int, uuid.UUID, Callable]

logger = log.getLogger(__name__)

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

    # This is a pointer to the currently instantiated
    # simulator. It can be accessed from anywhere without
    # the need to know about the specific simulator instance.
    globalSim = None

    def __init__(self, customLog = None):
        Simulator.globalSim = self

        self._process_q = deque()
        self._event_q = _EventQueue()
        self._cycles = 0

        # Custom log function
        self.customLog = customLog

    def run(self, num_cycles=1, reset_regs: bool = True):
        """Runs the simulation.

        Args:
            num_cycles (int, optional): Number of cycles to execute. Defaults to 1.
            reset_regs (bool, optional): Whether to reset registers before the
                simulation. Defaults to True.
        """
        if reset_regs:
            Clock.reset()

        for i in range(0, num_cycles):
            #print("")
            #print("**** Cycle {} ****".format(self._cycles))
            logger.debug("**** Cycle {} ****".format(self._cycles))
            #print("")

            self._process_events()
            self._process_queue()

            self._customLog()

            Clock.tick()
            self._customLog()
            self._cycles += 1

    def _process_queue(self):
        while len(self._process_q) > 0:
            nextFn = self._process_q.popleft()
            logger.debug("Running {}".format(nextFn.__qualname__))
            nextFn()

    def _events_pending(self):
        return self._cycles == self._event_q.next_event_time()

    def _process_events(self):
        while self._events_pending():
            event: Event = self._event_q.get_next_event()
            callback = event[2]
            logger.debug(f"Triggering event -> {callback.__qualname__}()")
            callback()

    def _customLog(self):
        """Runs a custom logging function (if provided)."""
        if self.customLog is not None:
            self.customLog()

    def _addToProcessQueue(self, fn):
        """Add a function to the simulation queue.

        Args:
            fn (function): The function we want to add to the queue.
        """
        if fn not in self._process_q:
            logger.debug("Adding {} to queue.".format(fn.__qualname__))
            self._process_q.append(fn)
        else:
            logger.debug("{} already in queue.".format(fn.__qualname__))

    def getCycles(self):
        """Returns the current number of cycles.

        Returns:
            int: The current number of cycles.
        """
        return self._cycles

    def postEventAbs(self, time_abs, callback):
        """Post an event into the future.

        Args:
            time_abs (int): Absolute time of event
            callback (function): Callback function to call on event trigger

        Raises:
            Exception: Event time is less then or equal to current cycle.
        """
        if time_abs <= self._cycles:
            raise Exception("Error: Event must lie in the future!")

        self._event_q.add_event(time_abs, callback)

    def postEventRel(self, time_rel, callback):
        """Post an event into the future.

        Args:
            time_rel (int): Relative time of event (wrt current cycle)
            callback (function): Callback function to call on event trigger
        """
        self.postEventAbs(self._cycles + time_rel, callback)
