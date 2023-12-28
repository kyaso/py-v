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
            return None


class CSRUnit(Module):
    def __init__(self):
        super().__init__()
        self.csr_bank = CSRBank()

        # TODO: interesting for docs: we shouldn't nest declare PyObjs inside
        # non-PyObjs -> Use Container class
        self.write_addr_i = Input(int, [self.write])
        self.write_val_i = Input(int, [None])
        self.write_en_i = Input(bool, [self.write])

        self.csr_bank.misa.write_val_i << self.write_val_i

    def _disable_write(self):
        self.csr_bank.misa.we_i.write(False)

    def write(self):
        self._disable_write()
        if self.write_en_i.read():
            addr = self.write_addr_i.read()
            csr = self.csr_bank.get_csr(addr)
            csr.we_i.write(True)

    def read(self, addr):
        csr = self.csr_bank.get_csr(addr)
        if csr is not None:
            return csr.csr_val_o.read()
        else:
            return 0
