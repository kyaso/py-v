import pytest
from test.fixtures import clear_reg_list
from pyv.reg import * 

def test_reg():
    clear_reg_list()

    reg = Reg()
    assert reg.cur.read() == 0

    reg.next.write(0x42)
    assert reg.cur.read() == 0

    reg.prepareNextVal()
    reg.tick()
    assert reg.cur.read() == 0x42

    reg.next.write(0x69)
    assert reg.cur.read() == 0x42

    reg.prepareNextVal()
    reg.tick()
    assert reg.cur.read() == 0x69

def test_regX():
    clear_reg_list()

    reg = RegX('A', 'B')

    reg.next.write('A', 42, 'B', 69)
    assert reg.cur.val['A'].val == 0
    assert reg.cur.val['B'].val == 0
    reg.prepareNextVal()
    reg.tick()
    assert reg.cur.val['A'].val == 42
    assert reg.cur.val['B'].val == 69

    ret = reg.cur.read()
    assert ret['A'] == 42
    assert ret['B'] == 69


def test_regfile():
    clear_reg_list()

    rf = Regfile()

    # Test read after initial state
    val1 = rf.read(0)
    val2 = rf.read(29)
    assert val1 == 0
    assert val2 == 0

    # Write some values
    rf.write(14, 0xdeadbeef)
    assert rf.regs[14] == 0xdeadbeef

    rf.write(2, 0x42)
    assert rf.regs[2] == 0x42

    # Write to x0
    rf.write(0, 0xdeadbeef)
    assert rf.regs[0] == 0

def test_regChain():
    clear_reg_list()

    A = Reg()
    B = Reg()
    C = Reg()
    D = Reg()

    B.next.connect(A.cur)
    C.next.connect(B.cur)
    D.next.connect(C.cur)

    A.next.write(0x42)

    RegBase.updateRegs()
    assert A.cur.read() == 0x42
    assert B.cur.read() == 0
    assert C.cur.read() == 0
    assert D.cur.read() == 0

    A.next.write(0)

    RegBase.updateRegs()
    assert A.cur.read() == 0
    assert B.cur.read() == 0x42
    assert C.cur.read() == 0
    assert D.cur.read() == 0

    RegBase.updateRegs()
    assert A.cur.read() == 0
    assert B.cur.read() == 0
    assert C.cur.read() == 0x42
    assert D.cur.read() == 0

    RegBase.updateRegs()
    assert A.cur.read() == 0
    assert B.cur.read() == 0
    assert C.cur.read() == 0
    assert D.cur.read() == 0x42

def test_regChainX():
    clear_reg_list()

    A = RegX('A', 'B')
    B = RegX('A', 'B')
    C = RegX('A', 'B')
    D = RegX('A', 'B')

    B.next.connect(A.cur)
    C.next.connect(B.cur)
    D.next.connect(C.cur)

    A.next.write('A',45,'B',78)

    RegBase.updateRegs()
    assert A.cur.read() == {'A':45, 'B':78}
    assert B.cur.read() == {'A':0, 'B':0}
    assert C.cur.read() == {'A':0, 'B':0}
    assert D.cur.read() == {'A':0, 'B':0}

    A.next.write('A',0,'B',0)

    RegBase.updateRegs()
    assert A.cur.read() == {'A':0, 'B':0}
    assert B.cur.read() == {'A':45, 'B':78}
    assert C.cur.read() == {'A':0, 'B':0}
    assert D.cur.read() == {'A':0, 'B':0}

    RegBase.updateRegs()
    assert A.cur.read() == {'A':0, 'B':0}
    assert B.cur.read() == {'A':0, 'B':0}
    assert C.cur.read() == {'A':45, 'B':78}
    assert D.cur.read() == {'A':0, 'B':0}

    RegBase.updateRegs()
    assert A.cur.read() == {'A':0, 'B':0}
    assert B.cur.read() == {'A':0, 'B':0}
    assert C.cur.read() == {'A':0, 'B':0}
    assert D.cur.read() == {'A':45, 'B':78}

def test_shiftReg():
    clear_reg_list()

    depth = 32
    A = ShiftReg(depth)

    assert len(A.regs) == depth
    assert A.serOut.read() == 0

    # Fill shift register
    for i in range(0, depth):
        A.serIn.write(i+1)
        RegBase.updateRegs()
        #print("i = {}, regs = {}".format(i, A.regs))

    # Drain shift register
    A.serIn.write(0)
    for i in range(0, depth):
        #print("i = {}, regs = {}".format(i, A.regs))
        assert A.serOut.read() == i+1
        RegBase.updateRegs()

def test_shiftRegParallel():
    clear_reg_list()

    depth = 8
    A = ShiftRegParallel(depth)

    assert len(A.regs) == depth

    # Test parallel load
    A.parEnable.write(1)
    A.parIn.write(0xAF)
    RegBase.updateRegs()
    assert A.regs == [1,0,1,0,1,1,1,1]

    # Test parallel read
    assert A.parOut.read() == 0xAF

    # Shift some bits
    A.parEnable.write(0)

    A.serIn.write(1)
    RegBase.updateRegs()
    A.serIn.write(1)
    RegBase.updateRegs()
    A.serIn.write(0)
    RegBase.updateRegs()

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
        
        RegBase.updateRegs()

    # Test parallel load with value wider than depth
    # This should throw an exception.
    A.parEnable.write(1)
    A.parIn.write(0xAEADBEEF)
    with pytest.raises(Exception):
        RegBase.updateRegs()

    # Test parallel load with value narrower than depth
    # This should make sure that the length of the list remains the same.
