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
        self.cur.val = initVal
        self.nextv = 0
    
    def prepareNextVal(self):
        self.nextv = self.next.val

    def tick(self):
        self.cur.val = self.nextv

class Regfile(RegBase):

    # rs1_idx_i = Port()
    # rs2_idx_i = Port()

    # rs1_val_o = Port()
    # rs2_val_o = Port()

    def __init__(self):
        # Add this register to the global register list
        super().__init__()

        self.regs = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.rd_idx_i = Port()
        self.rd_val_i = Port()
        self.we = Port(False)

    def read(self, reg):
        # This was from before where I tried to be very close to hardware.
        # However, it is way simpler to do the read directly as below.
        #
        # if self.rs1_idx_i.val != 0:
        #     self.rs1_val_o.val = self.regs[self.rs1_idx_i.val]
        # else:
        #     self.rs1_val_o.val = 0
        
        # if self.rs2_idx_i.val != 0:
        #     self.rs2_val_o.val = self.regs[self.rs2_idx_i.val]
        # else:
        #     self.rs2_val_o.val = 0

        if reg == 0:
            return 0
        else:
            return self.regs[reg]


    def prepareNextVal(self):
        self.nextv = self.rd_val_i.val

    def tick(self):
        # Write
        if self.we.val and (self.rd_idx_i.val != 0):
            self.regs[self.rd_idx_i.val] = self.nextv