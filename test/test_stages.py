import pytest
from stages import *
from reg import *

def test_sanity():
    assert True

# ---------------------------------------
# Test FETCH
# ---------------------------------------
def test_IFStage():
    fetch = IFStage()

    # SW a0,-20(s0) = SW, x10, -20(x8)
    fetch.inst_i.write(0xfea42623)
    fetch.npc_i.write(0x80000004)

    RegBase.updateRegs()
    fetch.process()

    out = fetch.IFID_o.read()
    assert out['inst'] == 0xfea42623
    assert out['pc'] == 0x80000004

# ---------------------------------------
# Test DECODE
# ---------------------------------------
class TestIDStage:
    def test_decImm(self):
        dec = IDStage(None)
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
    
    # TODO
    def test_check_exception(self):
        pass

    def test_IDStage(self):
        regf = Regfile()
        decode = IDStage(regf)

        # SW a0,-20(s0) = SW, x10, -20(x8) (x8=rs1, x10=rs2)
        # Write some values into the relevant registers
        regf.write(8, 0x80000000)
        regf.write(10, 42)

        # Set inputs
        decode.IFID_i.write('inst', 0xfea42623, 'pc', 0x80000004)
        decode.process()

        # Validate outputs
        out = decode.IDEX_o.read()
        assert out['rs1'] == 0x80000000
        assert out['rs2'] == 42
        assert out['imm'] == 0xffffffec
        assert out['pc'] == 0x80000004
        assert out['rd'] == 0x0C
        assert out['we'] == False
        assert out['opcode'] == 0b01000
        assert out['funct3'] == 2

        # Test instruction with register write
        # ADDI x0, x0, 0
        decode.IFID_i.write('inst', 0x00000013)
        decode.process()
        out = decode.IDEX_o.read()
        assert out['rs1'] == 0
        assert out['rs2'] == 0
        assert out['imm'] == 0
        assert out['pc'] == 0x80000004
        assert out['rd'] == 0
        assert out['we'] == True
        assert out['wb_sel'] == 0
        assert out['opcode'] == 0b00100
        assert out['funct3'] == 0

        # Test instruction with funct7 output
        # SUB x14, x7, x5
        regf.write(7, 43)
        regf.write(5, 12)
        decode.IFID_i.write('inst', 0x40538733)
        decode.process()
        out = decode.IDEX_o.read()
        assert out['rs1'] == 43
        assert out['rs2'] == 12
        assert out['pc'] == 0x80000004
        assert out['rd'] == 14
        assert out['we'] == True
        assert out['wb_sel'] == 0
        assert out['opcode'] == 0b01100
        assert out['funct3'] == 0
        assert out['funct7'] == 0b0100000

        # Test wb_sel
        res = decode.wb_sel(0b11011)
        assert res == 1
        res = decode.wb_sel(0)
        assert res == 2
        res = decode.wb_sel(0b01100)
        assert res == 0

# ---------------------------------------
# Test EXECUTE
# ---------------------------------------

# ---------------------------------------
# Test MEMORY
# ---------------------------------------

# ---------------------------------------
# Test WRITE-BACK
# ---------------------------------------