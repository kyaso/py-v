import pyv.module as module
from pyv.simulator import Simulator
import warnings

class Model:
    """Base class for all core models.
    """
    def __init__(self, customLog = None):
        print("Initializing model...")

        # TODO: unused
        self.cycles = 0

        self.sim = Simulator(customLog)
    
        # Initialize modules
        try:
            self.top.init()
        except AttributeError:
            print("Error: Missing top module. Please set top module using Model.setTop().")
            exit()
    
    def setTop(self, mod: module.Module, name: str):
        """Set top module.

        Args:
            mod (module.Module): Designated top module.
            name (str): The name the top module should have.
        """
        
        # Set name of module
        mod.name = name
        # Register module as global top module
        self.top = mod
    
    @staticmethod
    def reset():
        # Reset the top module pointer
        module.Module.top = None

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