import pytest
import random
from pyv.reg import * 
from pyv.clocked import RegBase

def test_reg():
    RegBase.clear()

    reg = Reg()
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

def test_regbase():
    class myReg(RegBase):
        pass

    reg = myReg(0)
    with pytest.raises(NotImplementedError):
        reg._prepareNextVal()
    
    with pytest.raises(NotImplementedError):
        reg._tick()

def test_regX():
    RegBase.clear()

    reg = RegX('A', 'B')
    RegBase.reset()

    reg.next.write('A', 42, 'B', 69)
    assert reg.cur._val['A']._val == 0
    assert reg.cur._val['B']._val == 0
    RegBase.tick()
    assert reg.cur._val['A']._val == 42
    assert reg.cur._val['B']._val == 69

    ret = reg.cur.read()
    assert ret['A'] == 42
    assert ret['B'] == 69


def test_regfile():
    RegBase.clear()

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

    # Test reset
    rf._reset()
    assert rf.regs == [0 for _ in range(0,32)]

def test_regChain():
    RegBase.clear()

    A = Reg()
    B = Reg()
    C = Reg()
    D = Reg()

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

def test_regChainX():
    RegBase.clear()

    A = RegX('A', 'B')
    B = RegX('A', 'B')
    C = RegX('A', 'B')
    D = RegX('A', 'B')

    B.next.connect(A.cur)
    C.next.connect(B.cur)
    D.next.connect(C.cur)
    RegBase.reset()

    A.next.write('A',45,'B',78)

    RegBase.tick()
    assert A.cur.read() == {'A':45, 'B':78}
    assert B.cur.read() == {'A':0, 'B':0}
    assert C.cur.read() == {'A':0, 'B':0}
    assert D.cur.read() == {'A':0, 'B':0}

    A.next.write('A',0,'B',0)

    RegBase.tick()
    assert A.cur.read() == {'A':0, 'B':0}
    assert B.cur.read() == {'A':45, 'B':78}
    assert C.cur.read() == {'A':0, 'B':0}
    assert D.cur.read() == {'A':0, 'B':0}

    RegBase.tick()
    assert A.cur.read() == {'A':0, 'B':0}
    assert B.cur.read() == {'A':0, 'B':0}
    assert C.cur.read() == {'A':45, 'B':78}
    assert D.cur.read() == {'A':0, 'B':0}

    RegBase.tick()
    assert A.cur.read() == {'A':0, 'B':0}
    assert B.cur.read() == {'A':0, 'B':0}
    assert C.cur.read() == {'A':0, 'B':0}
    assert D.cur.read() == {'A':45, 'B':78}

def test_shiftReg():
    RegBase.clear()

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

def test_shiftRegParallel():
    RegBase.clear()

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
    reg1 = Reg()
    reg2 = Reg(42)
    reg3 = RegX('foo', 'bar')
    reg4 = ShiftReg(8, 1)
    reg5 = ShiftRegParallel(8, 2)

    RegBase.reset()

    assert reg1.cur.read() == 0
    assert reg2.cur.read() == 42
    assert reg3.cur.read() == {'foo': 0, 'bar': 0}
    assert reg4.regs == [1  for _ in range(0,8)]
    assert reg5.regs == [2  for _ in range(0,8)]
