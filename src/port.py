class Port:
    def __init__(self, initVal = 0):
        self.val = initVal
    
    def read(self):
        return self.val
    
    def write(self, val):
        self.val = val
    
class PortX(Port):
    def __init__(self, *args):
        # Build dict of ports
        self.val = { port: 0  for port in args}

    def read(self, port_key=None):
        # If no specific port name is given, return all ports
        if port_key is None:
            return self.val
        else:
            return self.val[port_key]
    
    def write(self, *args):
        # Even indices: ports
        # Odd indices: value
        for i in range(0, len(args), 2):
            self.val[args[i]] = args[i+1]