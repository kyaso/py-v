from pyv.module import Module
from pyv.simulator import Simulator
import warnings
import traceback

class Model:
    """Base class for all core models.
    """
    def __init__(self):
        print("Initializing model...")

        self.sim = Simulator()
        """Simulator instance"""

        # Initialize modules
        try:
            self.top._init()
        except:
            print(traceback.format_exc())
            print("Something went wrong during init. Aborting.")
            exit()

    def setTop(self, mod: Module, name: str):
        """Set top module.

        Args:
            mod (Module): Designated top module.
            name (str): The name the top module should have.
        """

        # Set name of module
        mod.name = name
        # Register module as global top module
        self.top = mod

    def run(self, num_cycles=1):
        """Runs the simulation.

        Args:
            num_cycles (int, optional): Number of clock cycles to simulate.
        """
        self.sim.run(num_cycles)

    def getCycles(self):
        """Get number cycles executed.

        Returns:
            int: Number of executed cycles.
        """
        return self.sim.getCycles()