import copy

class Port:
    def __init__(self, initVal = 0):
        self.val = initVal
        self._driver = self
    
    def read(self):
        if self._driver == self:
            return copy.deepcopy(self.val)
        return self._driver.read()
    
    def write(self, val):
        if self._driver == self:
            self.val = copy.deepcopy(val)
        else:
            raise Exception("ERROR (Port): Only driver port allowed to write!")
    
    def connect(self, driver):
        if driver == self:
            raise Exception("ERROR (Port): Cannot connect port to itself!")
        if not isinstance(driver, Port):
            raise TypeError("{} is not a Port!".format(driver))

        self._driver = driver
        del self.val
    
class PortX(Port):
    def __init__(self, *ports):
        # Build dict of ports
        self.val = { port: Port()  for port in ports }

    def read(self, *ports):
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
        # If a dict of ports is passed to this function,
        # this usually means that we want to copy the values
        # of some other PortX to this PortX (e.g. inside a RegX).
        if type(args[0]) is dict:
            ports = args[0]
            # self.val.update(args[0])
            for port in ports.keys():
                self.val[port].write(ports[port])
            return

        # Even indices: ports
        # Odd indices: value
        for i in range(0, len(args), 2):
            self.val[args[i]].write(args[i+1])
    
    def connect(self, driver):
        if not isinstance(driver, PortX):
            raise TypeError("{} is not a PortX!".format(driver))
        
        # Iterate over port names (keys)
        for port in self.val:
            self.val[port].connect(driver.val[port])

    # These two overrides are necessary when we want to connect two subports
    # directly by applying [] to the PortX object, instead of PortX.val[..].
    def __getitem__(self, key):
        return self.val[key]
    
    def __setitem__(self, key, value):
        if not isinstance(value, Port):
            raise TypeError("{} is not of type Port!".format(value))

        self.val[key] = value