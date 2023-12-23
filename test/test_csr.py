import pytest
from pyv.csr import CSRUnit
from pyv.simulator import Simulator


@pytest.fixture
def csr_unit() -> CSRUnit:
    csr_unit = CSRUnit()
    csr_unit._init()
    return csr_unit


class TestCSRUnit:
    def test_csr_read(self, sim: Simulator, csr_unit: CSRUnit):
        misa = 0x301
        csr_unit.csr_bank.misa.cur._val = 0x2
        csr_unit.csr_num_i.write(misa)
        sim.step()
        assert csr_unit.read_val_o.read() == 0x2

    def test_csr_write(self, sim: Simulator, csr_unit: CSRUnit):
        misa = 0x301
        csr_unit.csr_num_i.write(misa)

        csr_unit.write_en_i.write(True)
        csr_unit.write_val_i.write(0x1234)
        sim.step()
        assert csr_unit.csr_bank.misa.cur._val == 0x1234

        csr_unit.write_en_i.write(False)
        csr_unit.write_val_i.write(0x43)
        sim.step()
        assert csr_unit.csr_bank.misa.cur._val == 0x1234

    def test_non_existent_csr(self):
        assert False, "Test needs to be implemented"

    def test_access_to_debug_csr(self):
        """Machine-mode standard read-write CSRs 0x7A0–0x7BF are reserved for use by the debug system.
            Of these CSRs, 0x7A0–0x7AF are accessible to machine mode, whereas 0x7B0–0x7BF are only visible
            to debug mode. Implementations should raise illegal instruction exceptions on machine-mode access
            to the latter set of registers
        """
        assert False, "Test needs to be implemented"
