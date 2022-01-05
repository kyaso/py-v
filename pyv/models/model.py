from pyv.simulator import Simulator

class Model:
    """Base class for all core models.
    """
    def __init__(self, customLog = None):
        self.cycles = 0
        self.sim = Simulator(customLog)

    def run(self, num_cycles=1):
        """Runs the simulation.

        Args:
            num_cycles (int, optional): Number of clock cycles to simulate. Defaults to 1.
        """
        self.sim.run(num_cycles)
    
    def getCycles(self):
        """Get number cycles executed.

        Returns:
            int: Number of executed cycles.
        """
        return self.sim.getCycles()