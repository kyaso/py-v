from abc import ABC, abstractmethod
import copy
from typing import Any, TypeVar, Generic, Type
from pyv.log import logger
from pyv.util import PyVObj


T = TypeVar('T')


class Port(PyVObj, ABC):
    """Abstract base class for ports."""
    def __init__(self, type, val) -> None:
        super().__init__(name='UnnamedPort')
        self._type = type
        if val is not None:
            self._val = copy.deepcopy(val)
        else:
            # Take the type's default value
            self._val = self._type()
        self._root_driver = self
        self._downstreamInputs: list[Input] = []

        # Who drives this port?
        self._parent = None
        # Which ports does this port drive?
        self._children = []

        PortList.addPort(self)

    @abstractmethod
    def read(self):
        """Read the current port value"""

    def _init(self, parent=None):
        # Empty _init to prevent further processing
        pass

    def _addDownstreamInput(self, port: 'Port'):
        self._downstreamInputs.append(port)

    def _clear_root_attrs(self):
        del self._val
        self._downstreamInputs = []


class PortList:
    port_list: list[Port] = []
    port_list_filtered: list[Port] = []

    @staticmethod
    def addPort(port):
        PortList.port_list.append(port)

    @staticmethod
    def clear():
        PortList.port_list = []
        PortList.port_list_filtered = []

    @staticmethod
    def logPorts():
        if len(PortList.port_list_filtered) > 0:
            ports_to_log = PortList.port_list_filtered
        else:
            ports_to_log = PortList.port_list

        for p in ports_to_log:
            logger.info(f"{p.name}: {p.read()}")

    @staticmethod
    def filter(patterns: list[str]):
        for pat in patterns:
            for port in PortList.port_list:
                if pat in port.name:
                    if port not in PortList.port_list_filtered:
                        PortList.port_list_filtered.append(port)


class _ProcessMethodHandler():
    def __init__(self, sensitive_methods) -> None:
        # Setup sensitivity list
        self._processMethods = []
        for m in sensitive_methods:
            self._addProcessMethod(m)

    def _addProcessMethod(self, func):
        if func not in self._processMethods:
            self._processMethods.append(func)

    def init_process_methods(self, parent: PyVObj):
        if self._processMethods == []:
            self._addProcessMethod(parent.process)
        elif self._processMethods == [None]:
            self._processMethods = []

    def add_methods_to_sim_queue(self):
        import pyv.simulator as simulator
        for func in self._processMethods:
            simulator.Simulator.globalSim._addToProcessQueue(func)


class PortRW(Port, Generic[T]):
    """Base class for read/write ports"""
    def __init__(self, type: Type[T]):
        """Create a new `PortRW` object.

        Args:
            type: Data type for this port.
        """
        super().__init__(type, None)

        # Whether the port has not been written to in the entire simulation.
        # For most (if not all) ports this will only be the case during the
        # first cycle.
        self._isUntouched = True

    def read(self) -> T:
        """Reads the current value of the port.

        Returns:
            The current value of the port.
        """
        if self._root_driver is self:
            return self._val
        else:
            return self._root_driver.read()

    def write(self, val: T):
        """Writes a new value to the port.

        If multiple ports are connected together, only the *root* port, i.e.,
        the one without a parent, can be written to.

        Args:
            val: The new value.

        Raises:
            Exception: `write()` called on a *non-root* port.
            TypeError: Invalid write value type.
        """

        if self._root_driver is self:
            def update_val_and_propagate():
                oldVal = self._val
                newVal = val
                self._val = newVal
                self._propagate(oldVal, newVal)

            # If the value is different from the current value we have to
            # propagate the change to all children ports.

            # Make sure the type is correct
            if type(val) is not self._type:
                raise TypeError(f"ERROR: Cannot write value of type {type(val)} to Port {self.name} which is of type {self._type}.")  # noqa: E501

            # When the port has not been written to yet, force a propagation
            # even if the new value is the same as the default value
            if self._isUntouched:
                # Port has been written to
                self._isUntouched = False
                update_val_and_propagate()
            # This is the default behavior: Only propagate when the new value
            # is different
            elif self._val != val:
                update_val_and_propagate()

        else:
            raise Exception(f"ERROR (Port '{self.name}'): Only root driver port allowed to write!")  # noqa: E501

    def _propagate(self, oldVal: T, newVal: T):
        """Propagate a value change.
        """
        logger.debug(f"Port {self.name} changed from {oldVal} to {newVal}.")

        for port in self._downstreamInputs:
            logger.debug(f"Notifying {port.name}")
            port._notify()

    def _set_root_driver(self, newRoot: Port):
        self._root_driver = newRoot

    def _update_root_driver(self, driver: Port):
        self._set_root_driver(driver._root_driver)
        for child in self._children:
            child._update_root_driver(self._root_driver)

    def connect(self, driver: Port):
        """Connects the current port to a driver port.

        You can also use a shortcut via the `<<` operator:

        `A.connect(B)`

        is equivalent to:

        `A << B`

        Read: "`A` gets its value from `B`", or "`A` is driven by  `B`"

        Args:
            driver (Port): The new driving port (aka *parent*) for this port.

        Raises:
            Exception: The port attempted to connect to itself.
            TypeError: The `driver` was not of type `Port`.
            TypeError: Driver port is of different type.
            Exception: The port is already connected to another port.
        """

        # Check whether an illegal self-connection was attempted.
        if driver == self:
            raise Exception("ERROR (Port): Cannot connect port to itself!")
        if not isinstance(driver, Port):
            raise TypeError(f"{driver} is not a Port!")
        if self._type != driver._type:
            raise TypeError(f"Port type mismatch: This port is of type {self._type}, while driver is of type {driver._type}.")  # noqa: E501

        # Make the driver this port's parent.
        # Add this port to the list of the driver's children.
        if self._parent is None:
            self._parent = driver
            driver._children.append(self)
            self._update_root_driver(driver)
            self._clear_root_attrs()
        else:
            raise Exception(
                f"ERROR (Port): Port {self.name} already has a parent!")

    def __lshift__(self, driver: 'PortRW'):
        """Overload << operator for port connection.

        `A << B`

        is equivalent to:

        `A.connect(B)`
        """
        self.connect(driver)


class Input(PortRW[T]):
    """Represents an **Input** port."""
    def __init__(self, type: type[T], sensitive_methods=[]):
        """Create a new input port.

        If the value of the input changes, sensitive method will be triggered.

        Args:
            type (type[T]): Data type of this input
            sensitive_methods (list, optional): List of methods to trigger when
                a write to this input changes its current value. If omitted,
                only the parent module's `pyv.module.Module.process()` method
                is taken. If `[None]` is passed, no sensitive method will be
                associated with this port. **Important**: if you provide a
                custom sensitivity list, but still want the default `process()`
                to be triggered as well, you have to include it explicitly in
                the list.
        """
        super().__init__(type)
        self._processMethodHandler = _ProcessMethodHandler(sensitive_methods)

    def _init(self, parent: PyVObj):
        if self._visited:
            return
        self._visited = True
        self._processMethodHandler.init_process_methods(parent)

    def _set_root_driver(self, newRoot: Port):
        super()._set_root_driver(newRoot)
        newRoot._addDownstreamInput(self)

    def _propagate(self, oldVal: T, newVal: T):
        # TODO: Figure out how to log the change before the log of process
        # queue

        # logger.debug(f"Port {self.name} changed from {oldVal} to {newVal}.")

        self._processMethodHandler.add_methods_to_sim_queue()
        super()._propagate(oldVal, newVal)

    def _notify(self):
        self._processMethodHandler.add_methods_to_sim_queue()


class Output(PortRW[T]):
    """Represents an **Output** port."""
    def __init__(self, type: type[T]):
        """Create a new ouput port.

        Note that output port do not have any sensitive methods.

        Args:
            type (type[T]): Data type of this output
        """
        super().__init__(type)


class Wire(Input[T]):
    """Represents a **Wire**.

    A wire can be written to and read from just like a regular port.

    A wire can be connected to other wires or ports.

    If wire value changes, sensitive methods are triggered.
    """
    def __init__(self, type: Type[T], sensitive_methods=[]):
        """Create a new wire.

        Args:
            type: Data type of wire value
            sensitive_methods (list, optional): See `Input.__init__()`.
        """
        super().__init__(type, sensitive_methods)


class Constant(Port):
    """Represents a constant signal. Once initialized, its value cannot be
    changed.
    """
    def __init__(self, constVal: Any):
        """Create a new constant signal.

        Args:
            constVal (Any): Constant value
        """
        super().__init__(type(constVal), constVal)

    def read(self):
        return self._val
