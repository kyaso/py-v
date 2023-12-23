from pyv.module import Module
from pyv.port import Input, Output
from pyv.reg import Reg
from pyv.util import Container


class CSRBank(Container):
    def __init__(self):
        super().__init__()
        self.misa = Reg(int, 0x42)


class CSRUnit(Module):
    def __init__(self):
        super().__init__()

        self.csr_bank = CSRBank()
        # TODO: interesting for docs: we shouldn't nest declare PyObjs inside
        # non-PyObjs -> Use Container class
        self._CSR_MAP = {
            0x301: self.csr_bank.misa
        }

        self.csr_num_i = Input(int)
        self.write_val_i = Input(int, [self.write])
        self.write_en_i = Input(bool, [self.write])
        self.read_val_o = Output(int)

    def process(self):
        self.read()
        self.write()

    def read(self):
        addr = self.csr_num_i.read()
        csr_val = self._CSR_MAP[addr].cur.read()
        self.read_val_o.write(csr_val)

    def write(self):
        if self.write_en_i.read():
            addr = self.csr_num_i.read()
            write_val = self.write_val_i.read()
            self._CSR_MAP[addr].next.write(write_val)
