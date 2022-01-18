import copy
from pyv.defines import *
import warnings
import pyv.log as log

logger = log.getLogger(__name__)

class Port:
    """Represents a single port."""

    def __init__(self, direction: bool = IN, module = None, initVal = 0):
        """Create a new Port object.

        Args:
            direction (bool): Direction of this Port.
                Defaults to Input.
            module (Module): The module this port belongs to.
            initVal (int, optional): Value to initialize Port output with.
                Defaults to None.
        """
        self.name = 'noName'

        self._direction = direction
        self._val = initVal

        if module is not None:
            self._module = module
        else:
            self._module = None

        # Is this port the root driver?
        self._is_root_driver = True

        # Who drives this port?
        self._parent = None
        # Which ports does this ports drive?
        self._children = []

        # Whether the port has not been written to in the entire simulation.
        # For most (if not all) ports this will only be the case during the
        # first cycle.
        self._isUntouched = True

    def read(self):
        """Reads the current value of the port.

        Returns:
            The current value of the port.
        """

        if self._direction == OUT:
            warnings.warn("Reading output ports directly in process methods is not recommended. If you are reading a top-level output port, you can ignore this warning.")

        return copy.deepcopy(self._val)

    def write(self, val):
        """Writes a new value to the port.

        Args:
            val: The new value.

        Raises:
            Exception: A port that is driven by another port has called
            `write()`.
        """

        if self._is_root_driver:
            # If the value is different from the current value we have to
            # propagate the change to all children ports.

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
    
    def _propagate(self, val):
        logger.debug("Port {} changed from 0x{:08X} to 0x{:08X}.".format(self.name, self._val, val))
        """Propagate a new value to all children ports.

        Args:
            val (int): The new value.
        """
        self._val = copy.deepcopy(val)

        # Call the onChange handler of the parent module
        # Only for input ports
        if (self._module is not None) and (self._direction == IN):
            self._module.onPortChange(self)

        # Now call propagate change to children as well.
        for p in self._children:
            p._propagate(val)
    
    def connect(self, driver):
        """Connects the current port to a driver port. 

        Args:
            driver (Port): The new driving port for this port.

        Raises:
            Exception: The port attempted to connect to itself.
            TypeError: The `driver` was not of type `Port`.
        """

        # Check whether an illegal self-connection was attempted.
        if driver == self:
            raise Exception("ERROR (Port): Cannot connect port to itself!")
        if not isinstance(driver, Port):
            raise TypeError("{} is not a Port!".format(driver))

        # Make the driver this port's parent.
        # Add this port to the list of the driver's children.
        if self._parent is None:
            self._parent = driver
            driver._children.append(self)
            self._is_root_driver = False
            # This variable is only needed for the root driver
            del self._isUntouched
        else:
            raise Exception("ERROR (Port): Port already has a parent!")

class PortX(Port):
    """Represents a collection of Ports."""

    def __init__(self, direction: bool = IN, module = None, *ports):
        """Creates a new PortX object.

        A dictionary of `Port` objects will be created.

        Each port within that dict is considered a sub-port of the PortX
        object.

        Args:
            direction: Port direction. Default: Input
                
                All sub-ports will have the same direction.
            module: The parent module of this port.
            *ports: The names of the sub-ports.
        """

        # Build dict of ports
        self._val = { port: Port(direction, module)  for port in ports }

    def read(self, *ports):
        """Reads the current value(s) of one or more sub-ports.

        Args:
            *ports: The name(s) of the sub-port(s) to read values from.

        Returns:
            Depending on the number n of sub-port names given:
            * n=0: Return values of all sub-ports as `dict`.
            * n=1: Return value of the single sub-port.
            * otherwise: Return values of the n provided sub-ports in a list.
        """

        if len(ports) == 0:
            # If no specific port name is given, return values of all ports (as dict)
            return { port: p.read()  for port, p in self._val.items() }
        elif len(ports) == 1:
            return self._val[ports[0]].read()
        else:
            port_vals = (self._val[ports[0]].read(),)
            for i in range(1, len(ports)):
                port_vals = port_vals+(self._val[ports[i]].read(),)
            
            return port_vals
    
    def write(self, *args):
        """Writes new values to one or more sub-ports.

        Args:
            *args: A single integer value,
                OR dict of Ports,
                OR a list of key-value pairs.
                
        If a single integer value is passed, all sub-ports will receive that value.

        A `dict` of ports is usually passed as part of some automatic write
        (e.g. in a `RegX`).

        For writing values to a subset of the sub-ports, use a *key-value* pair list.
        For example:
        ```
        p.write('foo', 42, 'bar', 99)
        ```
        will write 42 to the sub-port named "foo", and 99 to the sub-port named "bar".
        """

        # If a single integer value is passed to this function,
        # all subports will get this value.
        if type(args[0]) is int:
            for port in self._val:
                self._val[port].write(args[0])
            return

        # If a dict of ports is passed to this function,
        # this usually means that we want to copy the values
        # of some other PortX to this PortX (e.g. inside a RegX).
        if type(args[0]) is dict:
            ports = args[0]
            # self._val.update(args[0])
            for port in ports.keys():
                self._val[port].write(ports[port])
            return

        # Even indices: sub-port names
        # Odd indices: values
        for i in range(0, len(args), 2):
            self._val[args[i]].write(args[i+1])
    
    def connect(self, driver):
        """Connects the current PortX to a driver PortX.

        Args:
            driver (PortX): The new driver port for this port.

        Raises:
            TypeError: The `driver` was not a PortX object.
        """

        if not isinstance(driver, PortX):
            raise TypeError("{} is not a PortX!".format(driver))
        
        # Iterate over port names (keys) and
        # Connect each sub-port to their new drivers.
        for port in self._val:
            self._val[port].connect(driver._val[port])

    # These two overrides are necessary when we want to connect two sub-ports
    # directly by applying [] to the PortX object, instead of PortX._val[..].
    def __getitem__(self, key):
        # `key` is the name of a sub-port
        return self._val[key]
    
    # TODO: Is this method necessary??
    def __setitem__(self, key, value):
        if not isinstance(value, Port):
            raise TypeError("{} is not of type Port!".format(value))

        self._val[key] = value
        # self._val[key].connect(value)
    
    def _namePorts(self):
        """Name all subports with portxName.subportName format.
        
        This requires a name to be set for the PortX (usually in Module.init()).
        """
        for port in self._val:
            self._val[port].name = self.name+"."+port 

# A Wire has the same methods and attributes as a Port.
class Wire(Port):
    """Represents a single-valued wire.

    A wire can be written to and read from just like a regular `Port`.

    A wire can be connected to other wires or ports.
    """
    pass

class WireX(PortX):
    """Represents a multi-valued wire.

    Can be connected to PortX ports.
    """
    pass