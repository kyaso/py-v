from unittest.mock import MagicMock
import pytest
from pyv.reg import Reg, Regfile
from pyv.clocked import RegList


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
    assert reg._reset_val == 42


def test_sensitive_methods():
    def foo():
        pass

    regA = Reg(int)
    regA._init()
    assert regA.cur._process_method_handler._process_methods == []

    regB = Reg(int, sensitive_methods=[foo])
    assert regB.cur._process_method_handler._process_methods == [foo]


def test_reg(reg):
    RegList.reset()
    assert reg.cur.read() == 0

    reg.next.write(0x42)
    assert reg.cur.read() == 0

    RegList.prepare_next_val()
    RegList.tick()
    assert reg.cur.read() == 0x42

    reg.next.write(0x69)
    assert reg.cur.read() == 0x42

    RegList.prepare_next_val()
    RegList.tick()
    assert reg.cur.read() == 0x69


def test_reg_tick(reg):
    reg.next.write(42)
    RegList.prepare_next_val()
    RegList.tick()
    assert reg._do_tick == True
    assert reg.cur._val == 42

    # Tick again, but as port value is unchanged, register should skip _tick
    reg.cur.write = MagicMock()
    RegList.prepare_next_val()
    RegList.tick()
    assert reg._do_tick == False
    reg.cur.write.assert_not_called()


def test_RegList(reg):
    assert RegList._reg_list == [reg]


def test_regfile():
    rf = Regfile()

    # Test read after initial state
    for r in range(0, 32):
        assert rf.read(r) == 0

    # Write some values
    rf.write_request(14, 0xdeadbeef)
    assert rf.regs[14] == 0
    rf._tick()
    assert rf.regs[14] == 0xdeadbeef

    rf.write_request(2, 0x42)
    assert rf.regs[2] == 0
    rf._tick()
    assert rf.regs[2] == 0x42

    rf._tick()
    assert rf.regs[2] == 0x42
    assert rf.regs[14] == 0xdeadbeef

    # Write to x0
    rf.write_request(0, 0xdeadbeef)
    assert rf.regs[0] == 0
    rf._tick()
    assert rf.regs[0] == 0

    # Test invalid index
    # This shouldn't raise an IndexError exception.
    # Check the log for the warning.
    # TODO: we should probably assert the the log message (maybe using caplog?)
    _ = rf.read(33)

    # Test reset
    rf._reset()
    assert rf.regs == [0 for _ in range(0, 32)]


def test_reg_chain():
    A = Reg(int)
    B = Reg(int)
    C = Reg(int)
    D = Reg(int)
    A._init(); B._init(); C._init(); D._init()

    B.next.connect(A.cur)
    C.next.connect(B.cur)
    D.next.connect(C.cur)
    RegList.reset()

    A.next.write(0x42)

    RegList.prepare_next_val()
    RegList.tick()
    assert A.cur.read() == 0x42
    assert B.cur.read() == 0
    assert C.cur.read() == 0
    assert D.cur.read() == 0

    A.next.write(0)

    RegList.prepare_next_val()
    RegList.tick()
    assert A.cur.read() == 0
    assert B.cur.read() == 0x42
    assert C.cur.read() == 0
    assert D.cur.read() == 0

    RegList.prepare_next_val()
    RegList.tick()
    assert A.cur.read() == 0
    assert B.cur.read() == 0
    assert C.cur.read() == 0x42
    assert D.cur.read() == 0

    RegList.prepare_next_val()
    RegList.tick()
    assert A.cur.read() == 0
    assert B.cur.read() == 0
    assert C.cur.read() == 0
    assert D.cur.read() == 0x42


def test_next_value_does_not_propagate():
    A = Reg(list)
    A._init()

    foo = [1, 2]

    A.next.write(foo)
    RegList.prepare_next_val()
    RegList.tick()

    foo[0] = 3
    assert A.cur._val == [1, 2]


def test_reset():
    reg1 = Reg(int)
    reg2 = Reg(int, 42)

    RegList.reset()

    assert reg1.cur.read() == 0
    assert reg2.cur.read() == 42


def test_sync_reset(reg):

    # No reset -> next val
    reg.next.write(42)
    reg.rst.write(0)
    RegList.prepare_next_val()
    RegList.tick()
    assert reg.cur.read() == 42

    # Now assert reset
    reg.rst.write(1)
    RegList.prepare_next_val()
    RegList.tick()
    assert reg.cur.read() == 0

    # Throw exception on wrong reset value
    reg.rst.write(44)
    with pytest.raises(Exception, match="Error: Invalid rst signal!"):
        RegList.prepare_next_val()
        RegList.tick()
