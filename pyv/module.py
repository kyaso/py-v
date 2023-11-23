from typing import Any
import pyv.simulator as simulator
from pyv.clocked import RegBase
from pyv.port import Port, Input
from pyv.reg import Reg
import pyv.log as log
from pyv.util import PyVObj


# TODO: Maybe make this abstract
class Module(PyVObj):
    """Base class for Modules.

    All modules inherit from this class.
    """
    def __init__(self, name = 'UnnamedModule'):
        super().__init__(name)

    def process(self):
        """Generates module's combinatorial outputs for current cycle based on inputs."""
        pass
