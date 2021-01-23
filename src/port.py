class Port:
    def __init__(self, initVal = 0):
        self.val = initVal
    
    def read(self):
        return self.val
    
    def write(self, val):
        self.val = val
    
class PortX(Port):
    def __init__(self, *ports):
        # Build dict of ports
        self.val = { port: 0  for port in ports }

    def read(self, *ports):
        # If no specific port name is given, return all ports (as dict)
        if len(ports) == 0:
            return self.val
        elif len(ports) == 1:
            return self.val[ports[0]]
        else:
            port_vals = (self.val[ports[0]],)
            for i in range(1, len(ports)):
                port_vals = port_vals+(self.val[ports[i]],)
            
            return port_vals
    
    def write(self, *args):
        # If a dict of ports is passed to this function,
        # this usually means that we want to copy the values
        # of some other port to this port (e.g. inside a register).
        if type(args[0]) is dict:
            self.val.update(args[0])
            return

        # Even indices: ports
        # Odd indices: value
        for i in range(0, len(args), 2):
            self.val[args[i]] = args[i+1]