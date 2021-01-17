import pytest
from reg import *

def test_reg():
    reg = Reg()
    assert reg.cur.val == 0

    reg.next.val = 0x42
    assert reg.cur.val == 0

    reg.prepareNextVal()
    reg.tick()
    assert reg.cur.val == 0x42

    reg.next.val = 0x69
    assert reg.cur.val == 0x42

    reg.prepareNextVal()
    reg.tick()
    assert reg.cur.val == 0x69

def test_regfile():
    rf = Regfile()

    # Test read after initial state
    val1 = rf.read(0)
    val2 = rf.read(29)
    assert val1 == 0
    assert val2 == 0

    # Write some values
    rf.rd_idx_i.val = 14
    rf.rd_val_i.val = 0xdeadbeef
    rf.we.val = True
    rval = rf.read(14)
    assert rval == 0
    rf.prepareNextVal()
    rf.tick()
    rval = rf.read(14)
    assert rval == 0xdeadbeef

    rf.rd_idx_i.val = 2
    rf.rd_val_i.val = 0x42
    rf.we.val = True
    rval = rf.read(2)
    assert rval == 0
    rf.prepareNextVal()
    rf.tick()
    rval = rf.read(2)
    assert rval == 0x42

    # Write to x0
    rf.rd_idx_i.val = 0
    rf.rd_val_i.val = 0xdeadbeef
    rf.prepareNextVal()
    rf.tick()
    rval = rf.read(0)
    assert rval == 0

    # Test with WE=0
    rf.rd_idx_i.val = 14
    rf.rd_val_i.val = 0xaffeaffe
    rf.we.val = False
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

    A.next.val = 0x42

    RegBase.updateRegs()
    assert A.cur.val == 0x42
    assert B.cur.val == 0
    assert C.cur.val == 0
    assert D.cur.val == 0