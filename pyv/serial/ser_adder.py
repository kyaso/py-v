from pyv.module import *
from pyv.port import *
from pyv.reg import Reg

# TODO: Maybe add a DONE signal
class SerAdder(Module):
    def __init__(self):
        # Inputs
        self.A_i = Port()
        self.B_i = Port()
        self.C_rst_i = Port()

        # Outputs
        self.S_o = Port()

        # Internal carry register
        self.carry = 0
    
    def process(self):
        # Read inputs
        A = self.A_i.read()
        B = self.B_i.read()
        C_rst = self.C_rst_i.read()

        # Check for reset internal carry
        if C_rst == 1:
            self.carry = 0
        
        # Full-adder equations
        S = A ^ B ^ self.carry
        self.carry = A&B | B&self.carry | self.carry&A

        # Write sum bit to output
        self.S_o.write(S)