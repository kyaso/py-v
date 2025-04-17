from abc import ABC, abstractmethod
import copy
import inspect
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
        self._downstream_inputs: list[Input] = []

        # Who drives this port?
        self._parent = None
        # Which ports does this port drive?
        self._children = []

        PortList.add_port(self)

    @abstractmethod
    def read(self):
        """Read the current port value"""

    def _init(self, parent=None):
        if self._visited:
            return
        self._visited = True

    def _add_downstream_input(self, port: 'Port'):
        self._downstream_inputs.append(port)

    def _clear_root_attrs(self):
        del self._val
        self._downstream_inputs = []


class PortList:
    port_list: list[Port] = []
    port_list_filtered: list[Port] = []

    @staticmethod
    def add_port(port):
        PortList.port_list.append(port)

    @staticmethod
    def clear():
        PortList.port_list = []
        PortList.port_list_filtered = []

    @staticmethod
    def log_ports():
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
        self._process_methods = []
        for m in sensitive_methods:
            self._add_process_method(m)

    def _add_process_method(self, func):
        if func not in self._process_methods:
            self._process_methods.append(func)

    def _parent_has_process_method(self, parent: PyVObj):
        return (hasattr(parent, 'process')
                and inspect.ismethod(getattr(parent, 'process')))

    def init_process_methods(self, parent: PyVObj):
        if self._process_methods == []:
            if self._parent_has_process_method(parent):
                self._add_process_method(parent.process)
        elif self._process_methods == [None]:
            self._process_methods = []

        # Add process methods to simulation queue so they get executed in the
        # first cycle no matter what
        self.add_methods_to_sim_queue()

    def add_methods_to_sim_queue(self):
        import pyv.simulator as simulator
        for func in self._process_methods:
            simulator.Simulator.globalSim._add_to_change_queue(func)


class PortRW(Port, Generic[T]):
    """Base class for read/write ports"""
    def __init__(self, type: Type[T]):
        """Create a new `PortRW` object.

        Args:
            type: Data type for this port.
        """
        super().__init__(type, None)

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

            if self._val != val:
                update_val_and_propagate()

        else:
            raise Exception(f"ERROR (Port '{self.name}'): Only root driver port allowed to write!")  # noqa: E501

    def _propagate(self, oldVal: T, newVal: T):
        """Propagate a value change.
        """
        logger.debug(f"Port {self.name} changed from {oldVal} to {newVal}.")

        for port in self._downstream_inputs:
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
                a write to this input changes its current value. If omitted, a
                default method `process()` is taken as the only sensitive
                method -- if the parent module has such a method defined. If
                `[None]` is passed, no sensitive method will be associated with
                this port. **Important**: if you provide a custom sensitivity
                list, but still want the default `process()` to be triggered as
                well, you have to include it explicitly in the list.
        """
        super().__init__(type)
        self._process_method_handler = _ProcessMethodHandler(sensitive_methods)

    def _init(self, parent: PyVObj):
        super()._init(parent)
        self._process_method_handler.init_process_methods(parent)

    def _set_root_driver(self, newRoot: Port):
        super()._set_root_driver(newRoot)
        newRoot._add_downstream_input(self)

    def _propagate(self, oldVal: T, newVal: T):
        # TODO: Figure out how to log the change before the log of process
        # queue

        # logger.debug(f"Port {self.name} changed from {oldVal} to {newVal}.")

        self._process_method_handler.add_methods_to_sim_queue()
        super()._propagate(oldVal, newVal)

    def _notify(self):
        self._process_method_handler.add_methods_to_sim_queue()


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
