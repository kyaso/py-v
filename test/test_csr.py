import pytest
from pyv.csr import CSRBlock, CSRUnit
from pyv.simulator import Simulator

@pytest.fixture
def csr_block() -> CSRBlock:
    csr = CSRBlock()
    csr._init()
    return csr

class TestCSRBlock:
    def test_read(self, sim: Simulator, csr_block: CSRBlock):
        csr_block._csr_reg.cur._val = 0x42
        assert csr_block.csr_val_o.read() == 0x42

    def test_write(self, sim: Simulator, csr_block: CSRBlock):
        csr_block.we_i.write(True)
        csr_block.write_val_i.write(0x123)
        sim.step()
        assert csr_block.csr_val_o.read() == 0x123

        csr_block.we_i.write(False)
        csr_block.write_val_i.write(0x3)
        sim.step()
        assert csr_block.csr_val_o.read() == 0x123


@pytest.fixture
def csr_unit() -> CSRUnit:
    csr_unit = CSRUnit()
    csr_unit._init()
    return csr_unit

def csr_write(csr_unit: CSRUnit, csr_num: int, value: int, sim: Simulator):
    csr_unit.csr_num_i.write(csr_num)
    csr_unit.write_en_i.write(True)
    csr_unit.write_val_i.write(value)
    sim.step()

def csr_read(csr_unit: CSRUnit, csr_num: int, sim: Simulator):
    csr_unit.read_en_i.write(True)
    csr_unit.csr_num_i.write(csr_num)
    sim.step()
    return csr_unit.read_val_o.read()

def write_and_read(csr_unit: CSRUnit, csr_num: int, value: int, sim: Simulator):
    csr_write(csr_unit, csr_num, value, sim)
    return csr_read(csr_unit, csr_num, sim)


class TestCSRUnit:
    def test_csr_read(self, sim: Simulator, csr_unit: CSRUnit):
        misa = 0x301
        csr_unit.csr_bank.misa._csr_reg.cur._val = 0x456
        assert csr_read(csr_unit, misa, sim) == 0x456

    def test_csr_write(self, sim: Simulator, csr_unit: CSRUnit):
        misa = 0x301
        csr_write(csr_unit, misa, 0x1234, sim)
        assert csr_unit.csr_bank.misa._csr_reg.cur._val == 0x1234

    def test_csr_write_not_enable(self, sim: Simulator, csr_unit: CSRUnit):
        misa = 0x301
        csr_unit.csr_bank.misa._csr_reg.cur._val = 0x1234
        csr_unit.csr_num_i.write(misa)
        csr_unit.write_en_i.write(False)
        csr_unit.write_val_i.write(0x43)
        sim.step()
        assert csr_unit.csr_bank.misa._csr_reg.cur._val == 0x1234

    def test_read_and_write_at_same_time(self, sim: Simulator, csr_unit: CSRUnit):
        csr_unit.read_en_i.write(True)
        csr_unit.write_en_i.write(True)
        with pytest.raises(Exception):
            sim.step()

    def test_non_existent_csr(self):
        assert False, "Test needs to be implemented"

    def test_access_to_debug_csr(self):
        """Machine-mode standard read-write CSRs 0x7A0–0x7BF are reserved for use by the debug system.
            Of these CSRs, 0x7A0–0x7AF are accessible to machine mode, whereas 0x7B0–0x7BF are only visible
            to debug mode. Implementations should raise illegal instruction exceptions on machine-mode access
            to the latter set of registers
        """
        assert False, "Test needs to be implemented"

