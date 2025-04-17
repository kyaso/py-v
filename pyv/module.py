from typing import Callable
from pyv.simulator import Simulator
from pyv.util import PyVObj


# TODO: Maybe make this abstract
class Module(PyVObj):
    """Base class for Modules.

    All modules inherit from this class.
    """

    def __init__(self, name='UnnamedModule'):
        super().__init__(name)
        self._stable_callbacks = []

    def _init(self, parent=None):
        super()._init(parent)
        self._init_stable_callbacks()

    def _init_stable_callbacks(self):
        for sb in self._stable_callbacks:
            Simulator.register_stable_callback(sb)

    def register_stable_callbacks(self, callbacks: list[Callable]):
        """Register methods to be called back once all signal values during the
        current cycle have stabilized.

        Args:
            callbacks (list[Callable]): List of methods to register
        """
        self._stable_callbacks = callbacks
