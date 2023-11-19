from typing import Any
import pyv.simulator as simulator
from pyv.clocked import RegBase
from pyv.port import Port, Input
from pyv.reg import Reg
import pyv.log as log
from pyv.util import PyVObj

logger = log.getLogger(__name__)

# TODO: Maybe make this abstract
class Module(PyVObj):
    """Base class for Modules.

    All modules inherit from this class.

    All modules have to implement the `process()` method.
    """
    def __init__(self, name = 'UnnamedModule'):
        super().__init__(name)

    def process(self):
        """Generates module's combinatorial outputs for current cycle based on inputs."""
        pass


    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name not in self.__dict__.keys():
            super().__setattr__(__name, __value)
            return

        attr = self.__dict__[__name]
        if (isinstance(attr, Port) and isinstance(__value, Port)):
            port: Port = attr
            driver: Port = __value
            port.connect(driver)
            return
        else:
            super().__setattr__(__name, __value)
            return

