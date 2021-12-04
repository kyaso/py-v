from module import *
from port import *
from reg import Reg

class SerAdder(Module):
    def __init__(self, depth: int):
        # depth needs to be a power of 2
        if not ((depth & (depth-1) == 0) and depth != 0):
            raise Exception("SerAdder: depth must be power of 2! Given depth is {}.".format(depth))

        # Inputs
        self.A_i = Port()
        self.B_i = Port()

        # Outputs
        self.S_o = Port()

        # Sum register
        self.S_reg = Reg()
        self.S_o.connect(self.S_reg.cur)

        self.depth = depth
        self.bit_cnt = 0
        self.bit_cnt_mask = depth - 1

        # Internal carry
        self.carry = 0
    
    def process(self):
        # Read inputs
        A = self.A_i.read()
        B = self.B_i.read()

        # Reset internal carry in case we are done with one word
        if self.bit_cnt == 0:
            self.carry = 0
        
        # Full-adder equations
        S = A ^ B ^ self.carry
        self.carry = A&B | B&self.carry | self.carry&A

        # Write sum bit to output register
        self.S_reg.next.write(S)

        # Increase bit counter
        # The masking emulates a saturating counter
        self.bit_cnt = self.bit_cnt_mask&(self.bit_cnt + 1)
        