from pyv.module import Module
from pyv.port import Input, Output
from pyv.reg import Reg
from pyv.util import Container
from pyv.log import logger

class CSRBlock(Module):
    def __init__(self, reset_val, read_only = False):
        super().__init__()
        self.read_only = read_only
        self._csr_reg = Reg(int, reset_val)
        self.we_i = Input(bool)
        self.write_val_i = Input(int)
        self.csr_val_o = Output(int)

        self.csr_val_o << self._csr_reg.cur

    def process(self):
        val = self._csr_reg.cur.read()
        if not self.read_only and self.we_i.read():
            val = self.write_val_i.read()
        self._csr_reg.next.write(val)


class CSRBank(Container):
    def __init__(self):
        super().__init__()
        self.misa = CSRBlock(0x4000_0100, read_only=False)

    def get_csr(self, addr) -> CSRBlock:
        if addr == 0x301:
            return self.misa
        else:
            logger.warn(f"CSR: Ignoring access to invalid/unimplemented CSR {addr}.")


class CSROutMux(Module):
    def __init__(self):
        super().__init__()
        # Inputs
        self.select_i = Input(int)
        self.misa_i = Input(int)

        # Output
        self.out_o = Output(int)

    def process(self):
        addr = self.select_i.read()
        out_val = 0
        if addr == 0x301:
            out_val = self.misa_i.read()

        self.out_o.write(out_val)

class CSRUnit(Module):
    def __init__(self):
        super().__init__()
        self.csr_bank = CSRBank()
        self.out_mux = CSROutMux()

        # TODO: interesting for docs: we shouldn't nest declare PyObjs inside
        # non-PyObjs -> Use Container class
        self.csr_num_i = Input(int, [self.write])
        self.write_val_i = Input(int, [None])
        self.write_en_i = Input(bool, [self.write])
        self.read_val_o = Output(int)

        self.csr_bank.misa.write_val_i << self.write_val_i

        # Out mux
        self.out_mux.select_i << self.csr_num_i
        self.out_mux.misa_i << self.csr_bank.misa.csr_val_o
        self.read_val_o << self.out_mux.out_o

    def _disable_write(self):
        self.csr_bank.misa.we_i.write(False)

    def write(self):
        self._disable_write()
        if self.write_en_i.read():
            addr = self.csr_num_i.read()
            csr = self.csr_bank.get_csr(addr)
            csr.we_i.write(True)
