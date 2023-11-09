from typing import TypeVar, Generic, Type
from pyv.defines import *
import warnings
import pyv.log as log

logger = log.getLogger(__name__)

T = TypeVar('T')

class _Port(Generic[T]):
    """Represents a single port."""

    def __init__(self, type: Type[T], direction: bool = IN, sensitive_methods = []):
        """Create a new _Port object.

        Args:
            type: Data type for this _Port.
            direction (bool, optional): Direction of this _Port.
                Defaults to Input.
            sensitive_methods (list, optional): List of methods to trigger when
                a write to this port changes it current value. Only valid for
                INPUT ports. If omitted, only the parent module's process()
                method is taken. If [None] is passed, no sensitive method will
                be associated with this port.
        """
        self.name = 'noName'

        self._type = type
        self._direction = direction
        self._val = self._type()

        # Is this port the root driver?
        self._is_root_driver = True

        # Who drives this port?
        self._parent = None
        # Which ports does this port drive?
        self._children = []

        # Whether the port has not been written to in the entire simulation.
        # For most (if not all) ports this will only be the case during the
        # first cycle.
        self._isUntouched = True

        # Setup sensitivity list
        self._processMethods = []
        if self._direction == IN:
            for m in sensitive_methods:
                self._addProcessMethod(m)
        elif len(sensitive_methods) > 0:
            raise Exception(f"Port '{self.name}' with direction OUT cannot have sensitive methods.")

    def read(self) -> T:
        """Reads the current value of the port.

        Returns:
            The current value of the port.
        """

        if self._direction == OUT:
            warnings.warn("Reading output ports directly in process methods is not recommended. If you are reading a top-level output port, you can ignore this warning.")

        return self._val

    def write(self, val: T):
        """Writes a new value to the port.

        Args:
            val: The new value.

        Raises:
            Exception: A port that is driven by another port has called
            `write()`.
            TypeError: Invalid write value type.
        """

        if self._is_root_driver:
            # If the value is different from the current value we have to
            # propagate the change to all children ports.

            # Make sure the type is correct
            if type(val) != self._type:
                raise TypeError(f"ERROR: Cannot write value of type {type(val)} to Port {self.name} which is of type {self._type}.")

            # When the port has not been written to yet, force a propagation
            # even if the new value is the same as the default value
            if self._isUntouched:
                # Port has been written to
                self._isUntouched = False
                self._propagate(val)
            # This is the default behavior: Only propagate when the new value is different
            elif self._val != val:
                self._propagate(val)

        else:
            raise Exception("ERROR (Port): Only root driver port allowed to write!")

    def _propagate(self, val: T):
        """Propagate a new value to all children ports.

        Args:
            val (int): The new value.
        """
        logger.debug(f"Port {self.name} changed from {self._val} to {val}.")

        self._val = val

        # Add this port's sensitive methods to the simulation queue
        if self._direction == IN:
            import pyv.simulator as simulator
            for func in self._processMethods:
                simulator.Simulator.globalSim._addToProcessQueue(func)

        # Now call propagate change to children as well.
        for p in self._children:
            p._propagate(val)

    def connect(self, driver):
        """Connects the current port to a driver port.

        Args:
            driver (_Port): The new driving port for this port.

        Raises:
            Exception: The port attempted to connect to itself.
            TypeError: The `driver` was not of type `_Port`.
            TypeError: Driver port is of different type.
            Exception: The port is already connected to another port.
        """

        # Check whether an illegal self-connection was attempted.
        if driver == self:
            raise Exception("ERROR (Port): Cannot connect port to itself!")
        if not isinstance(driver, _Port):
            raise TypeError(f"{driver} is not a Port!")
        if self._type != driver._type:
            raise TypeError(f"Port type mismatch: This port is of type {self._type}, while driver is of type {driver._type}.")

        # Make the driver this port's parent.
        # Add this port to the list of the driver's children.
        if self._parent is None:
            self._parent = driver
            driver._children.append(self)
            self._is_root_driver = False
            # This variable is only needed for the root driver
            del self._isUntouched
        else:
            raise Exception(f"ERROR (Port): Port {self.name} already has a parent!")

    def _addProcessMethod(self, func):
        if func not in self._processMethods:
            self._processMethods.append(func)


class Input(_Port[T]):
    def __init__(self, type: type[T], sensitive_methods=[]):
        """Create a new input port.

        Args:
            type (type[T]): Data type of this input
            sensitive_methods (list, optional): see _Port.
        """
        super().__init__(type, IN, sensitive_methods)


class Output(_Port[T]):
    def __init__(self, type: type[T]):
        """Create a new ouput port.

        Args:
            type (type[T]): Data type of this output
        """
        super().__init__(type, OUT)

# A Wire has the same methods and attributes as a Port.
class Wire(_Port[T]):
    """Represents a wire.

    A wire can be written to and read from just like a regular port.

    A wire can be connected to other wires or ports.

    If wire value changes, sensitive methods are triggered.
    """
    def __init__(self, type: Type[T], sensitive_methods = []):
        """Create a new wire.

        Args:
            type: Data type of wire value
            sensitive_methods (list, optional): Same as for Port.
        """
        super().__init__(type, IN, sensitive_methods)
