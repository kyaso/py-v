from module import *
from port import *
from reg import *
import isa
from instructions import *
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

        self.IDEX_o = PortX('rs1', 'rs2', 'imm', 'pc', 'rd', 'we', 'wb_sel', 'opcode', 'funct3', 'funct7', 'mem')
        
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

        # Determine none/load/store
        mem = self.mem_sel(opcode)

        # Outputs
        self.IDEX_o.write('rs1', rs1, 'rs2', rs2, 'imm', imm, 'pc', pc, 'rd', rd_idx, 'we', we, 'wb_sel', wb_sel, 'opcode', opcode, 'funct3', funct3, 'funct7', funct7, 'mem', mem)

    def mem_sel(self, opcode):
        if opcode==isa.OPCODES['LOAD']:
            return 1
        elif opcode==isa.OPCODES['STORE']:
            return 2
        else:
            return 0

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

        imm = 0
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

class EXStage(Module):
    def __init__(self):
        self.IDEX_i = PortX('rs1',
                            'rs2',
                            'imm',
                            'pc',
                            'rd',
                            'we',
                            'wb_sel',
                            'opcode',
                            'funct3',
                            'funct7',
                            'mem')
        
        self.EXMEM_o = PortX('rd',
                             'we',
                             'wb_sel',
                             'take_branch',
                             'alu_res',
                             'pc4',
                             'rs2',
                             'mem',
                             'funct3')

        # Pass throughs
        self.EXMEM_o['rd'] = self.IDEX_i['rd']
        self.EXMEM_o['we'] = self.IDEX_i['we']
        self.EXMEM_o['wb_sel'] = self.IDEX_i['wb_sel']
        self.EXMEM_o['rs2'] = self.IDEX_i['rs2']
        self.EXMEM_o['mem'] = self.IDEX_i['mem']
        self.EXMEM_o['funct3'] = self.IDEX_i['funct3']
    
    def process(self):
        # Read inputs
        opcode, rs1, rs2, imm, pc, f3, f7 = self.IDEX_i.read('opcode', 'rs1', 'rs2', 'imm', 'pc', 'funct3', 'funct7')

        # Check for branch/jump
        take_branch = False
        if opcode==isa.OPCODES['BRANCH']:
            take_branch = self.branch(f3, rs1, rs2) # TODO
        elif opcode==isa.OPCODES['JAL'] or opcode==isa.OPCODES['JALR']:
            take_branch = True
        
        pc4 = pc+4

        # ALU
        alu_res = self.alu(opcode, rs1, rs2, imm, pc, f3, f7)

        # Outputs
        self.EXMEM_o.write('take_branch', take_branch, 'pc4', pc4, 'alu_res', alu_res)

    def alu(self, opcode, rs1, rs2, imm, pc, f3, f7):
        # Select operands
        op1 = op2 = 0
        # op1
        if opcode==isa.OPCODES['AUIPC'] or opcode==isa.OPCODES['JAL'] or opcode==isa.OPCODES['BRANCH']:
            op1 = pc
        else:
            op1 = rs1
        # op2
        if opcode!=isa.OPCODES['OP']:
            op2 = imm
        else:
            op2 = rs2

        # Perform ALU op
        alu_res = 0
        if opcode==isa.OPCODES['LUI']:
            alu_res = op2
        
        elif opcode==isa.OPCODES['AUIPC'] or opcode==isa.OPCODES['JAL'] or opcode==isa.OPCODES['BRANCH']:
            alu_res = op1 + op2
        
        elif opcode==isa.OPCODES['JALR']:
            alu_res = 0xfffffffe & (op1 + op2)

        elif opcode==isa.OPCODES['LOAD'] or opcode==isa.OPCODES['STORE']:
            alu_res = op1 + op2
        
        elif opcode==isa.OPCODES['OP-IMM']:
            if f3==0b000: # ADDI
                alu_res = op1 + op2
            elif f3==0b010: # SLTI
                alu_res = i_SLT(op1, op2)
            elif f3==0b011: # SLTIU
                alu_res = i_SLTU(op1, op2)
            elif f3==0b100: # XORI
                alu_res = op1 ^ op2
            elif f3==0b110: # ORI
                alu_res = op1 | op2
            elif f3==0b111: # ANDI
                alu_res = op1 & op2
            elif f3==0b001: # SLLI
                if f7==0: # TODO: We could remove this check if IDStage catches f7!=0 case
                    alu_res = i_SLL(op1, op2)
            elif f3==0b101:
                if f7==0: # SRLI
                    alu_res = i_SRL(op1, op2)
                elif f7==0b0100000: # SRAI
                    alu_res = i_SRA(op1, op2)
        
        elif opcode==isa.OPCODES['OP']:
            if f7==0:
                if f3==0b000: # ADD
                    alu_res = op1 + op2
                elif f3==0b001: # SLL
                    alu_res = i_SLL(op1, op2)
                elif f3==0b010: # SLT
                    alu_res = i_SLT(op1, op2)
                elif f3==0b011: # SLTU
                    alu_res = i_SLTU(op1, op2)
                elif f3==0b100: # XOR
                    alu_res = op1 ^ op2
                elif f3==0b101: # SRL
                    alu_res = i_SRL(op1, op2)
                elif f3==0b110: # OR
                    alu_res = op1 | op2
                elif f3==0b111: # AND
                    alu_res = op1 & op2

            elif f7==0b0100000:
                if f3==0b000: # SUB
                    alu_res = op1 - op2
                elif f3==0b101: # SRA
                    alu_res = i_SRA(op1, op2)
   
        return MASK_32 & alu_res

    # TODO
    # opcode can be removed
    def branch(self, f3, rs1, rs2):
        """
        Performs comparison of rs1 and rs2 using comp op given by f3.

        Returns True if branch is taken.
        """
        if f3==0:               # BEQ
            return rs1==rs2
        elif f3==1:             # BNE
            return rs1!=rs2
        elif f3==4:             # BLT
            return rs1<rs2
        elif f3==5:             # BGE
            return rs1>=rs2
        elif f3==6:             # BLTU
            # TODO
            return rs1<rs2
        elif f3==7:             # BGEU
            # TODO
            return rs1>=rs2
