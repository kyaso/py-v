# TODO: Maybe make this abstract
class Module:
    """Base class for Modules.

    All modules inherit from this class.

    All modules have to implement the `process()` method.
    """

    def process(self):
        """Gnerates module's outputs for current cycle based on inputs."""

        raise Exception('Please implement process() for this module')