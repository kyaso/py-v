import pytest
from pyv.csr import CSRUnit
from pyv.exception_unit import ExceptionUnit
from pyv.module import Module
from pyv.port import Input, Output
from pyv.simulator import Simulator
from pyv.test_utils import check_port
from pyv.isa import CSR


class TestExceptionUnit:
    @pytest.fixture
    def eu(self) -> ExceptionUnit:
        csr = CSRUnit()
        csr._dbg_set_csr(CSR['mtvec']['addr'], 0xFFFF_FFF1)
        csr._dbg_set_csr(CSR['mepc']['addr'], 0xFFFF_FFFE)
        eu = ExceptionUnit(csr)
        eu._init()
        return eu

    def test_init(self, eu: ExceptionUnit):
        assert isinstance(eu, Module)

    def test_ports(self, eu: ExceptionUnit):
        check_port(eu.ecall_i, Input, bool)
        check_port(eu.pc_i, Input, int)
        check_port(eu.mret_i, Input, bool)

        check_port(eu.raise_exception_o, Output, bool)
        check_port(eu.npc_o, Output, int)
        check_port(eu.mcause_o, Output, int)
        check_port(eu.mepc_o, Output, int)
        check_port(eu.trap_return_o, Output, bool)

    def test_ecall(self, eu: ExceptionUnit, sim: Simulator):
        eu.ecall_i.write(True)
        eu.pc_i.write(0x4000_0004)
        sim.run_comb_logic()
        assert eu.raise_exception_o.read() == True
        assert eu.npc_o.read() == 0xFFFF_FFF1
        assert eu.mcause_o.read() == 11
        assert eu.mepc_o.read() == 0x4000_0004

        # Check no ecall
        eu.ecall_i.write(False)
        sim.run_comb_logic()
        assert eu.raise_exception_o.read() == False
        assert eu.npc_o.read() == 0

    def test_mret(self, eu: ExceptionUnit, sim: Simulator):
        eu.ecall_i.write(False)
        eu.mret_i.write(True)
        eu.pc_i.write(0x4000_0004)
        sim.run_comb_logic()
        assert eu.trap_return_o.read() == True
        assert eu.npc_o.read() == 0xFFFF_FFFE
