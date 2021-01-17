import pytest
from stages import *
from reg import *

def test_sanity():
    assert True

# ---------------------------------------
# Test FETCH
# ---------------------------------------
def test_FETCH():
    fetch = FetchStage()

    # SW a0,-20(s0) = SW, x10, -20(x8)
    fetch.inst_i.val = 0xfea42623
    fetch.npc_i.val = 0x80000004
    fetch.process()

    assert fetch.inst_o.val == 0xfea42623
    assert fetch.pc_o.val == 0x80000004

# ---------------------------------------
# Test DECODE
# ---------------------------------------
def test_DECODE():
    regf = Regfile()
    decode = DecodeStage(regf)

    # SW a0,-20(s0) = SW, x10, -20(x8) (x8=rs1, x10=rs2)
    # Write some values into the relevant registers
    regf.we.val = True
    # regf.write(True, 8, 0x80000000)
    regf.rd_idx_i.val = 8
    regf.rd_val_i.val = 0x80000000
    regf.prepareNextVal()
    regf.tick()

    # regf.write(True, 10, 42)
    regf.rd_idx_i.val = 10
    regf.rd_val_i.val = 42
    regf.prepareNextVal()
    regf.tick()

    # Set inputs
    decode.inst_i.val = 0xfea42623
    decode.pc_i.val = 0x80000004
    decode.process()

    # Validate outputs
    return # TODO: For now
    assert decode.rs1_o.val == 0x80000000
    assert decode.rs2_o.val == 42
    assert decode.imm_o.val == 0xffffffec # -20, 32-bit sign-extended
    assert decode.pc_o.val == 0x80000004
    assert decode.rd_o.val == 0x0C # rd is bits [11:7] of instruction
    assert decode.we_o.val == False

    # TODO: Test instruction with register write

# ---------------------------------------
# Test EXECUTE
# ---------------------------------------

# ---------------------------------------
# Test MEMORY
# ---------------------------------------

# ---------------------------------------
# Test WRITE-BACK
# ---------------------------------------