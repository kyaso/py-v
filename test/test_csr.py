import pytest
from pyv import isa
from pyv.clocked import Clock
from pyv.csr import CSRBank, CSRBlock, CSRUnit
from pyv.simulator import Simulator


@pytest.fixture
def csr_block() -> CSRBlock:
    csr = CSRBlock(reset_val=0, read_only=False, read_mask=0xFFFF_FFFF)
    csr._init()
    return csr


class TestCSRBlock:
    def test_read(self, sim: Simulator, csr_block: CSRBlock):
        csr_block._csr_reg.cur._val = 0x42
        sim.step()
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

    def test_read_with_mask(self, sim: Simulator, csr_block: CSRBlock):
        csr_block._read_mask = 0xDEAD_BEEF
        csr_block._csr_reg.cur._val = 0xFFFF_FFFF
        sim.step()
        assert csr_block.csr_val_o.read() == 0xDEAD_BEEF


@pytest.fixture
def csr_bank() -> CSRBank:
    bank = CSRBank()
    return bank


class TestCSRBank:
    def test_get_csr(self, csr_bank: CSRBank):
        assert csr_bank.get_csr(0x301) == csr_bank.csrs[0x301]

    def test_get_invalid_csr(self, csr_bank: CSRBank):
        assert csr_bank.get_csr(1) is None

    def test_set_write_val(self, csr_bank: CSRBank):
        csr_addr = isa.CSR["mepc"]["addr"]
        csr_bank.set_write_val(csr_addr, 0xdeadbeef)
        assert csr_bank.csrs[csr_addr].write_val_i.read() == 0xdeadbeef

    def test_set_write_en(self, csr_bank: CSRBank):
        csr_addr = isa.CSR["mepc"]["addr"]
        csr_bank.set_write_en(csr_addr)
        assert csr_bank.csrs[csr_addr].we_i.read() == True

    def test_disable_write(self, csr_bank: CSRBank):
        csr: CSRBlock
        for _, csr in csr_bank.csrs.items():
            csr.we_i.write(True)

        csr_bank.disable_write()

        for _, csr in csr_bank.csrs.items():
            assert csr.we_i.read() == False

    def test_exception_we(self, csr_bank: CSRBank):
        csr_bank.set_exception_we()
        assert csr_bank.csrs[isa.CSR["mepc"]["addr"]].we_i.read() == True
        assert csr_bank.csrs[isa.CSR["mcause"]["addr"]].we_i.read() == True

    def test_exception_write_val(self, csr_bank: CSRBank):
        csr_bank.set_exception_write_val(
            mepc=0xdeadbeef,
            mcause=0xaffeaffe
        )
        assert csr_bank.csrs[isa.CSR["mepc"]["addr"]].write_val_i.read() == 0xdeadbeef
        assert csr_bank.csrs[isa.CSR["mcause"]["addr"]].write_val_i.read() == 0xaffeaffe

    def test_dbg_set_get(self, csr_bank: CSRBank):
        misa = 0x301
        csr_bank._dbg_set_csr(misa, 0xdeadbeef)
        assert csr_bank.csrs[misa]._csr_reg.cur._val == 0xdeadbeef
        assert csr_bank._dbg_get_csr(misa) == 0xdeadbeef


@pytest.fixture
def csr_unit() -> CSRUnit:
    csr_unit = CSRUnit()
    csr_unit._init()
    Clock.reset()
    return csr_unit


def csr_write(csr_unit: CSRUnit, csr_num: int, value: int, sim: Simulator):
    csr_unit.write_addr_i.write(csr_num)
    csr_unit.write_en_i.write(True)
    csr_unit.write_val_i.write(value)
    sim.step()


def csr_read(csr_unit: CSRUnit, csr_num: int):
    return csr_unit.read(csr_num)


class TestCSRUnit:
    def test_dbg_set_get(self, csr_unit: CSRUnit):
        misa = 0x301
        csr_unit._dbg_set_csr(misa, 0xdeadbeef)
        assert csr_unit.csr_bank.csrs[misa]._csr_reg.cur._val == 0xdeadbeef
        assert csr_unit._dbg_get_csr(misa) == 0xdeadbeef

    def test_csr_read(self, sim: Simulator, csr_unit: CSRUnit):
        misa = 0x301
        csr_unit._dbg_set_csr(misa, 0x456)
        sim.step()
        assert csr_read(csr_unit, misa) == 0x456

    def test_csr_write(self, sim: Simulator, csr_unit: CSRUnit):
        misa = 0x301
        csr_write(csr_unit, misa, 0x1234, sim)
        assert csr_unit._dbg_get_csr(misa) == 0x1234

    def test_csr_write_not_enable(self, sim: Simulator, csr_unit: CSRUnit):
        misa = 0x301
        csr_unit.csr_bank.csrs[misa]._csr_reg.cur._val = 0x1234
        csr_unit.write_addr_i.write(misa)
        csr_unit.write_en_i.write(False)
        csr_unit.write_val_i.write(0x43)
        sim.step()
        assert csr_unit._dbg_get_csr(misa) == 0x1234

    def test_read_and_write_in_same_cycle(self, sim: Simulator, csr_unit: CSRUnit):
        csr_unit.write_addr_i.write(0x301)
        csr_unit.write_en_i.write(False)
        sim.step()
        csr_unit.write_en_i.write(True)
        csr_unit.write_val_i.write(0x42)
        assert csr_read(csr_unit, 0x301) == 0x4000_0100
        sim.step()
        assert csr_read(csr_unit, 0x301) == 0x42

    def test_m_mode_csrs(self, sim: Simulator, csr_unit: CSRUnit):
        def run_check(csr_addr, expected_reset_val, expected_read_back):
            sim.step()
            reset_val = csr_read(csr_unit, csr_addr)
            assert reset_val == expected_reset_val

            csr_write(csr_unit, csr_addr, 0xFFFF_FFFF, sim)
            read_back = csr_read(csr_unit, csr_addr)
            assert read_back == expected_read_back

        # ---- misa ----
        run_check(0x301, 0x4000_0100, 0xFFFF_FFFF)

        # ---- mepc ----
        run_check(0x341, 0, 0xFFFF_FFFE)

        # ---- mcause ----
        run_check(0x342, 0, 0xFFFF_FFFF)

        # ---- mtvec -----
        run_check(0x305, 0, 0xFFFF_FFF1)


class TestException:
    mepc = 0x341
    mcause = 0x342

    def test_mepc_is_set_during_exception(self, csr_unit: CSRUnit, sim: Simulator):
        csr_unit.ex_i.write(True)
        csr_unit.write_en_i.write(True)
        csr_unit.mepc_i.write(0xdeadbeef)
        sim.step()
        assert csr_unit._dbg_get_csr(self.mepc) == 0xdeadbeef

    def test_mepc_is_not_set_when_no_exception(self, csr_unit: CSRUnit, sim: Simulator):
        csr_unit._dbg_set_csr(self.mepc, 0x8000_0000)
        csr_unit.ex_i.write(False)
        csr_unit.mepc_i.write(0)
        sim.step()
        assert csr_unit._dbg_get_csr(self.mepc) == 0x8000_0000

    def test_mcause_is_set_during_exception(self, csr_unit: CSRUnit, sim: Simulator):
        csr_unit.ex_i.write(True)
        csr_unit.write_en_i.write(True)
        csr_unit.mcause_i.write(0xdeadbeef)
        sim.step()
        assert csr_unit._dbg_get_csr(self.mcause) == 0xdeadbeef

    def test_mcause_is_not_set_when_no_exception(self, csr_unit: CSRUnit, sim: Simulator):
        csr_unit._dbg_set_csr(self.mcause, 0x8000_0000)
        csr_unit.ex_i.write(False)
        csr_unit.mcause_i.write(0)
        sim.step()
        assert csr_unit._dbg_get_csr(self.mcause) == 0x8000_0000
