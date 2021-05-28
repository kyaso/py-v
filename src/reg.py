import copy
from port import *

# TODO: Maybe make abstract
class RegBase:
    reg_list = []

    def __init__(self):
        # Add register to register list
        self.reg_list.append(self)

    def prepareNextVal(self):
        raise Exception('RegBase: Please implement prepareNextVal().')

    def tick(self):
        raise Exception('RegBase: Please implement tick().')

    @staticmethod
    def updateRegs():
        for r in RegBase.reg_list:
            r.prepareNextVal()
        
        for r in RegBase.reg_list:
            r.tick()

class Reg(RegBase):
    def __init__(self, initVal = 0):
        # Add this register to the global register list
        super().__init__()

        self.next = Port()
        self.cur = Port()
        self.cur.write(initVal)
        self.nextv = 0
    
    def prepareNextVal(self):
        self.nextv = copy.deepcopy(self.next.read())

    def tick(self):
        self.cur.write(copy.deepcopy(self.nextv))

class RegX(Reg):
    def __init__(self, *args):
        super().__init__()

        self.next = PortX(*args)
        self.cur = PortX(*args)

class Regfile():
    def __init__(self):
        self.regs = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

    def read(self, reg: int) -> int:
        if reg == 0:
            return 0
        else:
            return self.regs[reg]

    def write(self, reg: int, val: int):
        if reg != 0:
            self.regs[reg] = val