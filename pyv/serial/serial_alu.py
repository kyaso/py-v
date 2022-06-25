from pyv.module import *
from pyv.port import *
from pyv.serial.ser_adder import SerAdder
import pyv.isa as isa
import warnings

class SerALU(Module):
    def __init__(self, depth):
        self.depth = depth
        warnings.warn("SerALU: depth {} is not a power of 2.".format(depth))
        
        # Inputs
        self.alu_i = PortX( 'opcode',
                            'rs1',
                            'rs2',
                            'imm',
                            'pc',
                            'f3',
                            'f7'
                          )
        
        # Outputs
        self.alu_res_o = Port()
        self.alu_done_o = Port()

        # Bit counter register
        self.bit_cnt = 0
        self.bit_cnt_next = 0
        self.bit_cnt_mask = self.depth-1

        # Submodules
        self.adder = SerAdder()
    
    def process(self):
        self.bit_cnt = self.bit_cnt_next
        self.alu_done_o.write(0)
        if self.bit_cnt == self.bit_cnt_mask:
            self.alu_done_o.write(1)

        opcode = self.alu_i.read('opcode')

        # Select operands
        op1 = op2 = 0
        # op1
        if opcode==isa.OPCODES['AUIPC'] or opcode==isa.OPCODES['JAL'] or opcode==isa.OPCODES['BRANCH']:
            op1 = self.alu_i.read('pc')
        else:
            op1 = self.alu_i.read('rs1')
        # op2
        if opcode!=isa.OPCODES['OP']:
            op2 = self.alu_i.read('imm')
        else:
            op2 = self.alu_i.read('rs2')

        # TODO: ALU MUX
        alu_res = 0

        # Write ALU output
        self.alu_res_o.write(alu_res)

        # Increase bit counter
        # Masking simulates a saturating counter
        self.bit_cnt_next = self.bit_cnt_mask&(self.bit_cnt+1)