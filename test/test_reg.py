import pytest
from pyv.reg import * 

def test_reg():
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