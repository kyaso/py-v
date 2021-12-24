import copy

class Port:
    """Represents a single port."""

    def __init__(self, initVal = 0):
        """Create a new Port object.

        Args:
            initVal (int, optional): Value to initialize Port output with.
                Defaults to 0.
        """
        self.val = initVal

        # Is this port the root driver?
        self._is_root_driver = True

        # Who drives this port?
        self._parent = None
        # Which ports does this ports drive?
        self._children = []
    
    def read(self):
        """Reads the current value of the port.

        The current value is obtained by quering the `read()` method of the
        driving port. These recursive calls will eventually reach the root
        driver port; its `val` is then returned.

        Returns:
            The current value of the port.
        """

        return copy.deepcopy(self.val)

        # return self._driver.read()
    
    def write(self, val):
        """Writes a new value to the port.

        Args:
            val: The new value.

        Raises:
            Exception: A port that is driven by another port has called
            `write()`.
        """

        if self._is_root_driver:
            self._propagate(val)

        else:
            raise Exception("ERROR (Port): Only root driver port allowed to write!")
    
    def _propagate(self, val):
        # TODO: check if val is new -> add module to sim queue

        self.val = copy.deepcopy(val)
        for p in self._children:
            p._propagate(val)
    
    def connect(self, driver):
        """Connects two ports.

        Args:
            driver (Port): The new driving port for this port.

        Raises:
            Exception: The port attempted to connect to itself.
            TypeError: The `driver` was not of type `Port`.
        """

        if driver == self:
            raise Exception("ERROR (Port): Cannot connect port to itself!")
        if not isinstance(driver, Port):
            raise TypeError("{} is not a Port!".format(driver))

        if self._parent is None:
            self._parent = driver
            driver._children.append(self)
            self._is_root_driver = False
        else:
            raise Exception("ERROR (Port): Port already has a parent!")


        # del self.val
    
class PortX(Port):
    """Represents a collection of Ports."""

    def __init__(self, *ports):
        """Creates a new PortX object.

        A dictionary of `Port` objects will be created.

        Each port within that dict is considered a sub-port of the PortX
        object.

        Args:
            *ports: The names of the sub-ports.
        """

        # Build dict of ports
        self.val = { port: Port()  for port in ports }

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
            return { port: p.read()  for port, p in self.val.items() }
        elif len(ports) == 1:
            return self.val[ports[0]].read()
        else:
            port_vals = (self.val[ports[0]].read(),)
            for i in range(1, len(ports)):
                port_vals = port_vals+(self.val[ports[i]].read(),)
            
            return port_vals
    
    def write(self, *args):
        """Writes new values to one or more sub-ports.

        Args:
            *args: A dict of Ports, OR a list of key-value pairs.
                More details see below.
        """

        # If a dict of ports is passed to this function,
        # this usually means that we want to copy the values
        # of some other PortX to this PortX (e.g. inside a RegX).
        if type(args[0]) is dict:
            ports = args[0]
            # self.val.update(args[0])
            for port in ports.keys():
                self.val[port].write(ports[port])
            return

        # Even indices: sub-port names
        # Odd indices: values
        for i in range(0, len(args), 2):
            self.val[args[i]].write(args[i+1])
    
    def connect(self, driver):
        """Connects two PortX ports.

        Args:
            driver (PortX): The new driver port for this port.

        Raises:
            TypeError: The `driver` was not a PortX object.
        """

        if not isinstance(driver, PortX):
            raise TypeError("{} is not a PortX!".format(driver))
        
        # Iterate over port names (keys) and
        # Connect each sub-port to their new drivers.
        for port in self.val:
            self.val[port].connect(driver.val[port])

    # These two overrides are necessary when we want to connect two sub-ports
    # directly by applying [] to the PortX object, instead of PortX.val[..].
    def __getitem__(self, key):
        return self.val[key]
    
    # TODO: Is this method necessary??
    def __setitem__(self, key, value):
        if not isinstance(value, Port):
            raise TypeError("{} is not of type Port!".format(value))

        self.val[key] = value
        # self.val[key].connect(value)

# A Wire has the same methods and attributes as a Port.
class Wire(Port):
    pass

class WireX(PortX):
    pass