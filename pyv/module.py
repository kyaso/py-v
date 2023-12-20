from pyv.util import PyVObj


# TODO: Maybe make this abstract
class Module(PyVObj):
    """Base class for Modules.

    All modules inherit from this class.
    """
    def __init__(self, name='UnnamedModule'):
        super().__init__(name)

    def process(self):
        """Generates module's combinatorial outputs for current cycle based on
        inputs.
        """
        pass
