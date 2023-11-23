import pytest
from pyv.module import Module
from pyv.reg import Reg
from pyv.clocked import Clock, Clocked, MemBase, RegBase

# A dummy memory
class Mem(MemBase):
    def __init__(self):
        super().__init__()
        self.val = 0
    
    def _tick(self):
        self.val = 12

def test_init():
    reg1 = Reg(int)
    reg2 = Reg(int)
    mem1 = Mem()
    mem2 = Mem()
    assert RegBase._reg_list == [reg1, reg2]
    assert MemBase._mem_list == [mem1, mem2]

def test_abstractMethods():
    class Foo(Clocked):
        pass

    with pytest.raises(TypeError):
        foo = Foo()

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
    reg1 = Reg(int)
    reg2 = Reg(int)
    mem1 = Mem()
    mem2 = Mem()

    Clock.clear()
    assert RegBase._reg_list == []
    assert MemBase._mem_list == []
