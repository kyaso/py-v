import pytest
from core import Core

@pytest.fixture
def coreFx():
    core = Core()
    return core

def test_sanity():
    assert True

# ---------------------------------------
# Integer Computational Instructions
# ---------------------------------------

def test_ADD(coreFx):
    res = coreFx.i_ADD(0x00000000, 0x00000000)
    assert res == 0x00000000

    res = coreFx.i_ADD(0x00000001, 0x00000001)
    assert res == 0x00000002

    res = coreFx.i_ADD(0x00000003, 0x00000007)
    assert res == 0x0000000a

    res = coreFx.i_ADD(0x00000000, 0xfffff800)
    assert res == 0xfffff800

    res = coreFx.i_ADD(0x80000000, 0x000007ff)
    assert res == 0x800007ff

def test_SUB(coreFx):
    res = coreFx.i_SUB(0x00000000, 0x00000000)
    assert res == 0x00000000

    res = coreFx.i_SUB(0x00000001, 0x00000001)
    assert res == 0x00000000

    res = coreFx.i_SUB(0x00000003, 0x00000007)
    assert res == 0xfffffffc

    res = coreFx.i_SUB(0x00000000, 0xffff8000)
    assert res == 0x00008000

    res = coreFx.i_SUB(0x00000000, 0x00007fff)
    assert res == 0xffff8001

    res = coreFx.i_SUB(0x7fffffff, 0xffff8000)
    assert res == 0x80007fff


def test_SLT(coreFx):
    res = coreFx.i_SLT(0x00000000, 0x00000000)
    assert res == 0

    res = coreFx.i_SLT(0x00000001, 0x00000001)
    assert res == 0

    res = coreFx.i_SLT(0x00000003, 0x00000007)
    assert res == 1

    res = coreFx.i_SLT(0x80000000, 0x00000000)
    assert res == 1

    res = coreFx.i_SLT(0x7fffffff, 0xfffff800)
    assert res == 0

    res = coreFx.i_SLT(0x80000000, 0xfffff800)
    assert res == 0

def test_SLTU(coreFx):
    res = coreFx.i_SLTU(0x00000000, 0x00000000)
    assert res == 0

    res = coreFx.i_SLTU(0x00000001, 0x00000001)
    assert res == 0

    res = coreFx.i_SLTU(0x00000003, 0x00000007)
    assert res == 1

    res = coreFx.i_SLTU(0x00000007, 0x00000003)
    assert res == 0

    res = coreFx.i_SLTU(0x00000000, 0xfffff800)
    assert res == 1

    res = coreFx.i_SLTU(0x80000000, 0xfffff800)
    assert res == 1

def test_AND(coreFx):
    res = coreFx.i_AND(0xff00ff00, 0xffffff0f)
    assert res == 0xff00ff00

    res = coreFx.i_AND(0x00ff00ff, 0x0000070f)
    assert res == 0x0000000f

def test_OR(coreFx):
    res = coreFx.i_OR(0xff00ff00, 0xffffff0f)
    assert res == 0xffffff0f

    res = coreFx.i_OR(0x00ff00ff, 0x0000070f)
    assert res == 0x00ff07ff

def test_XOR(coreFx):
    res = coreFx.i_XOR(0x00ff0f00, 0xffffff0f)
    assert res == 0xff00f00f

    res = coreFx.i_XOR(0x00ff08ff, 0x0000070f)
    assert res == 0x00ff0ff0

def test_SLL(coreFx):
    res = coreFx.i_SLL(0x00000001, 0)
    assert res == 0x00000001

    res = coreFx.i_SLL(0x00000001, 1)
    assert res == 0x00000002

    res = coreFx.i_SLL(0x00000001, 7)
    assert res == 0x00000080

    res = coreFx.i_SLL(0x00000001, 31)
    assert res == 0x80000000
    
    res = coreFx.i_SLL(0xffffffff, 7)
    assert res == 0xffffff80

    res = coreFx.i_SLL(0x21212121, 14)
    assert res == 0x48484000

def test_SRL(coreFx):
    res = coreFx.i_SRL(0x00000001, 0)
    assert res == 0x00000001

    res = coreFx.i_SRL(0x00000001, 1)
    assert res == 0x00000000

    res = coreFx.i_SRL(0x00000001, 7)
    assert res == 0x00000000

    res = coreFx.i_SRL(0x00000001, 31)
    assert res == 0x00000000
    
    res = coreFx.i_SRL(0xffffffff, 7)
    assert res == 0x01ffffff

    res = coreFx.i_SRL(0x21212121, 14)
    assert res == 0x00008484

def test_SRA(coreFx):
    res = coreFx.i_SRA(0x7fffffff, 0)
    assert res == 0x7fffffff

    res = coreFx.i_SRA(0x7fffffff, 1)
    assert res == 0x3fffffff

    res = coreFx.i_SRA(0x81818181, 1)
    assert res == 0xc0c0c0c0

    res = coreFx.i_SRA(0x81818181, 7)
    assert res == 0xff030303

    res = coreFx.i_SRA(0x81818181, 31)
    assert res == 0xffffffff

def test_LUI(coreFx):
    res = coreFx.i_LUI(0x00000000) # imm (sign-extended)
    assert res == 0x00000000

    res = coreFx.i_LUI(0xffffffff) # imm (sign-extended)
    assert res == 0xfffff000

    res = coreFx.i_LUI(0x0007ffff) # imm (sign-extended)
    assert res == 0x7ffff000

def test_AUIPC(coreFx):
    res = coreFx.i_AUIPC(0x00001000, 0) # PC, imm (sign-ext)
    assert res == 0x00001000

    res = coreFx.i_AUIPC(0x00001000, 0x0007ffff) # PC, imm (sign-ext)
    assert res == 0x00080FFF




# ---------------------------------------
# Control Transfer Instructions
# ---------------------------------------

# Unconditional Jumps

def test_JAL(coreFx):
    res = coreFx.i_JAL(0x80000000, ) # IN: PC, imm (20bit, sign-ext); OUT: link reg (pc+4, rd)

# Conditional Branches

# ---------------------------------------
# Load and Store Instructions
# ---------------------------------------