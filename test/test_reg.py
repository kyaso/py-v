from unittest.mock import MagicMock
import pytest
import random
from pyv.reg import *
from pyv.clocked import RegBase

@pytest.fixture
def reg():
    reg = Reg(int)
    reg._init()
    return reg

def test_reg_init():
    reg = Reg(float, 42)

    assert reg.next._type == float
    assert reg.cur._type == float
    assert reg.rst._type == int
    assert reg._resetVal == 42

def test_reg(reg):
    RegBase.reset()
    assert reg.cur.read() == 0

    reg.next.write(0x42)
    assert reg.cur.read() == 0

    RegBase.tick()
    assert reg.cur.read() == 0x42

    reg.next.write(0x69)
    assert reg.cur.read() == 0x42

    RegBase.tick()
    assert reg.cur.read() == 0x69

def test_reg_tick(reg):
    reg.next.write(42)
    RegBase.tick()
    assert reg._doTick == True
    assert reg.cur._val == 42

    # Tick again, but as port value is unchanged, register should skip _tick
    reg.cur.write = MagicMock()
    RegBase.tick()
    assert reg._doTick == False
    reg.cur.write.assert_not_called()


def test_regbase(reg):
    assert RegBase._reg_list == [reg]

def test_regfile():
    rf = Regfile()

    # Test read after initial state
    val1 = rf.read(0)
    val2 = rf.read(29)
    assert val1 == 0
    assert val2 == 0

    # Write some values
    rf.writeRequest(14, 0xdeadbeef)
    assert rf.regs[14] == 0
    rf._tick()
    assert rf.regs[14] == 0xdeadbeef

    rf.writeRequest(2, 0x42)
    assert rf.regs[2] == 0
    rf._tick()
    assert rf.regs[2] == 0x42

    rf._tick()
    assert rf.regs[2] == 0x42
    assert rf.regs[14] == 0xdeadbeef

    # Write to x0
    rf.writeRequest(0, 0xdeadbeef)
    assert rf.regs[0] == 0
    rf._tick()
    assert rf.regs[0] == 0

    # Test invalid index
    # This shouldn't raise an IndexError exception.
    # Check the log for the warning.
    # TODO: we should probably assert the the log message (maybe using caplog?)
    val = rf.read(33)

    # Test reset
    rf._reset()
    assert rf.regs == [0 for _ in range(0,32)]

def test_regChain():
    A = Reg(int)
    B = Reg(int)
    C = Reg(int)
    D = Reg(int)
    A._init(); B._init(); C._init(); D._init()

    B.next.connect(A.cur)
    C.next.connect(B.cur)
    D.next.connect(C.cur)
    RegBase.reset()

    A.next.write(0x42)

    RegBase.tick()
    assert A.cur.read() == 0x42
    assert B.cur.read() == 0
    assert C.cur.read() == 0
    assert D.cur.read() == 0

    A.next.write(0)

    RegBase.tick()
    assert A.cur.read() == 0
    assert B.cur.read() == 0x42
    assert C.cur.read() == 0
    assert D.cur.read() == 0

    RegBase.tick()
    assert A.cur.read() == 0
    assert B.cur.read() == 0
    assert C.cur.read() == 0x42
    assert D.cur.read() == 0

    RegBase.tick()
    assert A.cur.read() == 0
    assert B.cur.read() == 0
    assert C.cur.read() == 0
    assert D.cur.read() == 0x42

def test_next_value_does_not_propagate():
    A = Reg(list)
    A._init()

    foo = [1,2]

    A.next.write(foo)
    RegBase.tick()

    foo[0] = 3
    assert A.cur._val == [1,2]

@pytest.mark.skip()
def test_shiftReg():
    depth = 32
    A = ShiftReg(depth)
    RegBase.reset()

    inputs = [random.randint(0,1)  for _ in range(depth)]

    assert len(A.regs) == depth
    assert A.serOut.read() == 0

    # Fill shift register
    for i in range(depth):
        A.serIn.write(inputs[i])
        RegBase.tick()
        #print("i = {}, regs = {}".format(i, A.regs))

    # Drain shift register
    A.serIn.write(0)
    for i in range(depth):
        #print("i = {}, regs = {}".format(i, A.regs))
        assert A.serOut.read() == inputs[i]
        RegBase.tick()
    
    # Test warning when input wider than 1 bit
    A.serIn.write(4)
    with pytest.warns(UserWarning):
        RegBase.tick()

@pytest.mark.skip()
def test_shiftRegParallel():
    depth = 8
    A = ShiftRegParallel(depth)
    RegBase.reset()

    assert len(A.regs) == depth

    # Test parallel load
    A.parEnable.write(1)
    A.parIn.write(0xAF)
    RegBase.tick()
    assert A.regs == [1,0,1,0,1,1,1,1]

    # Test parallel read
    assert A.parOut.read() == 0xAF

    # Shift some bits
    A.parEnable.write(0)

    A.serIn.write(1)
    RegBase.tick()
    A.serIn.write(1)
    RegBase.tick()
    A.serIn.write(0)
    RegBase.tick()

    # Test parallel read again
    print(A.regs)
    assert A.parOut.read() == 0b01111110

    # Test serial shift out
    A.serIn.write(0)
    for i in range(0, depth):
        #print("i = {}, regs = {}".format(i, A.regs))
        if i == 0:
            assert A.serOut.read() == 0
        elif i == 1:
            assert A.serOut.read() == 1
        elif i == 2:
            assert A.serOut.read() == 1
        elif i == 3:
            assert A.serOut.read() == 1
        elif i == 4:
            assert A.serOut.read() == 1
        elif i == 5:
            assert A.serOut.read() == 1
        elif i == 6:
            assert A.serOut.read() == 1
        elif i == 7:
            assert A.serOut.read() == 0
        
        RegBase.tick()

    # Test parallel load with value wider than depth
    # This should issue a warning.
    A.parEnable.write(1)
    A.parIn.write(0xAEADBEEF)
    with pytest.warns(UserWarning):
        RegBase.tick()

    # Test parallel load with value narrower than depth
    # This should make sure that the length of the list remains the same.
    A.parEnable.write(1)
    A.parIn.write(0x47)
    RegBase.tick()
    assert len(A.regs) == depth

def test_reset():
    reg1 = Reg(int)
    reg2 = Reg(int, 42)
    # reg4 = ShiftReg(8, 1)
    # reg5 = ShiftRegParallel(8, 2)

    RegBase.reset()

    assert reg1.cur.read() == 0
    assert reg2.cur.read() == 42
    # assert reg4.regs == [1  for _ in range(0,8)]
    # assert reg5.regs == [2  for _ in range(0,8)]

def test_sync_reset(reg):

    # No reset -> next val
    reg.next.write(42)
    reg.rst.write(0)
    RegBase.tick()
    assert reg.cur.read() == 42

    # Now assert reset
    reg.rst.write(1)
    RegBase.tick()
    assert reg.cur.read() == 0

    # Throw exception on wrong reset value
    reg.rst.write(44)
    with pytest.raises(Exception, match = "Error: Invalid rst signal!"):
        RegBase.tick()

@pytest.mark.skip()
def test_sync_reset_shiftreg():
    reg1 = ShiftReg(8, 1)
    reg2 = ShiftRegParallel(8, 0)

    # Load some values
    reg1.regs = [1,0,1,0,0,1,0,1]
    reg2.regs = [1,0,1,0,0,1,0,1]

    # No reset
    reg1.rst.write(0)
    reg2.rst.write(0)
    RegBase.tick()
    assert reg1.regs != [1,1,1,1,1,1,1,1]
    assert reg2.regs != [0,0,0,0,0,0,0,0]

    # Reset
    reg1.rst.write(1)
    reg2.rst.write(1)
    RegBase.tick()
    assert reg1.regs == [1  for _ in range(0,8)]
    assert reg2.regs == [0  for _ in range(0,8)]
