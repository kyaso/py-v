import pytest
from reg import *

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
    assert reg.cur.val == {'A':0, 'B':0}
    reg.prepareNextVal()
    reg.tick()
    assert reg.cur.val == {'A':42, 'B':69}

    assert reg.cur.read() == {'A':42, 'B':69}


def test_regfile():
    rf = Regfile()

    # Test read after initial state
    val1 = rf.read(0)
    val2 = rf.read(29)
    assert val1 == 0
    assert val2 == 0

    # Write some values
    rf.rd_idx_i.write(14)
    rf.rd_val_i.write(0xdeadbeef)
    rf.we.write(True)
    rval = rf.read(14)
    assert rval == 0
    rf.prepareNextVal()
    rf.tick()
    rval = rf.read(14)
    assert rval == 0xdeadbeef

    rf.rd_idx_i.write(2)
    rf.rd_val_i.write(0x42)
    rf.we.write(True)
    rval = rf.read(2)
    assert rval == 0
    rf.prepareNextVal()
    rf.tick()
    rval = rf.read(2)
    assert rval == 0x42

    # Write to x0
    rf.rd_idx_i.write(0)
    rf.rd_val_i.write(0xdeadbeef)
    rf.prepareNextVal()
    rf.tick()
    rval = rf.read(0)
    assert rval == 0

    # Test with WE=0
    rf.rd_idx_i.write(14)
    rf.rd_val_i.write(0xaffeaffe)
    rf.we.write(False)
    rval = rf.read(14)
    assert rval == 0xdeadbeef
    rf.prepareNextVal()
    rf.tick()
    rval = rf.read(14)
    assert rval == 0xdeadbeef

def test_regChain():
    A = Reg()
    B = Reg()
    C = Reg()
    D = Reg()

    B.next = A.cur
    C.next = B.cur
    D.next = C.cur

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

    B.next = A.cur
    C.next = B.cur
    D.next = C.cur

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