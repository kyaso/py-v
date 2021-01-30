from module import *
from port import *
from reg import *
import isa
from util import *

# class Stage:
#     def __init__(self):
#         pass

#     A_i = Port()
#     B_i = Port()
#     C_o = Port()

#     def process(self):
#         self.C_o.val = self.A_i.val + self.B_i.val
    
class IFStage(Module):
    def __init__(self):
        self.npc_i = Port()
        self.inst_i = Port()
        self.IFID_o = PortX('inst', 'pc')

        self.PC = Reg()
        # Connect next pc with next value in of PC reg
        self.PC.next = self.npc_i
        # Connect current PC to output
        self.IFID_o['pc'] = self.PC.cur
    
    def process(self):
        # Read instruction
        ir = self.inst_i.read() # TODO: Read instruction mem

        # Outputs
        self.IFID_o.write('inst', ir)

class IDStage(Module):
    def __init__(self, regf):
        self.regfile = regf

        self.IFID_i = PortX('inst', 'pc')

        self.IDEX_o = PortX('rs1', 'rs2', 'imm', 'pc', 'rd', 'we', 'wb_sel', 'opcode', 'funct3', 'funct7')
        
    def process(self):
        # Read inputs
        inst, pc = self.IFID_i.read('inst', 'pc')
        
        # Determine opcode (inst[6:2])
        opcode = getBits(inst, 6, 2)

        # Determine register indeces
        rs1_idx = getBits(inst, 19, 15)
        rs2_idx = getBits(inst, 24, 20)
        rd_idx = getBits(inst, 11, 7)

        # Read regfile
        rs1 = self.regfile.read(rs1_idx)
        rs2 = self.regfile.read(rs2_idx)

        # funct3, funct7
        funct3 = getBits(inst, 14, 12)
        funct7 = getBits(inst, 31, 25)

        # TODO: Check for exception
        # exc = self.check_exception(opcode, funct3, funct7)

        # Decode immediate
        imm = self.decImm(opcode, inst)

        # Determine register file write enable
        we = opcode in isa.REG_OPS

        # Determine what to write-back into regfile
        wb_sel = self.wb_sel(opcode)

        # Outputs
        self.IDEX_o.write('rs1', rs1, 'rs2', rs2, 'imm', imm, 'pc', pc, 'rd', rd_idx, 'we', we, 'wb_sel', wb_sel, 'opcode', opcode, 'funct3', funct3, 'funct7', funct7)

    def wb_sel(self, opcode):
        if opcode == isa.OPCODES['JAL']:
            return 1
        elif opcode == isa.OPCODES['LOAD']:
            return 2
        else:
            return 0

    def decImm(self, opcode, inst):
        # Save sign bit
        sign = getBit(inst, 31)

        sign_ext = 0

        # Decode + sign-extend immediate
        if opcode in isa.INST_I:
            imm_11_0 = getBits(inst, 31, 20)
            imm = imm_11_0
            if sign:
                sign_ext = 0xfffff<<12
        
        elif opcode in isa.INST_S:
            imm_11_5 = getBits(inst, 31, 25)
            imm_4_0 = getBits(inst, 11, 7)
            imm = (imm_11_5<<5) | imm_4_0
            if sign:
                sign_ext = 0xfffff<<12
        
        elif opcode in isa.INST_B:
            imm_12 = getBit(inst, 31)
            imm_10_5 = getBits(inst, 30, 25)
            imm_4_1 = getBits(inst, 11, 8)
            imm_11 = getBits(inst, 7, 7)
            imm =  (imm_12<<12) | (imm_11<<11) | (imm_10_5<<5) | (imm_4_1<<1)
            if sign:
                sign_ext = 0x7ffff<<13
        
        elif opcode in isa.INST_U:
            imm_31_12 = getBits(inst, 31, 12)
            imm = imm_31_12<<12
        
        elif opcode in isa.INST_J:
            imm_20 = getBit(inst, 31)
            imm_10_1 = getBits(inst, 30, 21)
            imm_11 = getBits(inst, 20, 20)
            imm_19_12 = getBits(inst, 19, 12)
            imm = (imm_20<<20) | (imm_19_12<<12) | (imm_11<<11) | (imm_10_1<<1)
            if sign:
                sign_ext = 0x7ff<<21

        return (sign_ext | imm)

    # TODO
    def check_exception(self, opcode, f3, f7):
        if opcode not in isa.OPCODES:
            # Illegal instruction
            pass
        
        if opcode==isa.OPCODES['OP-IMM']:
            if f3==0b001 and f7!=0: # SLLI
                # Illegal instruction
                pass
            elif f3==0b101 and not(f7==0 or f7==0b0100000): # SRLI, SRAI
                # Illegal instruction
                pass
        
        if opcode==isa.OPCODES['OP']:
            if not (f7==0 or f7==0b0100000):
                # Illegal instruction
                pass
            elif f7==0b0100000 and not(f3==0b000 or f3==0b101):
                # Illegal instruction
                pass

        # TODO: Return some exception type
        return False
