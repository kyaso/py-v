class Port:
    def __init__(self, initVal = 0):
        self.val = initVal
    
    def read(self):
        return self.val
    
    def write(self, val):
        self.val = val