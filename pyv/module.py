from typing import Any
import pyv.simulator as simulator
from pyv.clocked import RegBase
from pyv.port import _Port, Input
from pyv.reg import Reg
import pyv.log as log

logger = log.getLogger(__name__)

# TODO: Maybe make this abstract
class Module:
    """Base class for Modules.

    All modules inherit from this class.

    All modules have to implement the `process()` method.
    """
    def __init__(self, name = 'UnnamedModule'):
        self.name = name

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

                if isinstance(obj, Input):
                    if obj._processMethods == []:
                        obj._addProcessMethod(self.process)
                    elif obj._processMethods == [None]:
                        obj._processMethods = []

                if isinstance(obj, Module):
                    obj.init()


    def process(self):
        """Generates module's combinatorial outputs for current cycle based on inputs."""
        pass


    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name not in self.__dict__.keys():
            super().__setattr__(__name, __value)
            return

        attr = self.__dict__[__name]
        if (isinstance(attr, _Port) and isinstance(__value, _Port)):
            port: _Port = attr
            driver: _Port = __value
            port.connect(driver)
            return
        else:
            super().__setattr__(__name, __value)
            return

