from module import *
from port import *
from reg import *

# class Stage:
#     def __init__(self):
#         pass

#     A_i = Port()
#     B_i = Port()
#     C_o = Port()

#     def process(self):
#         self.C_o.val = self.A_i.val + self.B_i.val
    
class FetchStage(Module):
    def __init__(self):
        self.npc_i = Port()
        self.inst_i = Port()
        self.inst_o = Port()
        self.pc_o = Port()

        self.PC = 0
        self.IR = 0
    
    def process(self):
        # Read inputs
        self.IR = self.inst_i.read() # TODO: Read instruction mem
        self.PC = self.npc_i.read()

        # Outputs
        self.inst_o.write(self.IR)
        self.pc_o.write(self.PC)

class DecodeStage(Module):
    def __init__(self, regf):
        self.regfile = regf

        self.inst_i = Port()
        self.pc_i = Port()
        
        self.rs1_o = Port()
        self.rs2_o = Port()
        self.imm_o = Port()
        self.pc_o = Port()
        self.rd_o = Port()
        self.we_o = Port(False)
        
    def process(self):
        # Determine register indeces
        rs1_idx = 0 # TODO
        rs2_idx = 0

        # Read regfile
        rs1 = self.regfile.read(rs1_idx)
        rs2 = self.regfile.read(rs2_idx)

        # Decode immediate
        imm = 0 # TODO

        # Outputs
        self.rs1_o.val = rs1
        self.rs2_o.val = rs2
        self.imm_o.val = imm
        self.pc_o.val = self.pc_i.val
        self.rd_o.val = 0 # TODO
        self.we_o.val = 0 # TODO

