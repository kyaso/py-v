import pytest
from pyv.clocked import MemList
from pyv.port import Input, Output
from pyv.mem import Memory
from pyv.simulator import Simulator


@pytest.fixture
def mem() -> Memory:
    mem = Memory()
    mem.mem = [0xef, 0xbe, 0xad, 0xde]
    mem.name = "Memory_DUT"
    mem._init()
    return mem


def test_MemList():
    mem = Memory()
    assert MemList._mem_list == [mem]


class TestInit():
    def test_init(self, mem: Memory):
        assert isinstance(mem.mem, list)

    def test_read_port_0(self, mem: Memory):
        rp0 = mem.read_port0
        assert isinstance(rp0.re_i, Input)
        assert rp0.re_i._type == bool
        assert rp0.re_i._process_method_handler._process_methods == [mem.process_read0]

        assert isinstance(rp0.width_i, Input)
        assert rp0.width_i._type == int
        assert rp0.width_i._process_method_handler._process_methods == [mem.process_read0]

        assert isinstance(rp0.addr_i, Input)
        assert rp0.addr_i._type == int
        assert rp0.addr_i._process_method_handler._process_methods == [mem.process_read0]

        assert isinstance(rp0.rdata_o, Output)
        assert rp0.rdata_o._type == int

    def test_read_port_1(self, mem: Memory):
        rp1 = mem.read_port1
        assert isinstance(rp1.re_i, Input)
        assert rp1.re_i._type == bool
        assert rp1.re_i._process_method_handler._process_methods == [mem.process_read1]

        assert isinstance(rp1.width_i, Input)
        assert rp1.width_i._type == int
        assert rp1.width_i._process_method_handler._process_methods == [mem.process_read1]

        assert isinstance(rp1.addr_i, Input)
        assert rp1.addr_i._type == int
        assert rp1.addr_i._process_method_handler._process_methods == [mem.process_read1]

        assert isinstance(rp1.rdata_o, Output)
        assert rp1.rdata_o._type == int

    def test_write_port(self, mem: Memory):
        # Note: Write port uses width, addr from read port 0, so no need to test
        wp = mem.write_port
        assert isinstance(wp.we_i, Input)
        assert wp.we_i._type == bool

        assert isinstance(wp.wdata_i, Input)
        assert wp.wdata_i._type == int


class TestLoad:
    def test_load_re_disabled(self, sim: Simulator, mem: Memory):
        # Read port 0
        mem.read_port0.re_i.write(False)
        mem.read_port0.addr_i.write(0)
        mem.read_port0.width_i.write(1)

        sim.step()
        assert mem.read_port0.rdata_o.read() == 0

        # Read port 1
        mem.read_port1.re_i.write(False)
        mem.read_port1.addr_i.write(0)
        mem.read_port1.width_i.write(1)

        sim.step()
        assert mem.read_port1.rdata_o.read() == 0

    def test_load_byte(self, sim: Simulator, mem: Memory):
        # Read port 0
        mem.read_port0.re_i.write(True)
        mem.read_port0.addr_i.write(0)
        mem.read_port0.width_i.write(1)

        sim.step()
        assert mem.read_port0.rdata_o.read() == 0xef

        # Read port 1
        mem.read_port1.re_i.write(True)
        mem.read_port1.addr_i.write(0)
        mem.read_port1.width_i.write(1)

        sim.step()
        assert mem.read_port1.rdata_o.read() == 0xef

    def test_load_half_word(self, sim: Simulator, mem: Memory):
        # Read port 0
        mem.read_port0.re_i.write(True)
        mem.read_port0.addr_i.write(0)
        mem.read_port0.width_i.write(2)

        sim.step()
        assert mem.read_port0.rdata_o.read() == 0xbeef

        # Read port 1
        mem.read_port1.re_i.write(True)
        mem.read_port1.addr_i.write(0)
        mem.read_port1.width_i.write(2)

        sim.step()
        assert mem.read_port1.rdata_o.read() == 0xbeef

    def test_load_word(self, sim: Simulator, mem: Memory):
        # Read port 0
        mem.read_port0.re_i.write(True)
        mem.read_port0.addr_i.write(0)
        mem.read_port0.width_i.write(4)

        sim.step()
        assert mem.read_port0.rdata_o.read() == 0xdeadbeef

        # Read port 1
        mem.read_port1.re_i.write(True)
        mem.read_port1.addr_i.write(0)
        mem.read_port1.width_i.write(4)

        sim.step()
        assert mem.read_port1.rdata_o.read() == 0xdeadbeef

    def test_load_misaligned(self, sim: Simulator, mem: Memory):
        # Read port 0
        mem.read_port0.re_i.write(True)
        mem.read_port0.addr_i.write(1)
        mem.read_port0.width_i.write(2)

        sim.step()
        assert mem.read_port0.rdata_o.read() == 0xadbe

        # Read port 1
        mem.read_port1.re_i.write(True)
        mem.read_port1.addr_i.write(1)
        mem.read_port1.width_i.write(2)

        sim.step()
        assert mem.read_port1.rdata_o.read() == 0xadbe

    def test_load_invalid_width(self, sim: Simulator, mem: Memory):
        # Read port 0
        mem.read_port0.re_i.write(True)
        mem.read_port0.addr_i.write(0)
        mem.read_port0.width_i.write(5)

        with pytest.raises(Exception):
            sim.step()

        # Read port 1
        mem.read_port1.re_i.write(True)
        mem.read_port1.addr_i.write(0)
        mem.read_port1.width_i.write(5)

        with pytest.raises(Exception):
            sim.step()

    def test_read_invalid_idx(self, sim: Simulator, mem: Memory):
        # Read port 0
        mem.read_port0.re_i.write(True)
        mem.read_port0.addr_i.write(8)
        mem.read_port0.width_i.write(1)
        # This shouldn't raise an IndexError exception.
        sim.step()
        assert mem.read_port0.rdata_o.read() == 0

        # Read port 1
        mem.read_port1.re_i.write(True)
        mem.read_port1.addr_i.write(8)
        mem.read_port1.width_i.write(1)
        # This shouldn't raise an IndexError exception.
        sim.step()
        assert mem.read_port1.rdata_o.read() == 0


class TestStore:
    def test_store_we_disabled(self, sim: Simulator, mem: Memory):
        mem.write_port.we_i.write(False)
        mem.read_port0.addr_i.write(0)
        mem.write_port.wdata_i.write(42)
        mem.read_port0.width_i.write(1)

        sim.step()
        assert mem.mem[0] == 0xef

    def test_store_byte(self, sim: Simulator, mem: Memory):
        mem.write_port.we_i.write(True)
        mem.read_port0.addr_i.write(0)
        mem.write_port.wdata_i.write(0xaf)
        mem.read_port0.width_i.write(1)

        assert mem.mem[0] == 0xef
        sim.step()
        assert mem.mem[0] == 0xaf

    def test_store_half_word(self, sim: Simulator, mem: Memory):
        mem.write_port.we_i.write(True)
        mem.read_port0.addr_i.write(0)
        mem.write_port.wdata_i.write(0xbabe)
        mem.read_port0.width_i.write(2)

        assert mem.mem[0] == 0xef
        assert mem.mem[1] == 0xbe
        sim.step()
        assert mem.mem[0] == 0xbe
        assert mem.mem[1] == 0xba

    def test_store_word(self, sim: Simulator, mem: Memory):
        mem.write_port.we_i.write(True)
        mem.read_port0.addr_i.write(0)
        mem.write_port.wdata_i.write(0xaffedead)
        mem.read_port0.width_i.write(4)

        assert mem.mem[0] == 0xef
        assert mem.mem[1] == 0xbe
        assert mem.mem[2] == 0xad
        assert mem.mem[3] == 0xde
        sim.step()
        assert mem.mem[0] == 0xad
        assert mem.mem[1] == 0xde
        assert mem.mem[2] == 0xfe
        assert mem.mem[3] == 0xaf

    def test_store_invalid_width(self, sim: Simulator, mem: Memory):
        mem.write_port.we_i.write(True)
        mem.read_port0.addr_i.write(0)
        mem.write_port.wdata_i.write(0xaffedead)
        mem.read_port0.width_i.write(6)

        with pytest.raises(Exception):
            sim.step()
