from pyv.module import Module
from pyv.simulator import Simulator
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
        except:  # noqa: E722
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

    def setProbes(self, probes: list[str]=[]):
        """Setup probes for ports.

        Only ports whose full hierarchical name match at least one element from
        `probes` will be logged during simulation. If `probes` is empty, ALL
        ports will be logged.

        Args:
            probes (list[str]): List of strings to match ports to probe
        """
        self.sim.setProbes(probes)

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
