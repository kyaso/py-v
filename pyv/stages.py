from pyv.module import *
from pyv.port import *
from pyv.reg import *
from pyv.mem import *
import pyv.isa as isa
from pyv.util import *
from pyv.defines import *
import pyv.log as log
from dataclasses import dataclass

logger = log.getLogger(__name__)

@dataclass
class IFID_t:
    inst: int = 0
    pc: int = 0

@dataclass
class IDEX_t:
    rs1: int = 0
    rs2: int = 0
    imm: int = 0
    pc: int = 0
    rd: int = 0
    we: int = 0
    wb_sel: int = 0
    opcode: int = 0
    funct3: int = 0
    funct7: int = 0
    mem: int = 0

@dataclass
class EXMEM_t:
    rd: int = 0
    we: int = 0
    wb_sel: int = 0
    take_branch: bool = False
    alu_res: int = 0
    pc4: int = 0
    rs2: int = 0
    mem: int = 0
    funct3: int = 0

@dataclass
class MEMWB_t:
    rd: int = 0
    we: int = 0
    alu_res: int = 0
    pc4: int = 0
    mem_rdata: int = 0
    wb_sel: int = 0

LOAD = 1
STORE = 2

class IFStage(Module):
    """Instruction Fetch Stage.

    Inputs:
        npc_i: Next program counter (PC).

    Outputs:
        IFID_o: Interface to IDStage.
    """

    def __init__(self, imem: Memory):
        # Next PC
        self.npc_i = Input(int, self)
        self.IFID_o = Output(IFID_t, self)

        # Program counter (PC)
        self.pc_reg = Reg(int, -4)

        # Instruction register (IR)
        self.ir_reg = Reg(int, 0x00000013)

        # Helper wires
        self.pc_reg_w = Wire(int, self, [self.writeOutput])
        self.ir_reg_w = Wire(int, self, [self.writeOutput])
        self.pc_reg_w = self.pc_reg.cur
        self.ir_reg_w = self.ir_reg.cur

        # Instruction memory
        self.imem = imem

        # Connect next PC to input of PC reg
        self.pc_reg.next = self.npc_i

    def process(self):
        # Read inputs
        npc = self.npc_i.read()

        # Read instruction
        self.ir_reg.next.write(self.imem.read(npc, 4))
        # TODO: Illegal address exception handling

    def writeOutput(self):
        self.IFID_o.write(IFID_t(self.ir_reg_w.read(), self.pc_reg_w.read()))

class IDStage(Module):
    """Instruction decode stage.

    Inputs:
        IFID_i: Interface from IFStage

    Outputs:
        IDEX_o: Interface to EXStage
    """

    def __init__(self, regf: Regfile):
        self.regfile = regf

        # Inputs
        self.IFID_i = Input(IFID_t, self)

        # Outputs
        self.IDEX_o = Output(IDEX_t, self)

    def process(self):
        # Read inputs
        val: IFID_t = self.IFID_i.read()
        inst = val.inst
        self.pc = val.pc

        # Illegal instruction if bits 1:0 of inst != b11
        if (inst & 0x3) != 0x3:
            raise Exception(f"IDStage: Illegal instruction @ PC = 0x{self.pc:08X} detected.")

        # Determine opcode (inst[6:2])
        opcode = getBits(inst, 6, 2)

        # funct3, funct7
        funct3 = getBits(inst, 14, 12)
        funct7 = getBits(inst, 31, 25)

        self.check_exception(opcode, funct3, funct7)

        # Determine register indeces
        rs1_idx = getBits(inst, 19, 15)
        rs2_idx = getBits(inst, 24, 20)
        rd_idx = getBits(inst, 11, 7)

        # Read regfile
        rs1 = self.regfile.read(rs1_idx)
        rs2 = self.regfile.read(rs2_idx)

        # Decode immediate
        imm = self.decImm(opcode, inst)

        # Determine register file write enable
        we = opcode in isa.REG_OPS

        # Determine what to write-back into regfile
        wb_sel = self.wb_sel(opcode)

        # Determine none/load/store
        mem = self.mem_sel(opcode)

        # Outputs
        self.IDEX_o.write(IDEX_t(rs1, rs2, imm, self.pc, rd_idx, we, wb_sel, opcode, funct3, funct7, mem))

    def mem_sel(self, opcode):
        """Generates control signal for memory access.

        Args:
            opcode: Opcode of current instruction.

        Returns:
            A special value when the instruction is LOAD/STORE.
            0 otherwise.
        """
        if opcode==isa.OPCODES['LOAD']:
            return LOAD
        elif opcode==isa.OPCODES['STORE']:
            return STORE
        else:
            return 0

    def wb_sel(self, opcode):
        """Generates control signal for write-back.

        Args:
            opcode: Opcode of current instruction.

        Returns:
            * 1: JAL instruction
            * 2: LOAD instruction
            * 0: otherwise
        """
        if opcode == isa.OPCODES['JAL']:
            return 1
        elif opcode == isa.OPCODES['LOAD']:
            return 2
        else:
            return 0

    def decImm(self, opcode, inst):
        """Decodes the immediate from the instruction word.

        Args:
            opcode: Opcode of current instruction.
            inst: Current instruction word.

        Returns:
            The decoded immediate.
        """

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

    def check_exception(self, opcode, f3, f7):
        """[summary]

        Args:
            opcode ([type]): [description]
            f3 ([type]): [description]
            f7 ([type]): [description]

        Returns:
            [type]: [description]
        """
        illinst = False

        if opcode not in isa.OPCODES.values():
            # Illegal instruction
            raise Exception(f"IDStage: Illegal instruction @ PC = 0x{self.pc:08X}: unknown opcode")

        if opcode==isa.OPCODES['OP-IMM']:
            if f3==0b001 and f7!=0: # SLLI
                # Illegal instruction
                raise Exception(f"IDStage: Illegal instruction @ PC = 0x{self.pc:08X} detected.")
                illinst = True
            elif f3==0b101 and not(f7==0 or f7==0b0100000): # SRLI, SRAI
                # Illegal instruction
                raise Exception(f"IDStage: Illegal instruction @ PC = 0x{self.pc:08X} detected.")
                illinst = True

        if opcode==isa.OPCODES['OP']:
            if not (f7==0 or f7==0b0100000):
                # Illegal instruction
                raise Exception(f"IDStage: Illegal instruction @ PC = 0x{self.pc:08X} detected.")
                illinst = True
            elif f7==0b0100000 and not(f3==0b000 or f3==0b101):
                # Illegal instruction
                raise Exception(f"IDStage: Illegal instruction @ PC = 0x{self.pc:08X} detected.")
                illinst = True

        if opcode==isa.OPCODES['JALR']:
            if f3 != 0:
                # Illegal instruction
                raise Exception(f"IDStage: Illegal instruction @ PC = 0x{self.pc:08X} detected.")
                illinst = True

        if opcode==isa.OPCODES['BRANCH']:
            if f3 == 2 or f3 == 3:
                # Illegal instruction
                raise Exception(f"IDStage: Illegal instruction @ PC = 0x{self.pc:08X} detected.")
                illinst = True

        if opcode==isa.OPCODES['LOAD']:
            if f3 == 3 or f3 == 6 or f3 == 7:
                # Illegal instruction
                raise Exception(f"IDStage: Illegal instruction @ PC = 0x{self.pc:08X} detected.")
                illinst = True

        if opcode==isa.OPCODES['STORE']:
            if f3 > 2:
                # Illegal instruction
                raise Exception(f"IDStage: Illegal instruction @ PC = 0x{self.pc:08X} detected.")
                illinst = True

        # TODO: do something with illinst

        # TODO: Return some exception type
        return False

class EXStage(Module):
    """Execute stage.

    Inputs:
        IDEX_i: Interface from IDStage.

    Outputs:
        EXMEM_o: Interface to MEMStage.
    """
    def __init__(self):
        self.IDEX_i = Input(IDEX_t, self, sensitive_methods=[self.process, self.passThrough])

        self.EXMEM_o = Output(EXMEM_t, self)
        self.exmem_val = EXMEM_t()

    def writeOutput(self):
        self.EXMEM_o.write(EXMEM_t(
            self.exmem_val.rd,
            self.exmem_val.we,
            self.exmem_val.wb_sel,
            self.exmem_val.take_branch,
            self.exmem_val.alu_res,
            self.exmem_val.pc4,
            self.exmem_val.rs2,
            self.exmem_val.mem,
            self.exmem_val.funct3
        ))

    def passThrough(self):
        val = self.IDEX_i.read()
        self.exmem_val.rd = val.rd
        self.exmem_val.we = val.we
        self.exmem_val.wb_sel = val.wb_sel
        self.exmem_val.rs2 = val.rs2
        self.exmem_val.mem = val.mem
        self.exmem_val.funct3 = val.funct3

        self.writeOutput()


    def process(self):
        # Read inputs
        val: IDEX_t = self.IDEX_i.read()
        opcode = val.opcode
        rs1 = val.rs1
        rs2 = val.rs2
        imm = val.imm
        pc = val.pc
        f3 = val.funct3
        f7 = val.funct7

        # Check for branch/jump
        take_branch = False
        if opcode==isa.OPCODES['BRANCH']:
            take_branch = self.branch(f3, rs1, rs2)
        elif opcode==isa.OPCODES['JAL'] or opcode==isa.OPCODES['JALR']:
            take_branch = True

        pc4 = pc+4

        # ALU
        alu_res = self.alu(opcode, rs1, rs2, imm, pc, f3, f7)

        # Check for exceptions
        self.check_exception(take_branch, alu_res, pc)

        # Outputs
        self.exmem_val.take_branch = take_branch
        self.exmem_val.pc4 = pc4
        self.exmem_val.alu_res = alu_res
        self.writeOutput()

    def alu(self, opcode, rs1, rs2, imm, pc, f3, f7):
        """Implements arithmetic-logic unit (ALU)

        Args: TODO
            opcode ([type]): [description]
            rs1 ([type]): [description]
            rs2 ([type]): [description]
            imm ([type]): [description]
            pc ([type]): [description]
            f3 ([type]): [description]
            f7 ([type]): [description]

        Returns:
            ALU result.
        """

        # Helpers
        def _slt(val1, val2):
            """ SLT[I] instruction

            Args:
                val1: Value of register rs1
                val2: rs2 / Sign-extended immediate

            Returns:
                1 if val1 < val2 (signed comparison)
                0 otherwise
            """

            msb_r = getBit(val1, 31)
            msb_i = getBit(val2, 31)

            # Check if both operands are positive
            if (msb_r==0) and (msb_i==0):
                if val1 < val2:
                    return 1
                else:
                    return 0
            # val1 negative; val2 positive
            elif (msb_r==1) and (msb_i==0):
                return 1
            # val1 positive, val2 negative
            elif (msb_r==0) and (msb_i==1):
                return 0
            # both negative
            else:
                if val2 < val1:
                    return 1
                else:
                    return 0

        def _sltu(val1, val2):
            """ SLT[I]U instruction

            Args:
                val1: Value of register rs1
                val2: rs2 / Sign-extended immediate

            Returns:
                1 if val1 < val2 (unsigned comparison)
                0 otherwise
            """

            if val1 < val2:
                return 1
            else:
                return 0

        def _sll(val1, val2):
            """ SLL[I] instruction

            Args:
                val1: Value of register rs1
                val2: rs2 / Immediate

            Returns:
                Logical left shift of val1 by val2 (5 bits)
            """

            return (MASK_32 & (val1<<(0x1f&val2))) # Mask so that bits above bit 31 turn to zero (for Python)

        def _srl(val1, val2):
            """ SRL[I] instruction

            Args:
                val1: Value of register rs1
                val2: rs2 / Immediate

            Returns:
                Logical right shift of val1 by val2 (5 bits)
            """

            return (MASK_32 & (val1>>(0x1f&val2))) # Mask so that bits above bit 31 turn to zero (for Python)

        def _sra(val1, val2):
            """ SRA[I] instruction

            Args:
                val1: Value of register rs1
                val2: rs2 / Immediate

            Returns:
                Arithmetic right shift of val1 by val2 (5 bits)
            """

            msb_r = getBit(val1, 31)
            shamt = 0x1f & val2
            rshift = (MASK_32 & (val1>>shamt)) # Mask so that bits above bit 31 turn to zero (for Python)
            if msb_r==0:
                return rshift 
            else:
                # Fill upper bits with 1s
                return (MASK_32 & (rshift | (0xffffffff<<(XLEN-shamt))))

        # ------------------
        # ALU start
        # ------------------

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

        elif opcode==isa.OPCODES['LOAD'] or opcode==isa.OPCODES['STORE']: # TODO: Could be merged with the upper elif
            alu_res = op1 + op2

        elif opcode==isa.OPCODES['OP-IMM']:
            if f3==0b000: # ADDI
                alu_res = op1 + op2
            elif f3==0b010: # SLTI
                alu_res = _slt(op1, op2)
            elif f3==0b011: # SLTIU
                alu_res = _sltu(op1, op2)
            elif f3==0b100: # XORI
                alu_res = op1 ^ op2
            elif f3==0b110: # ORI
                alu_res = op1 | op2
            elif f3==0b111: # ANDI
                alu_res = op1 & op2
            elif f3==0b001: # SLLI
                if f7==0: # TODO: We could remove this check if IDStage catches f7!=0 case
                    alu_res = _sll(op1, op2)
            elif f3==0b101:
                if f7==0: # SRLI
                    alu_res = _srl(op1, op2)
                elif f7==0b0100000: # SRAI
                    alu_res = _sra(op1, op2)

        elif opcode==isa.OPCODES['OP']:
            if f7==0:
                if f3==0b000: # ADD
                    alu_res = op1 + op2
                elif f3==0b001: # SLL
                    alu_res = _sll(op1, op2)
                elif f3==0b010: # SLT
                    alu_res = _slt(op1, op2)
                elif f3==0b011: # SLTU
                    alu_res = _sltu(op1, op2)
                elif f3==0b100: # XOR
                    alu_res = op1 ^ op2
                elif f3==0b101: # SRL
                    alu_res = _srl(op1, op2)
                elif f3==0b110: # OR
                    alu_res = op1 | op2
                elif f3==0b111: # AND
                    alu_res = op1 & op2

            elif f7==0b0100000:
                if f3==0b000: # SUB
                    alu_res = op1 - op2
                elif f3==0b101: # SRA
                    alu_res = _sra(op1, op2)

        return MASK_32 & alu_res

    def branch(self, f3, rs1, rs2) -> bool:
        """Performs comparison of rs1 and rs2 using comp op given by f3.

        Returns:
            True if branch is taken.
        """

        # Branch less-than (BLT) logic
        def _blt(rs1, rs2):
            if msb_32(rs1)==msb_32(rs2):
                return rs1<rs2
            elif msb_32(rs1)==1:
                return True
            else:
                return False

        if f3==0:               # BEQ
            return rs1==rs2
        elif f3==1:             # BNE
            return rs1!=rs2
        elif f3==4:             # BLT
            return _blt(rs1, rs2)
        elif f3==5:             # BGE
            return not _blt(rs1, rs2)
        elif f3==6:             # BLTU
            return rs1<rs2
        elif f3==7:             # BGEU
            return rs1>=rs2

    def check_exception(self, take_branch, alu_res, pc):
        # --- Branch/jump target misaligned ------
        if take_branch:
            if alu_res & 0x3 != 0:
                raise Exception(f"Target instruction address misaligned exception at PC = 0x{pc:08X}")


class MEMStage(Module):
    """Memory stage.

    Inputs:
        EXMEM_i: Interface from EXStage.

    Outputs:
        MEMWB_o: Interface to WBStage.
    """
    def __init__(self, dmem: Memory):
        self.EXMEM_i = Input(EXMEM_t, self)
        self.MEMWB_o = Output(MEMWB_t, self)

        # Main memory
        self.mem = dmem

    def process(self):
        # Read inputs
        in_val = self.EXMEM_i.read()
        addr = in_val.alu_res
        mem_wdata = in_val.rs2
        op = in_val.mem
        f3 = in_val.funct3

        load_val = 0
        # Don't write by default
        self.mem.we = False
        self.mem.re = False

        self.check_exception(op, addr, f3)

        if op == LOAD:                                          # Read memory
            if f3 == 0: # LB
                load_val = signext(self.mem.read(addr, 1), 8)
            elif f3 == 1: # LH
                load_val = signext(self.mem.read(addr, 2), 16)
            elif f3 == 2: # LW
                load_val = self.mem.read(addr, 4)
            elif f3 == 4: # LBU
                load_val = self.mem.read(addr, 1)
            elif f3 == 5: # LHU
                load_val = self.mem.read(addr, 2)
            else:
                raise Exception('ERROR (MEMStage, process): Illegal f3 {}'.format(f3))

        elif op == STORE:                                       # Store memory
            if f3 == 0: # SB
                self.mem.writeRequest(addr, mem_wdata, 1)
            elif f3 == 1: # SH
                self.mem.writeRequest(addr, mem_wdata, 2)
            elif f3 == 2: # SW
                self.mem.writeRequest(addr, mem_wdata, 4)
            else:
                raise Exception('ERROR (MEMStage, process): Illegal f3 {}'.format(f3))
        # else:
        #     raise Exception('ERROR (MEMStage, process): Invalid op {}'.format(op))

        # TODO: Illegal address execption handling

        # Outputs
        self.MEMWB_o.write(MEMWB_t(
            rd=in_val.rd,
            we=in_val.we,
            alu_res=in_val.alu_res,
            pc4=in_val.pc4,
            mem_rdata=load_val,
            wb_sel=in_val.wb_sel
        ))

    def check_exception(self, op, addr, f3):
        if f3 == 0:
            return

        op_str = "load from" if op == LOAD else "store to"

        if f3 == 1: # Half word
            if addr & 0x1 != 0:
                logger.warn(f"Misaligned {op_str} address 0x{addr:08X}.")
        elif f3 == 2: # Word
            if addr & 0x11 != 0:
                logger.warn(f"Misaligned {op_str} address 0x{addr:08X}.")

class WBStage(Module):
    """Write-back stage.

    Inputs:
        MEMWB_i: Interface from MEMStage.
    """
    def __init__(self, regf: Regfile):
        self.regfile = regf

        self.MEMWB_i = Input(MEMWB_t, self)

    def process(self):
        # Read inputs
        in_val = self.MEMWB_i.read()
        rd = in_val.rd
        we = in_val.we
        alu_res = in_val.alu_res
        pc4 = in_val.pc4
        mem_rdata = in_val.mem_rdata
        wb_sel = in_val.wb_sel

        wb_val = 0
        # Default to no write.
        # If write, then `writeRequest()` below will
        # enable write in regfile.
        self.regfile.we = False

        if we:
            if wb_sel==0: # ALU op
                wb_val = alu_res
            elif wb_sel==1: # PC+4 (JAL)
                wb_val = pc4
            elif wb_sel==2: # Load
                wb_val = mem_rdata
            else:
                raise Exception('ERROR (WBStage, process): Invalid wb_sel {}'.format(wb_sel))

            self.regfile.writeRequest(rd, wb_val)

class BranchUnit(Module):
    """Branch unit.

    Inputs:
        pc_i: Program counter (PC)
        take_branch_i: Whether to take the branch or not
        target_i: Branch target address

    Outputs:
        npc_o: Next PC
    """
    def __init__(self):
        self.pc_i = Input(int, self)
        self.take_branch_i = Input(bool, self)
        self.target_i = Input(int, self)
        self.npc_o = Output(int, self)

    def process(self):
        # Read inputs
        pc = self.pc_i.read()
        take_branch = self.take_branch_i.read()
        target = self.target_i.read()

        # Compute NPC
        npc = pc+4
        if take_branch:
            npc = target

        # Outputs
        self.npc_o.write(npc)