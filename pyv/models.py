from pyv.stages import IFStage, IDStage, EXStage, MEMStage, WBStage, BranchUnit
from pyv.mem import Memory
from pyv.reg import Regfile, RegBase
from pyv.module import Module
from pyv.simulator import Simulator

class Model:
    """Base class for all core models.
    """
    def __init__(self, customLog = None):
        self.cycles = 0
        self.sim = Simulator(customLog)

    def run(self, num_cycles=1):
        """Runs the simulation.

        Args:
            num_cycles (int, optional): Number of clock cycles to simulate. Defaults to 1.
        """
        self.sim.run(num_cycles)
    
    def getCycles(self):
        """Get number cycles executed.

        Returns:
            int: Number of executed cycles.
        """
        return self.sim.getCycles()

class SingleCycle(Module):
    """Implements a simple, 5-stage, single cylce RISC-V CPU.

    Default memory size: 8 KiB
    """
    def __init__(self):
        # Stages/modules
        self.regf = Regfile()
        self.mem = Memory(8*1024)
        self.if_stg = IFStage(self.mem)
        self.id_stg = IDStage(self.regf)
        self.ex_stg = EXStage()
        self.mem_stg = MEMStage(self.mem)
        self.wb_stg = WBStage(self.regf)
        self.bu = BranchUnit()

        # Connect stages
        self.if_stg.npc_i        .connect(self.bu.npc_o)
        self.id_stg.IFID_i       .connect(self.if_stg.IFID_o)
        self.ex_stg.IDEX_i       .connect(self.id_stg.IDEX_o)
        self.mem_stg.EXMEM_i     .connect(self.ex_stg.EXMEM_o)
        self.wb_stg.MEMWB_i      .connect(self.mem_stg.MEMWB_o)
        self.bu.pc_i             .connect(self.if_stg.IFID_o['pc'])
        self.bu.take_branch_i    .connect(self.ex_stg.EXMEM_o['take_branch'])
        self.bu.target_i         .connect(self.ex_stg.EXMEM_o['alu_res']) 

class SingleCycleModel(Model):
    """Model wrapper for SingleCycle."""

    def __init__(self):
        #super().__init__(self.log)
        super().__init__()

        self.core = SingleCycle()
    
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
        addr = 0
        for i in instructions:
            self.core.if_stg.imem.write(addr, i, 4)
            addr+=4
    
    def load_binary(self, file):
        """Load a program binary into the instruction memory.

        Args:
            file (string): Path to the binary.
        """
        f = open(file, 'rb')
        ba = bytearray(f.read())
        f.close()
        inst = list(ba)

        self.core.if_stg.imem.mem[:len(inst)] = inst
    
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
        return [hex(self.core.mem_stg.mem.read(addr+i, 1))  for i in range(0, nbytes)]
    
    def readInstMem(self, addr, nbytes):
        """Read bytes from instruction memory.

        Args:
            addr (int): Address to read from
            nbytes (int): How many bytes to read starting from `addr`.

        Returns:
            list: List of bytes.
        """
        return [hex(self.core.if_stg.imem.read(addr+i, 1))  for i in range(0, nbytes)]