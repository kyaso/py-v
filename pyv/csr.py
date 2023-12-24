from pyv.module import Module
from pyv.port import Input, Output
from pyv.reg import Reg
from pyv.util import Container

class CSRBlock(Module):
    def __init__(self):
        super().__init__()
        self._csr_reg = Reg(int)
        self.we_i = Input(bool)
        self.write_val_i = Input(int)
        self.csr_val_o = Output(int)

        self.csr_val_o << self._csr_reg.cur

    def process(self):
        val = self._csr_reg.cur.read()
        if self.we_i.read():
            val = self.write_val_i.read()
        self._csr_reg.next.write(val)


class CSRBank(Container):
    def __init__(self):
        super().__init__()

        self.misa = CSRBlock()

class CSRUnit(Module):
    def __init__(self):
        super().__init__()

        self.csr_bank = CSRBank()

        # TODO: interesting for docs: we shouldn't nest declare PyObjs inside
        # non-PyObjs -> Use Container class
        self.csr_num_i = Input(int)
        self.write_val_i = Input(int, [None])
        self.write_en_i = Input(bool, [self.write, self.validate_read_en_write_en])
        self.read_en_i = Input(bool, [self.read, self.validate_read_en_write_en])
        self.read_val_o = Output(int)

        self.csr_bank.misa.write_val_i << self.write_val_i

    def process(self):
        self.read()
        self.write()

    def validate_read_en_write_en(self):
        if self.read_en_i.read() and self.write_en_i.read():
            raise Exception("CSR: Cannot read and write at same time!")

    def read(self):
        read_val = 0
        if self.read_en_i.read():
            addr = self.csr_num_i.read()
            if addr == 0x301:
                read_val = self.csr_bank.misa.csr_val_o.read()

        self.read_val_o.write(read_val)

    def _disable_write(self):
        self.csr_bank.misa.we_i.write(False)

    def write(self):
        self._disable_write()
        if self.write_en_i.read():
            addr = self.csr_num_i.read()
            if addr == 0x301:
                self.csr_bank.misa.we_i.write(True)
