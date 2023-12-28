from pyv.csr import CSRUnit
from pyv.stages import EXMEM_t, IFID_t, IFStage, IDStage, EXStage, MEMStage, \
    WBStage, BranchUnit
from pyv.mem import Memory
from pyv.reg import Regfile
from pyv.module import Module
from pyv.models.model import Model
from pyv.port import Wire


class SingleCycle(Module):
    """Implements a simple, 5-stage, single cylce RISC-V CPU.

    Default memory size: 8 KiB
    """
    def __init__(self):
        super().__init__()
        # Stages/modules
        self.regf = Regfile()
        """RISC-V 32-bit base register file"""
        self.csr_unit = CSRUnit()
        """RISC-V CSRs"""
        self.mem = Memory(8 * 1024)
        """Main Memory (for both instructions and data)"""
        self.if_stg = IFStage(self.mem.read_port1)
        """Instruction Fetch"""
        self.id_stg = IDStage(self.regf, self.csr_unit)
        """Instruction Decode"""
        self.ex_stg = EXStage()
        """Execute"""
        self.mem_stg = MEMStage(self.mem.read_port0, self.mem.write_port)
        """Mem stage"""
        self.wb_stg = WBStage(self.regf)
        """Write-back"""
        self.bu = BranchUnit()
        """Branch unit"""

        # Wires
        self.IFID = Wire(IFID_t, sensitive_methods=[self.connects])
        self.EXMEM = Wire(EXMEM_t, sensitive_methods=[self.connects])
        self.pc = Wire(int)
        self.take_branch = Wire(bool)
        self.alu_res = Wire(int)

        self.IFID << self.if_stg.IFID_o
        self.EXMEM << self.ex_stg.EXMEM_o

        # Connect stages
        self.if_stg.npc_i     << self.bu.npc_o
        self.id_stg.IFID_i    << self.if_stg.IFID_o
        self.ex_stg.IDEX_i    << self.id_stg.IDEX_o
        self.mem_stg.EXMEM_i  << self.ex_stg.EXMEM_o
        self.wb_stg.MEMWB_i   << self.mem_stg.MEMWB_o
        self.bu.pc_i          << self.pc
        self.bu.take_branch_i << self.take_branch
        self.bu.target_i      << self.alu_res

        # Connect WBStage to CSR unit
        self.csr_unit.write_en_i << self.wb_stg.csr_write_en_o
        self.csr_unit.write_addr_i << self.wb_stg.csr_write_addr_o
        self.csr_unit.write_val_i << self.wb_stg.csr_write_val_o

    def connects(self):
        val = self.IFID.read().pc
        self.pc.write(val)

        val = self.EXMEM.read()
        self.take_branch.write(val.take_branch)
        self.alu_res.write(val.alu_res)


class SingleCycleModel(Model):
    """Model wrapper for SingleCycle."""

    def __init__(self):
        self.core = SingleCycle()
        """Module instance"""
        self.setTop(self.core, 'SingleCycleTop')

        super().__init__()

    def log(self):
        """Custom log function.

        We pass it to the simulator in the constructor.
        """
        print("PC = 0x%08X" % self.core.if_stg.pc_reg.cur.read())
        print("IR = 0x%08X" % self.core.if_stg.ir_reg.cur.read())

    def load_instructions(self, instructions):
        """Load instructions into the instruction memory.

        Args:
            instructions (list): List of instruction words.
        """
        self.core.mem.mem[:len(instructions)] = instructions

    def load_binary(self, file):
        """Load a program binary into the instruction memory.

        Args:
            file (string): Path to the binary.
        """
        f = open(file, 'rb')
        ba = bytearray(f.read())
        f.close()
        inst = list(ba)

        self.core.mem.mem[:len(inst)] = inst

    def readReg(self, reg):
        """Read a register in the register file.

        Args:
            reg (int): index of register to be read.

        Returns:
            int: Value of register.
        """
        return self.core.regf.read(reg)

    def readPC(self):
        """Read current program counter (PC).

        Returns:
            int: current program counter
        """
        return self.core.if_stg.pc_reg.cur.read()

    def readDataMem(self, addr, nbytes):
        """Read bytes from data memory.

        Args:
            addr (int): Address to read from
            nbytes (int): How many bytes to read starting from `addr`.

        Returns:
            list: List of bytes.
        """
        return [hex(self.core.mem.mem[addr + i]) for i in range(0, nbytes)]

    def readInstMem(self, addr, nbytes):
        """Read bytes from instruction memory.

        Args:
            addr (int): Address to read from
            nbytes (int): How many bytes to read starting from `addr`.

        Returns:
            list: List of bytes.
        """
        return [hex(self.core.mem.mem[addr + i]) for i in range(0, nbytes)]
