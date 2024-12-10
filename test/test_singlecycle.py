import pytest

from pyv.models.singlecycle import SingleCycle
from pyv.simulator import Simulator


@pytest.fixture
def core() -> SingleCycle:
    core = SingleCycle()
    core.name = "core"
    core._init()
    return core


def mem_write_word(core: SingleCycle, addr, val):
    mem = core.mem.mem
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
        mem_write_word(core, 0, inst)
        mem_write_word(core, 4, nop)
        sim.run(2, False)
        assert core.regf.regs[5] == 0x4000_0100
        assert core.csr_unit.read(0x301) == 0xdeadbeef

    def test_csrrw_no_read(self, sim: Simulator, core: SingleCycle):
        sim.reset()

        # csrrw x0, misa, x12
        inst = 0x30161073
        nop = 0x13
        core.regf.regs[12] = 0xdeadbeef
        mem_write_word(core, 0, inst)
        mem_write_word(core, 4, nop)
        sim.run(2, False)
        assert core.regf.regs[5] != 0x4000_0100
        assert core.csr_unit.read(0x301) == 0xdeadbeef

    def test_csrrs(self, sim: Simulator, core: SingleCycle):
        sim.reset()

        # csrrs x5, misa, x12
        inst = 0x301622f3
        nop = 0x13
        core.regf.regs[12] = 0xdeadbeef
        mem_write_word(core, 0, inst)
        mem_write_word(core, 4, nop)
        sim.run(2, False)
        assert core.regf.regs[5] == 0x4000_0100
        assert core.csr_unit.read(0x301) == 0xdeadbfef

    def test_csrrc(self, sim: Simulator, core: SingleCycle):
        sim.reset()

        # csrrc x5, misa, x12
        inst = 0x301632f3
        nop = 0x13
        core.regf.regs[12] = 0xdeadbeef
        mem_write_word(core, 0, inst)
        mem_write_word(core, 4, nop)
        sim.run(2, False)
        assert core.regf.regs[5] == 0x4000_0100
        assert core.csr_unit.read(0x301) == 0x100

    def test_csrrs_no_write(self, sim: Simulator, core: SingleCycle):
        sim.reset()

        # csrrs x5, misa, x0
        inst = 0x301022f3
        nop = 0x13
        mem_write_word(core, 0, inst)
        mem_write_word(core, 4, nop)
        sim.run(2, False)
        assert core.regf.regs[5] == 0x4000_0100
        assert core.csr_unit.read(0x301) == 0x4000_0100

    def test_csrrwi(self, sim: Simulator, core: SingleCycle):
        sim.reset()

        # csrrwi x5, misa, 26
        inst = 0x301d52f3
        nop = 0x13
        mem_write_word(core, 0, inst)
        mem_write_word(core, 4, nop)
        sim.run(2, False)
        assert core.regf.regs[5] == 0x4000_0100
        assert core.csr_unit.read(0x301) == 26

    def test_csrrsi(self, sim: Simulator, core: SingleCycle):
        sim.reset()

        # csrrsi x5, misa, 26
        inst = 0x301d62f3
        nop = 0x13
        mem_write_word(core, 0, inst)
        mem_write_word(core, 4, nop)
        sim.run(2, False)
        assert core.regf.regs[5] == 0x4000_0100
        assert core.csr_unit.read(0x301) == 0x4000_011A

    def test_csrrci(self, sim: Simulator, core: SingleCycle):
        sim.reset()

        # csrrci x5, misa, 26
        inst = 0x301d72f3
        nop = 0x13
        mem_write_word(core, 0, inst)
        mem_write_word(core, 4, nop)
        sim.run(2, False)
        assert core.regf.regs[5] == 0x4000_0100
        assert core.csr_unit.read(0x301) == 0x4000_0100


class TestExceptions:
    def test_ecall(self, sim: Simulator, core: SingleCycle):
        sim.reset()

        inst = 0x73
        nop = 0x13
        mtvec_addr = 0x305
        mepc_addr = 0x341
        mcause_addr = 0x342
        mtvec = 16
        core.csr_unit._dbg_set_csr(mtvec_addr, mtvec)
        mem_write_word(core, 0, nop)
        mem_write_word(core, 4, inst)
        mem_write_word(core, 16, nop)
        sim.run(3, False)
        assert core.csr_unit.read(mepc_addr) == 4
        assert core.csr_unit.read(mcause_addr) == 11
        assert core.pc.read() == mtvec

    def test_mret(self, sim: Simulator, core: SingleCycle):
        sim.reset()

        inst = 0x30200073
        nop = 0x13
        mepc_addr = 0x341
        mepc = 16
        core.csr_unit._dbg_set_csr(mepc_addr, mepc)
        mem_write_word(core, 0, nop)
        mem_write_word(core, 4, inst)
        mem_write_word(core, 16, nop)
        sim.run(3, False)
        assert core.pc.read() == mepc
