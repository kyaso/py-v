from pyv.reg import RegBase
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
        
    def run(self, num_cycles=1, reset_regs: bool = True):
        if reset_regs:
            RegBase.reset()

        for i in range(0, num_cycles):
            print("")
            print("**** Cycle {} ****".format(self._cycles))
            print("")

            # While queue not empty
            while len(self._queue) > 0:
                nextFn = self._queue.popleft()
                nextFn()
        
            RegBase.updateRegs()
            self._cycles += 1
    
    def addToSimQ(self, fn):
        """Add a function to the simulation queue.

        Args:
            fn (function): The function we want to add to the queue.
        """
        if fn not in self._queue:
            #self._queue.append(fn)
            self._queue.append(fn)
    
    def getCycles(self):
        return self._cycles