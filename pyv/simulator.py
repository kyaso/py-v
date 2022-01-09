from pyv.reg import RegBase
import pyv.module as module
from collections import deque
import pyv.log as log

logger = log.getLogger(__name__)

class Simulator:

    # This is a pointer to the currently instantiated
    # simulator. It can be accessed from anywhere without
    # the need to know about the specific simulator instance.
    globalSim = None

    def __init__(self, customLog = None):
        Simulator.globalSim = self

        self._queue = deque()
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
            RegBase.reset()

        for i in range(0, num_cycles):
            #print("")
            #print("**** Cycle {} ****".format(self._cycles))
            logger.debug("**** Cycle {} ****".format(self._cycles))
            #print("")

            # While queue not empty
            while len(self._queue) > 0:
                nextFn = self._queue.popleft()
                logger.debug("Running {}".format(nextFn.__qualname__))
                nextFn()
        
            self._customLog() 

            RegBase._updateRegs()
            self._customLog() 
            self._cycles += 1
    
    def _customLog(self):
        """Runs a custom logging function (if provided)."""
        if self.customLog is not None:
            self.customLog()
    
    def addToSimQ(self, fn):
        """Add a function to the simulation queue.

        Args:
            fn (function): The function we want to add to the queue.
        """
        if fn not in self._queue:
            #self._queue.append(fn)
            logger.debug("Adding {} to queue.".format(fn.__qualname__))
            self._queue.append(fn)
        else:
            logger.debug("{} already in queue.".format(fn.__qualname__))
    
    def getCycles(self):
        """Returns the current number of cycles.

        Returns:
            int: The current number of cycles.
        """
        return self._cycles