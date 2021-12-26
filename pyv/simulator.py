from collections import deque

class Simulator:

    # This is a pointer to the currently instantiated
    # simulator. It can be accessed from anywhere without
    # the need to know about the specific simulator instance.
    globalSim = None

    def __init__(self):
        Simulator.globalSim = self

        #self._queue = []
        self._queue = deque()
        self._cycles = 0

    def addToSimQ(self, fn):
        """Add a function to the simulation queue.

        Args:
            fn (function): The function we want to add to the queue.
        """
        if fn not in self._queue:
            #self._queue.append(fn)
            self._queue.append(fn)