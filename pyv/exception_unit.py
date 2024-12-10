from pyv.csr import CSRUnit
from pyv.module import Module
from pyv.port import Input, Output
from pyv.isa import CSR


class ExceptionUnit(Module):
    def __init__(self, csr: CSRUnit, name='UnnamedModule'):
        super().__init__(name)

        self.csr = csr

        self.pc_i = Input(int, [None])
        self.ecall_i = Input(bool)
        self.mret_i = Input(bool)

        self.raise_exception_o = Output(bool)
        self.npc_o = Output(int)
        self.mcause_o = Output(int)
        self.mepc_o = Output(int)
        self.trap_return_o = Output(bool)

        self.mepc_o << self.pc_i

    def process(self):
        ecall = self.ecall_i.read()
        mret = self.mret_i.read()
        raise_ex = False
        npc = 0
        mcause = 0xFFFF_FFFF
        trap_return = False

        if ecall:
            raise_ex = True
            npc = self.csr.read(CSR['mtvec']['addr'])
            mcause = 11
        elif mret:
            trap_return = True
            npc = self.csr.read(CSR['mepc']['addr'])

        self.raise_exception_o.write(raise_ex)
        self.npc_o.write(npc)
        self.mcause_o.write(mcause)
        self.trap_return_o.write(trap_return)
