from pyv.simulator import Simulator
from pyv.port import Port

# TODO: Maybe make this abstract
class Module:
    """Base class for Modules.

    All modules inherit from this class.

    All modules have to implement the `process()` method.
    """

    def process(self):
        """Generates module's outputs for current cycle based on inputs."""

        raise Exception('Please implement process() for this module')
    
    def onPortChange(self, port: Port):
        """Handles a changed input port value.

        If not overriden, the module's process method is added to the
        simulation queue.
        """
        Simulator.globalSim.addToSimQ(self.process)