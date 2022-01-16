import pytest
from pyv.reg import Reg
from pyv.clocked import Clock, MemBase, RegBase

# A dummy memory
class Mem(MemBase):
    def __init__(self):
        super().__init__()
        self.val = 0
    
    def _tick(self):
        self.val = 12

def test_init():
    reg1 = Reg()
    reg2 = Reg()
    mem1 = Mem()
    mem2 = Mem()
    assert RegBase._reg_list == [reg1, reg2]
    assert MemBase._mem_list == [mem1, mem2]

def test_abstractMethods():
    class Foo(Clock):
        pass

    class Bar(MemBase):
        pass

    foo = Foo()
    bar = Bar()

    with pytest.raises(NotImplementedError):
        foo._tick()
    
    with pytest.raises(NotImplementedError):
        foo._reset()
    
    with pytest.raises(NotImplementedError):
        bar._tick()
    
    with pytest.raises(NotImplementedError):
        bar._reset()

def test_tick():
    Clock.clear()

    reg1 = Reg()
    reg2 = Reg()
    mem = Mem()

    reg1.next.write(43)
    reg2.next.write(45)
    assert mem.val == 0

    Clock.tick()
    assert reg1.cur.read() == 43
    assert reg2.cur.read() == 45
    assert mem.val == 12

def test_clear():
    Clock.clear()

    reg1 = Reg()
    reg2 = Reg()
    mem1 = Mem()
    mem2 = Mem()

    Clock.clear()
    assert RegBase._reg_list == []
    assert MemBase._mem_list == []
