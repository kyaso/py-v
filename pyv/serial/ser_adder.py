from module import *
from port import *
from reg import Reg

# TODO: Maybe add a DONE signal
class SerAdder(Module):
    def __init__(self):
        # Inputs
        self.A_i = Input(int)
        self.B_i = Input(int)
        self.C_rst_i = Input(int)

        # Outputs
        self.S_o = Input(int)

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