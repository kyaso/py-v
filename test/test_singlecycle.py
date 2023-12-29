import pytest

from pyv.models.singlecycle import SingleCycle
from pyv.simulator import Simulator

@pytest.fixture
def core() -> SingleCycle:
    core = SingleCycle()
    core.name = "core"
    core._init()
    return core

def mem_write_word(mem: list, addr, val):
    for i in range(4):
        mem[addr + i] = 0xff & val
        val >>= 8

class TestCSR:
    def test_csrrw(self, sim: Simulator, core: SingleCycle):
        sim.reset()

        # csrrw x5, misa, x12
        inst = 0x301612f3
        nop = 0x13
        core.regf.regs[12] = 0xdeadbeef
        mem_write_word(core.mem.mem, 0, inst)
        mem_write_word(core.mem.mem, 4, nop)
        sim.run(2, False)
        assert core.regf.regs[5] == 0x4000_0100
        assert core.csr_unit.read(0x301) == 0xdeadbeef

    def test_csrrs(self, sim: Simulator, core: SingleCycle):
        sim.reset()

        # csrrs x5, misa, x12
        inst = 0x301622f3
        nop = 0x13
        core.regf.regs[12] = 0xdeadbeef
        mem_write_word(core.mem.mem, 0, inst)
        mem_write_word(core.mem.mem, 4, nop)
        sim.run(2, False)
        assert core.regf.regs[5] == 0x4000_0100
        assert core.csr_unit.read(0x301) == 0xdeadbfef
