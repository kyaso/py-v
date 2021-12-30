from pyv.simulator import Simulator
from pyv.port import Port

# TODO: Maybe make this abstract
# TODO: Should process() really be mandatory for every module?
#   e.g. what about a top module that just instantiates and
#   connects several submodules.
class Module:
    """Base class for Modules.

    All modules inherit from this class.

    All modules have to implement the `process()` method.
    """

    def process(self):
        """Generates module's combinatorial outputs for current cycle based on inputs."""

        raise Exception('Please implement process() for this module')
    
    def onPortChange(self, port: Port):
        """Handles a changed input port value.

        If not overriden, the module's process method is added to the
        simulation queue.

        Args:
            port (Port): The port that changed.
        """
        Simulator.globalSim.addToSimQ(self.process)