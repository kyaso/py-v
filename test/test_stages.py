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
def test_decImm():
    dec = DecodeStage(None)
    # --- Test I-type -------------------------
    # 001100110000 10000 000 00001 0010011
    inst = 0b00110011000010000000000010010011
    imm = dec.decImm(0b00100, inst)
    assert imm == 0b001100110000

    # Test sign-ext
    # 101100110000 10000 000 00001 0010011
    inst = 0b10110011000010000000000010010011
    imm = dec.decImm(0b00100, inst)
    assert imm == 0xFFFFFB30

    # --- Test S-type -------------------------
    # 0111010 00000 00000 010 11100 0100011
    inst = 0b01110100000000000010111000100011
    imm = dec.decImm(0b01000, inst)
    assert imm == 0b011101011100

    # Test sign-ext
    # 1111010 00000 00000 010 11100 0100011
    inst = 0b11110100000000000010111000100011
    imm = dec.decImm(0b01000, inst)
    assert imm == 0xFFFFFF5C

    # --- Test B-type -------------------------
    # 0 100110 00000 00000 000 0110 1 1100011
    inst = 0b01001100000000000000011011100011
    imm = dec.decImm(0b11000, inst)
    assert imm == 0b0110011001100

    # Test sign-ext
    # 1 100110 00000 00000 000 0110 1 1100011
    inst = 0b11001100000000000000011011100011
    imm = dec.decImm(0b11000, inst)
    assert imm == 0xFFFFFCCC

    # --- Test U-type -------------------------
    # 00001011001111000101 00000 0110111
    inst = 0b00001011001111000101000000110111
    imm = dec.decImm(0b01101, inst)
    assert imm == 0x0B3C5000

    # Test sign-ext
    # 10001011001111000101 00000 0110111
    inst = 0b10001011001111000101000000110111
    imm = dec.decImm(0b01101, inst)
    assert imm == 0x8B3C5000

    # --- Test J-type -------------------------
    # 0 1111010110 0 00011010 00000 1101111
    inst = 0b01111010110000011010000001101111
    imm = dec.decImm(0b11011, inst)
    assert imm == 0x1A7AC

    # Test sign-ext
    # 1 1111010110 0 00011010 00000 1101111
    inst = 0b11111010110000011010000001101111
    imm = dec.decImm(0b11011, inst)
    assert imm == 0xFFF1A7AC

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
    #return # TODO: For now
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