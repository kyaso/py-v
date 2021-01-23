class Port:
    def __init__(self, initVal = 0):
        self.val = initVal
    
    def read(self):
        return self.val
    
    def write(self, val):
        self.val = val
    
class PortX(Port):
    def read(self, port_key=None):
        if port_key is None:
            return self.val
        else:
            return self.val[port_key]
    
    def write(self, val):
        self.val.update(val)