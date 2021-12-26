from pyv.stages import IFStage, IDStage, EXStage, MEMStage, WBStage, BranchUnit
from pyv.mem import Memory
from pyv.reg import Regfile, RegBase

class Model:
    """Base class for all core models.
    """
    def __init__(self):
        self.stages = []
        self.cycles = 0

    def run(self, num_cycles=1):
        """Runs the simulation.

        Args:
            num_cycles (int, optional): Number of clock cycles to simulate. Defaults to 1.
        """
        for c in range(0, num_cycles):
            for i in self.stages:
                i.process()
            
            RegBase.updateRegs()

            self.cycles += 1

class SingleCycle(Model):
    """Implements a simple, 5-stage, single cylce RISC-V CPU.

    Default memory size: 8 KiB
    """
    def __init__(self):
        super().__init__()

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

        # Define execution order
        self.stages = [ self.if_stg,
                        self.id_stg,
                        self.ex_stg,
                        self.mem_stg,
                        self.wb_stg,
                        self.bu
                      ]
        
    def load_instructions(self, instructions):
        addr = 0
        for i in instructions:
            self.if_stg.imem.write(addr, i, 4)
            addr+=4
    
    def load_binary(self, file):
        f = open(file, 'rb')
        ba = bytearray(f.read())
        f.close()
        inst = list(ba)

        self.if_stg.imem.mem[:len(inst)] = inst
    
    def readReg(self, reg):
        return self.regf.read(reg)
    
    def readPC(self):
        return self.if_stg.pc_reg.cur.read()
    
    def readDataMem(self, addr, nbytes):
        return [hex(self.mem_stg.mem.read(addr+i, 1))  for i in range(0, nbytes)]
    
    def readInstMem(self, addr, nbytes):
        return [hex(self.if_stg.imem.read(addr+i, 1))  for i in range(0, nbytes)]

    def getCycles(self):
        return self.cycles

