import pytest
from pyv.mem import Memory
from pyv.reg import Reg
from pyv.clocked import Clock, Clocked, MemList, RegList


# A dummy memory
class Mem(Clocked):
    def __init__(self):
        super().__init__()
        MemList.add_to_mem_list(self)
        self.val = 0

    def _prepare_next_val(self):
        self.next_val = 12

    def _tick(self):
        self.val = self.next_val

    def _reset(self):
        pass


def test_init():
    reg1 = Reg(int)
    reg2 = Reg(int)
    mem1 = Mem()
    mem2 = Mem()
    assert RegList._reg_list == [reg1, reg2]
    assert MemList._mem_list == [mem1, mem2]


def test_abstract_methods():
    class Foo(Clocked):
        pass

    with pytest.raises(TypeError):
        _ = Foo()


def test_tick():
    reg1 = Reg(int)
    reg2 = Reg(int)
    mem = Mem()

    reg1._init()
    reg2._init()

    reg1.next.write(43)
    reg2.next.write(45)
    assert mem.val == 0

    Clock.tick()
    assert reg1.cur.read() == 43
    assert reg2.cur.read() == 45
    assert mem.val == 12


def test_clear():
    _ = Reg(int)
    _ = Reg(int)
    _ = Mem()
    _ = Mem()

    Clock.clear()
    assert RegList._reg_list == []
    assert MemList._mem_list == []


def test_reg_mem_chain(sim):
    reg = Reg(int)
    mem = Memory()

    reg._init()
    mem._init()

    mem.write_port.wdata_i.connect(reg.cur)

    reg.cur._val = 42

    reg.next.write(12)
    mem.read_port0.addr_i.write(0)
    mem.write_port.we_i.write(True)
    mem.read_port0.width_i.write(1)

    Clock.tick()
    assert mem.mem[0] == 42
