import pyv.simulator as simulator
from pyv.clocked import RegBase
from pyv.port import _Port
from pyv.reg import Reg
import pyv.log as log

logger = log.getLogger(__name__)

# TODO: Maybe make this abstract
# TODO: Should process() really be mandatory for every module?
#   e.g. what about a top module that just instantiates and
#   connects several submodules.
class Module:
    """Base class for Modules.

    All modules inherit from this class.

    All modules have to implement the `process()` method.
    """

    def init(self):
        """Initializes the module.

        This includes the following steps:
        - Set name attributes for each port, register and submodule.
          The instance names are used. We need to access the names for
          logging and waveforms.
        - For each submodule, its own init() method is called.
        """

        for key in self.__dict__:
            obj = self.__dict__[key]
            if isinstance(obj, (_Port, RegBase, Reg, Module)):
                obj.name = self.name+"."+key

                if isinstance(obj, (Reg)):
                    obj.next.name = obj.name+".next"
                    obj.cur.name = obj.name+".cur"

                if isinstance(obj, Module):
                    obj.init()


    def process(self):
        """Generates module's combinatorial outputs for current cycle based on inputs."""

        raise Exception('Please implement process() for this module')
