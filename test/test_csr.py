import pytest
from pyv.clocked import Clock
from pyv.csr import CSRBlock, CSRUnit
from pyv.simulator import Simulator

@pytest.fixture
def csr_block() -> CSRBlock:
    csr = CSRBlock(0)
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
    Clock.reset()
    return csr_unit

def csr_write(csr_unit: CSRUnit, csr_num: int, value: int, sim: Simulator):
    csr_unit.csr_num_i.write(csr_num)
    csr_unit.write_en_i.write(True)
    csr_unit.write_val_i.write(value)
    sim.step()

def csr_read(csr_unit: CSRUnit, csr_num: int, sim: Simulator):
    csr_unit.write_en_i.write(False)
    csr_unit.csr_num_i.write(csr_num)
    sim.step()
    return csr_unit.read_val_o.read()


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

    def test_read_and_write_in_same_cycle(self, sim: Simulator, csr_unit: CSRUnit):
        csr_unit.csr_num_i.write(0x301)
        csr_unit.write_en_i.write(False)
        sim.step()
        csr_unit.write_en_i.write(True)
        csr_unit.write_val_i.write(0x42)
        assert csr_unit.read_val_o.read() == 0x4000_0100
        sim.step()
        # Second step is required to run process method of CSROutMux
        sim.step()
        assert csr_unit.read_val_o.read() == 0x42


    def test_m_mode_csrs(self, sim: Simulator, csr_unit: CSRUnit):
        # ---- misa ----
        misa = 0x301
        reset_val = csr_read(csr_unit, misa, sim)
        assert reset_val == 0x4000_0100

        csr_write(csr_unit, misa, 0xFFFF_FFFF, sim)
        read_back = csr_read(csr_unit, misa, sim)
        assert read_back == 0xFFFF_FFFF
