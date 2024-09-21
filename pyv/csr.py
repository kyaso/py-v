from pyv.module import Module
from pyv.port import Input, Output, Wire
from pyv.reg import Reg
from pyv.util import VContainer, VMap
from pyv.log import logger
import pyv.isa as isa


class CSRBlock(Module):
    def __init__(self, reset_val=0, read_only=False, read_mask=0xFFFF_FFFF):
        super().__init__()
        self.read_only = read_only
        self._read_mask = read_mask
        self._csr_reg = Reg(int, reset_val)
        self.we_i = Input(bool)
        self.write_val_i = Input(int)
        self.csr_val_o = Output(int)
        self.csr_val_w = Wire(int, [self.output])

        self.csr_val_w << self._csr_reg.cur

    def process(self):
        val = self._csr_reg.cur.read()
        if not self.read_only and self.we_i.read():
            val = self.write_val_i.read()
        self._csr_reg.next.write(val)

    def output(self):
        val = self.csr_val_w.read()
        self.csr_val_o.write(val & self._read_mask)


class CSRBank(VContainer):
    def __init__(self, write_val: Input):
        super().__init__()
        self.csrs = VMap({
            isa.CSR["misa"]["addr"]: CSRBlock(
                reset_val=0x4000_0100
            ),
            isa.CSR["mepc"]["addr"]: CSRBlock(
                read_mask=isa.CSR["mepc"]["read_mask"]
            ),
            isa.CSR["mcause"]["addr"]: CSRBlock(),
            isa.CSR["mtvec"]["addr"]: CSRBlock(
                read_mask=isa.CSR["mtvec"]["read_mask"]
            ),
        })
        self.connect_write_val(write_val)

    def get_csr(self, addr) -> CSRBlock:
        try:
            return self.csrs[addr]
        except KeyError:
            logger.warning(
                f"CSR: Ignoring access to invalid/unimplemented CSR {addr}.")
            return None

    def connect_write_val(self, write_val: Input):
        csr: CSRBlock
        for _, csr in self.csrs.items():
            csr.write_val_i << write_val

    def disable_write(self):
        csr: CSRBlock
        for _, csr in self.csrs.items():
            csr.we_i.write(False)

    def _dbg_set_csr(self, addr, val):
        self.csrs[addr]._csr_reg.cur._val = val

    def _dbg_get_csr(self, addr):
        return self.csrs[addr]._csr_reg.cur._val


class CSRUnit(Module):
    def __init__(self):
        super().__init__()

        # TODO: interesting for docs: we shouldn't nest declare PyObjs inside
        # non-PyObjs -> Use Container class
        self.write_addr_i = Input(int, [self.write])
        self.write_val_i = Input(int, [None])
        self.write_en_i = Input(bool, [self.write])

        self.csr_bank = CSRBank(self.write_val_i)

    def _disable_write(self):
        self.csr_bank.disable_write()

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

    def _dbg_set_csr(self, addr, val):
        self.csr_bank._dbg_set_csr(addr, val)

    def _dbg_get_csr(self, addr):
        return self.csr_bank._dbg_get_csr(addr)
