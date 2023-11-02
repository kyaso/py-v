import pytest
from pyv.stages import *
from pyv.reg import *
from pyv.util import MASK_32
from pyv.mem import Memory
from pyv.simulator import Simulator
from .fixtures import sim


def test_sanity():
    assert True

# ---------------------------------------
# Test data types
# ---------------------------------------
def test_data_types():
    def check_attrs(type_obj, attr_list):
        for attr in attr_list:
            assert hasattr(type_obj, attr)

    foo = IFID_t()
    attr_list = ['inst', 'pc']
    check_attrs(foo, attr_list)

    foo = IDEX_t()
    attr_list = ['rs1', 'rs2', 'imm', 'pc', 'rd', 'we', 'wb_sel', 'opcode', 'funct3', 'funct7', 'mem']
    check_attrs(foo, attr_list)

    foo = EXMEM_t()
    attr_list = ['rd', 'we', 'wb_sel', 'take_branch', 'alu_res', 'pc4', 'rs2', 'mem', 'funct3']
    check_attrs(foo, attr_list)

    foo = MEMWB_t()
    attr_list = ['rd', 'we', 'alu_res', 'pc4', 'mem_rdata', 'wb_sel']
    check_attrs(foo, attr_list)

# ---------------------------------------
# Test FETCH
# ---------------------------------------
def test_IFStage(sim):
    RegBase.clear()

    fetch = IFStage(Memory(1024))

    # SW a0,-20(s0) = SW, x10, -20(x8)
    fetch.imem.writeRequest(0, 0xfea42623, 4)
    fetch.imem._tick()
    fetch.npc_i.write(0x00000000)

    sim.process_queue()
    RegBase.tick()
    sim.process_queue()

    out = fetch.IFID_o.read()
    assert out.inst == 0xfea42623
    assert out.pc == 0x00000000

# ---------------------------------------
# Test DECODE
# ---------------------------------------
class TestIDStage:
    def test_constructor(self):
        regf = Regfile()
        dec = IDStage(regf)

        assert regf == dec.regfile
        assert dec.IFID_i._type == IFID_t
        assert dec.IDEX_o._type == IDEX_t

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

    def test_exception(self, caplog, sim):
        dec = IDStage(Regfile())

        # --- Illegal Instruction -----------------
        pc = 0

        # No exception for valid instruction
        inst = 0x23 # store
        dec.IFID_i.write(IFID_t(inst, pc))
        sim.process_queue()

        ## Inst[1:0] != 2'b11
        inst = 0x10
        pc += 1
        dec.IFID_i.write(IFID_t(inst, pc))
        with pytest.raises(Exception, match = f"IDStage: Illegal instruction @ PC = 0x{pc:08X} detected."):
            sim.process_queue()

        ## Unsupported RV32base Opcodes
        inst = 0x1F # opcode = 0011111
        pc += 1
        dec.IFID_i.write(IFID_t(inst, pc))
        with pytest.raises(Exception, match = f"IDStage: Illegal instruction @ PC = 0x{pc:08X}: unknown opcode"):
            sim.process_queue()

        inst = 0x73 # opcode = 1110011
        pc += 1
        dec.IFID_i.write(IFID_t(inst, pc))
        with pytest.raises(Exception, match = f"IDStage: Illegal instruction @ PC = 0x{pc:08X}: unknown opcode"):
            sim.process_queue()

        ## Illegal combinations of funct3, funct7

        # ADDI - SRAI -> opcode = 0010011
        # If funct3 == 1 => funct7 == 0
        inst = 0x02001013 # funct7 = 1
        pc += 1
        dec.IFID_i.write(IFID_t(inst, pc))
        with pytest.raises(Exception, match = f"IDStage: Illegal instruction @ PC = 0x{pc:08X} detected."):
            sim.process_queue()
        # If funct3 == 5 => funct7 == {0, 0100000}
        inst = 0xc0005013 # funct7 = 1100000
        pc += 1
        dec.IFID_i.write(IFID_t(inst, pc))
        with pytest.raises(Exception, match = f"IDStage: Illegal instruction @ PC = 0x{pc:08X} detected."):
            sim.process_queue()

        # ADD - AND -> opcode = 0110011
        # If funct7 != {0, 0100000} -> illegal
        inst = 0x80000033 # funct7 = 1000000
        pc += 1
        dec.IFID_i.write(IFID_t(inst, pc))
        with pytest.raises(Exception, match = f"IDStage: Illegal instruction @ PC = 0x{pc:08X} detected."):
            sim.process_queue()
        # If funct7 == 0100000 => funct3 == {0, 5}
        inst = 0x40002033 # funct3 = 2
        pc += 1
        dec.IFID_i.write(IFID_t(inst, pc))
        with pytest.raises(Exception, match = f"IDStage: Illegal instruction @ PC = 0x{pc:08X} detected."):
            sim.process_queue()

        # JALR -> opcode = 1100111 => funct3 == 0
        inst = 0x00005067 # funct3 = 5
        pc += 1
        dec.IFID_i.write(IFID_t(inst, pc))
        with pytest.raises(Exception, match = f"IDStage: Illegal instruction @ PC = 0x{pc:08X} detected."):
            sim.process_queue()

        # BEQ - BGEU -> opcode = 1100011 => funct3 = {0,1,4,5,6,7}
        funct3 = [2,3]
        for f3 in funct3:
            pc += 1
            inst = 0x63 | (f3 << 12)
            dec.IFID_i.write(IFID_t(inst, pc))
            with pytest.raises(Exception, match = f"IDStage: Illegal instruction @ PC = 0x{pc:08X} detected."):
                sim.process_queue()

        # LB - LHU -> opcode = 0000011 => funct3 = {0,1,2,4,5}
        funct3 = [3,6,7]
        for f3 in funct3:
            pc += 1
            inst = 0x3 | (f3 << 12)
            dec.IFID_i.write(IFID_t(inst, pc))
            with pytest.raises(Exception, match = f"IDStage: Illegal instruction @ PC = 0x{pc:08X} detected."):
                sim.process_queue()

        # SB, SH, SW -> opcode = 0100011 => funct3 = {0,1,2}
        funct3 = [3,4,5,6,7]
        for f3 in funct3:
            pc += 1
            inst = 0x23 | (f3 << 12)
            dec.IFID_i.write(IFID_t(inst, pc))
            with pytest.raises(Exception, match = f"IDStage: Illegal instruction @ PC = 0x{pc:08X} detected."):
                sim.process_queue()

    def test_IDStage(self, sim):
        regf = Regfile()
        decode = IDStage(regf)

        # SW a0,-20(s0) = SW, x10, -20(x8) (x8=rs1, x10=rs2)
        # Write some values into the relevant registers
        regf.writeRequest(8, 0x80000000)
        regf._tick()
        regf.writeRequest(10, 42)
        regf._tick()

        # Set inputs
        decode.IFID_i.write(IFID_t(0xfea42623, 0x80000004))
        sim.process_queue()

        # Validate outputs
        out = decode.IDEX_o.read()
        assert out.rs1 == 0x80000000
        assert out.rs2 == 42
        assert out.imm == 0xffffffec
        assert out.pc == 0x80000004
        assert out.rd == 0x0C
        assert out.we == False
        assert out.opcode == 0b01000
        assert out.funct3 == 2
        assert out.mem == 2

        # Test instruction with register write
        # ADDI x0, x0, 0
        decode.IFID_i.write(IFID_t(0x00000013, 0x80000004))
        sim.process_queue()
        out = decode.IDEX_o.read()
        assert out.rs1 == 0
        assert out.rs2 == 0
        assert out.imm == 0
        assert out.pc == 0x80000004
        assert out.rd == 0
        assert out.we == True
        assert out.wb_sel == 0
        assert out.opcode == 0b00100
        assert out.funct3 == 0
        assert out.mem == 0

        # Test instruction with funct7 output
        # SUB x14, x7, x5
        regf.writeRequest(7, 43)
        regf._tick()
        regf.writeRequest(5, 12)
        regf._tick()

        decode.IFID_i.write(IFID_t(0x40538733, 0x80000004))
        sim.process_queue()
        out = decode.IDEX_o.read()
        assert out.rs1 == 43
        assert out.rs2 == 12
        assert out.pc == 0x80000004
        assert out.rd == 14
        assert out.we == True
        assert out.wb_sel == 0
        assert out.opcode == 0b01100
        assert out.funct3 == 0
        assert out.funct7 == 0b0100000
        assert out.mem == 0

        # Test wb_sel
        res = decode.wb_sel(0b11011)
        assert res == 1
        res = decode.wb_sel(0)
        assert res == 2
        res = decode.wb_sel(0b01100)
        assert res == 0

        # Test LOAD
        # LW x15, x8, 0x456
        regf.writeRequest(8, 0x40000000)
        regf._tick()
        decode.IFID_i.write(IFID_t(0x45642783, 0x80000004))
        sim.process_queue()
        out = decode.IDEX_o.read()
        assert out.rs1 == 0x40000000
        assert out.imm == 0x456
        assert out.pc == 0x80000004
        assert out.rd == 15
        assert out.we == True
        assert out.wb_sel == 2
        assert out.opcode == 0b00000
        assert out.funct3 == 0b010
        assert out.mem == 1

# ---------------------------------------
# Test EXECUTE
# ---------------------------------------
class TestEXStage:
    def test_constructor(self):
        ex = EXStage()

        assert ex.IDEX_i._type == IDEX_t
        assert ex.EXMEM_o._type == EXMEM_t

    def test_passThrough(self, sim):
        ex = EXStage()

        ex.IDEX_i.write(IDEX_t(rd=1, we=1, wb_sel=2, rs2=23, mem=1, funct3=5))

        sim.process_queue()

        out = ex.EXMEM_o.read()
        assert out.rd == 1
        assert out.we == 1
        assert out.wb_sel == 2
        assert out.rs2 == 23
        assert out.mem == 1
        assert out.funct3 == 5

    def test_alu(self):
        ex = EXStage()

        # LUI
        res = ex.alu(0b01101, 0, 0, 0x41AF3000, 0, 0, 0)
        assert res == 0x41AF3000

        # AUIPC
        res = ex.alu(0b00101, 0, 0, 0x41AF3000, 0x10000000, 0, 0)
        assert res == 0x51AF3000

        # JAL
        res = ex.alu(0b11011, 0, 0, 0xB5E64, 0x80000000, 0, 0)
        assert res == 0x800B5E64

        res = ex.alu(0b11011, 0, 0, 0xffffffec, 0x90000000, 0, 0)
        assert res == 0x8FFFFFEC

        # JALR
        res = ex.alu(0b11001, 0x40000000, 0, 0x401, 0, 0, 0)
        assert res == 0x40000400

        res = ex.alu(0b11001, 0x90000000, 0, 0xffffffec, 0, 0, 0)
        assert res == 0x8FFFFFEC

        # BRANCH
        res = ex.alu(0b11000, 0, 0, 0xD58, 0x80000000, 0, 0)
        assert res == 0x80000D58

        res = ex.alu(0b11000, 0, 0, 0xffffffec, 0x90000000, 0, 0)
        assert res == 0x8FFFFFEC

        # LOAD
        res = ex.alu(0b00000, 0x60000000, 0, 0x7D2, 0, 0, 0)
        assert res == 0x600007D2

        # STORE
        res = ex.alu(0b01000, 0x60000000, 0, 0x7D2, 0, 0, 0)
        assert res == 0x600007D2

        # ADDI
        res = ex.alu(0b00100, 0x42, 0, 0x4593, 0, 0b000, 0)
        assert res == 0x45D5

        # SLTI
        res = ex.alu(opcode=0b00100, rs1=0, rs2=0, imm=0, pc=0, f3=0b010, f7=0)
        assert res == 0

        res = ex.alu(opcode=0b00100, rs1=1, rs2=0, imm=1, pc=0, f3=0b010, f7=0)
        assert res == 0

        res = ex.alu(opcode=0b00100, rs1=3, rs2=0, imm=7, pc=0, f3=0b010, f7=0)
        assert res == 1

        res = ex.alu(opcode=0b00100, rs1=0x80000000, rs2=0, imm=0, pc=0, f3=0b010, f7=0)
        assert res == 1

        res = ex.alu(opcode=0b00100, rs1=0x7fffffff, rs2=0, imm=0xfffff800, pc=0, f3=0b010, f7=0)
        assert res == 0

        res = ex.alu(opcode=0b00100, rs1=0x80000000, rs2=0, imm=0xfffff800, pc=0, f3=0b010, f7=0)
        assert res == 0

        # SLTIU
        res = ex.alu(opcode=0b00100, rs1=0, rs2=0, imm=0, pc=0, f3=0b011, f7=0)
        assert res == 0

        res = ex.alu(opcode=0b00100, rs1=1, rs2=0, imm=1, pc=0, f3=0b011, f7=0)
        assert res == 0

        res = ex.alu(opcode=0b00100, rs1=3, rs2=0, imm=7, pc=0, f3=0b011, f7=0)
        assert res == 1

        res = ex.alu(opcode=0b00100, rs1=7, rs2=0, imm=3, pc=0, f3=0b011, f7=0)
        assert res == 0

        res = ex.alu(opcode=0b00100, rs1=0, rs2=0, imm=0xfffff800, pc=0, f3=0b011, f7=0)
        assert res == 1

        res = ex.alu(opcode=0b00100, rs1=0x80000000, rs2=0, imm=0xfffff800, pc=0, f3=0b011, f7=0)
        assert res == 1

        # XORI
        res = ex.alu(opcode=0b00100, rs1=0x00ff0f00, rs2=0, imm=0xffffff0f, pc=0, f3=0b100, f7=0)
        assert res == 0xff00f00f

        res = ex.alu(opcode=0b00100, rs1=0x00ff08ff, rs2=0, imm=0x0000070f, pc=0, f3=0b100, f7=0)
        assert res == 0x00ff0ff0

        # ORI
        res = ex.alu(opcode=0b00100, rs1=0xff00ff00, rs2=0, imm=0xffffff0f, pc=0, f3=0b110, f7=0)
        assert res == 0xffffff0f

        res = ex.alu(opcode=0b00100, rs1=0x00ff00ff, rs2=0, imm=0x0000070f, pc=0, f3=0b110, f7=0)
        assert res == 0x00ff07ff

        # ANDI
        res = ex.alu(opcode=0b00100, rs1=0xff00ff00, rs2=0, imm=0xffffff0f, pc=0, f3=0b111, f7=0)
        assert res == 0xff00ff00

        res = ex.alu(opcode=0b00100, rs1=0x00ff00ff, rs2=0, imm=0x0000070f, pc=0, f3=0b111, f7=0)
        assert res == 0x0000000f

        # SLLI
        res = ex.alu(opcode=0b00100, rs1=0x00000001, rs2=0, imm=0, pc=0, f3=0b001, f7=0)
        assert res == 0x00000001

        res = ex.alu(opcode=0b00100, rs1=0x00000001, rs2=0, imm=1, pc=0, f3=0b001, f7=0)
        assert res == 0x00000002

        res = ex.alu(opcode=0b00100, rs1=0x00000001, rs2=0, imm=7, pc=0, f3=0b001, f7=0)
        assert res == 0x00000080

        res = ex.alu(opcode=0b00100, rs1=0x00000001, rs2=0, imm=31, pc=0, f3=0b001, f7=0)
        assert res == 0x80000000
        
        res = ex.alu(opcode=0b00100, rs1=0xffffffff, rs2=0, imm=7, pc=0, f3=0b001, f7=0)
        assert res == 0xffffff80

        res = ex.alu(opcode=0b00100, rs1=0x21212121, rs2=0, imm=14, pc=0, f3=0b001, f7=0)
        assert res == 0x48484000

        # SRLI
        res = ex.alu(opcode=0b00100, rs1=0x00000001, rs2=0, imm=0, pc=0, f3=0b101, f7=0)
        assert res == 0x00000001

        res = ex.alu(opcode=0b00100, rs1=0x00000001, rs2=0, imm=1, pc=0, f3=0b101, f7=0)
        assert res == 0x00000000

        res = ex.alu(opcode=0b00100, rs1=0x00000001, rs2=0, imm=7, pc=0, f3=0b101, f7=0)
        assert res == 0x00000000

        res = ex.alu(opcode=0b00100, rs1=0x00000001, rs2=0, imm=31, pc=0, f3=0b101, f7=0)
        assert res == 0x00000000
        
        res = ex.alu(opcode=0b00100, rs1=0xffffffff, rs2=0, imm=7, pc=0, f3=0b101, f7=0)
        assert res == 0x01ffffff

        res = ex.alu(opcode=0b00100, rs1=0x21212121, rs2=0, imm=14, pc=0, f3=0b101, f7=0)
        assert res == 0x00008484

        # SRAI
        res = ex.alu(opcode=0b00100, rs1=0x7fffffff, rs2=0, imm=0, pc=0, f3=0b101, f7=0b0100000)
        assert res == 0x7fffffff

        res = ex.alu(opcode=0b00100, rs1=0x7fffffff, rs2=0, imm=1, pc=0, f3=0b101, f7=0b0100000)
        assert res == 0x3fffffff

        res = ex.alu(opcode=0b00100, rs1=0x81818181, rs2=0, imm=1, pc=0, f3=0b101, f7=0b0100000)
        assert res == 0xc0c0c0c0

        res = ex.alu(opcode=0b00100, rs1=0x81818181, rs2=0, imm=7, pc=0, f3=0b101, f7=0b0100000)
        assert res == 0xff030303

        res = ex.alu(opcode=0b00100, rs1=0x81818181, rs2=0, imm=31, pc=0, f3=0b101, f7=0b0100000)
        assert res == 0xffffffff

        # ADD
        res = ex.alu(opcode=0b01100, rs1=0x42, rs2=0x4593, imm=0, pc=0, f3=0b000, f7=0)
        assert res == 0x45D5

        # SUB
        res = ex.alu(opcode=0b01100, rs1=0, rs2=0, imm=0, pc=0, f3=0b000, f7=0b0100000)
        assert res == 0x00000000

        res = ex.alu(opcode=0b01100, rs1=1, rs2=1, imm=0, pc=0, f3=0b000, f7=0b0100000)
        assert res == 0x00000000

        res = ex.alu(opcode=0b01100, rs1=3, rs2=7, imm=0, pc=0, f3=0b000, f7=0b0100000)
        assert res == 0xfffffffc

        res = ex.alu(opcode=0b01100, rs1=0, rs2=0xffff8000, imm=0, pc=0, f3=0b000, f7=0b0100000)
        assert res == 0x00008000

        res = ex.alu(opcode=0b01100, rs1=0, rs2=0x00007fff, imm=0, pc=0, f3=0b000, f7=0b0100000)
        assert res == 0xffff8001

        res = ex.alu(opcode=0b01100, rs1=0x7fffffff, rs2=0xffff8000, imm=0, pc=0, f3=0b000, f7=0b0100000)
        assert res == 0x80007fff

        # SLL
        res = ex.alu(opcode=0b01100, rs1=1, rs2=0, imm=0, pc=0, f3=0b001, f7=0b0000000)
        assert res == 0x00000001

        res = ex.alu(opcode=0b01100, rs1=1, rs2=1, imm=0, pc=0, f3=0b001, f7=0b0000000)
        assert res == 0x00000002

        res = ex.alu(opcode=0b01100, rs1=1, rs2=7, imm=0, pc=0, f3=0b001, f7=0b0000000)
        assert res == 0x00000080

        res = ex.alu(opcode=0b01100, rs1=1, rs2=31, imm=0, pc=0, f3=0b001, f7=0b0000000)
        assert res == 0x80000000
        
        res = ex.alu(opcode=0b01100, rs1=0xffffffff, rs2=7, imm=0, pc=0, f3=0b001, f7=0b0000000)
        assert res == 0xffffff80

        res = ex.alu(opcode=0b01100, rs1=0x21212121, rs2=14, imm=0, pc=0, f3=0b001, f7=0b0000000)
        assert res == 0x48484000

        # SLT
        res = ex.alu(opcode=0b01100, rs1=0, imm=0, rs2=0, pc=0, f3=0b010, f7=0)
        assert res == 0

        res = ex.alu(opcode=0b01100, rs1=1, imm=0, rs2=1, pc=0, f3=0b010, f7=0)
        assert res == 0

        res = ex.alu(opcode=0b01100, rs1=3, imm=0, rs2=7, pc=0, f3=0b010, f7=0)
        assert res == 1

        res = ex.alu(opcode=0b01100, rs1=0x80000000, imm=0, rs2=0, pc=0, f3=0b010, f7=0)
        assert res == 1

        res = ex.alu(opcode=0b01100, rs1=0x7fffffff, imm=0, rs2=0xfffff800, pc=0, f3=0b010, f7=0)
        assert res == 0

        res = ex.alu(opcode=0b01100, rs1=0x80000000, imm=0, rs2=0xfffff800, pc=0, f3=0b010, f7=0)
        assert res == 0

        # SLTU
        res = ex.alu(opcode=0b01100, rs1=0, imm=0, rs2=0, pc=0, f3=0b011, f7=0)
        assert res == 0

        res = ex.alu(opcode=0b01100, rs1=1, imm=0, rs2=1, pc=0, f3=0b011, f7=0)
        assert res == 0

        res = ex.alu(opcode=0b01100, rs1=3, imm=0, rs2=7, pc=0, f3=0b011, f7=0)
        assert res == 1

        res = ex.alu(opcode=0b01100, rs1=7, imm=0, rs2=3, pc=0, f3=0b011, f7=0)
        assert res == 0

        res = ex.alu(opcode=0b01100, rs1=0, imm=0, rs2=0xfffff800, pc=0, f3=0b011, f7=0)
        assert res == 1

        res = ex.alu(opcode=0b01100, rs1=0x80000000, imm=0, rs2=0xfffff800, pc=0, f3=0b011, f7=0)
        assert res == 1

        # XOR
        res = ex.alu(opcode=0b01100, rs1=0x00ff0f00, rs2=0xffffff0f, imm=0, pc=0, f3=0b100, f7=0)
        assert res == 0xff00f00f

        res = ex.alu(opcode=0b01100, rs1=0x00ff08ff, rs2=0x0000070f, imm=0, pc=0, f3=0b100, f7=0)
        assert res == 0x00ff0ff0

        # SRL
        res = ex.alu(opcode=0b01100, rs1=0x00000001, imm=0, rs2=0, pc=0, f3=0b101, f7=0)
        assert res == 0x00000001

        res = ex.alu(opcode=0b01100, rs1=0x00000001, imm=0, rs2=1, pc=0, f3=0b101, f7=0)
        assert res == 0x00000000

        res = ex.alu(opcode=0b01100, rs1=0x00000001, imm=0, rs2=7, pc=0, f3=0b101, f7=0)
        assert res == 0x00000000

        res = ex.alu(opcode=0b01100, rs1=0x00000001, imm=0, rs2=31, pc=0, f3=0b101, f7=0)
        assert res == 0x00000000
        
        res = ex.alu(opcode=0b01100, rs1=0xffffffff, imm=0, rs2=7, pc=0, f3=0b101, f7=0)
        assert res == 0x01ffffff

        res = ex.alu(opcode=0b01100, rs1=0x21212121, imm=0, rs2=14, pc=0, f3=0b101, f7=0)
        assert res == 0x00008484

        # SRA
        res = ex.alu(opcode=0b01100, rs1=0x7fffffff, imm=0, rs2=0, pc=0, f3=0b101, f7=0b0100000)
        assert res == 0x7fffffff

        res = ex.alu(opcode=0b01100, rs1=0x7fffffff, imm=0, rs2=1, pc=0, f3=0b101, f7=0b0100000)
        assert res == 0x3fffffff

        res = ex.alu(opcode=0b01100, rs1=0x81818181, imm=0, rs2=1, pc=0, f3=0b101, f7=0b0100000)
        assert res == 0xc0c0c0c0

        res = ex.alu(opcode=0b01100, rs1=0x81818181, imm=0, rs2=7, pc=0, f3=0b101, f7=0b0100000)
        assert res == 0xff030303

        res = ex.alu(opcode=0b01100, rs1=0x81818181, imm=0, rs2=31, pc=0, f3=0b101, f7=0b0100000)
        assert res == 0xffffffff

        # OR
        res = ex.alu(opcode=0b01100, rs1=0xff00ff00, imm=0, rs2=0xffffff0f, pc=0, f3=0b110, f7=0)
        assert res == 0xffffff0f

        res = ex.alu(opcode=0b01100, rs1=0x00ff00ff, imm=0, rs2=0x0000070f, pc=0, f3=0b110, f7=0)
        assert res == 0x00ff07ff

        # AND
        res = ex.alu(opcode=0b01100, rs1=0xff00ff00, imm=0, rs2=0xffffff0f, pc=0, f3=0b111, f7=0)
        assert res == 0xff00ff00

        res = ex.alu(opcode=0b01100, rs1=0x00ff00ff, imm=0, rs2=0x0000070f, pc=0, f3=0b111, f7=0)
        assert res == 0x0000000f

    def test_branch(self):
        ex = EXStage()

        # BEQ
        res = ex.branch(f3=0, rs1=0, rs2=0)
        assert res == True

        res = ex.branch(f3=0, rs1=1, rs2=1)
        assert res == True

        res = ex.branch(f3=0, rs1=-1, rs2=-1)
        assert res == True

        res = ex.branch(f3=0, rs1=0, rs2=1)
        assert res == False

        res = ex.branch(f3=0, rs1=1, rs2=0)
        assert res == False

        res = ex.branch(f3=0, rs1=-1, rs2=1)
        assert res == False

        # BNE
        res = ex.branch(f3=1, rs1=0, rs2=0)
        assert res == False

        res = ex.branch(f3=1, rs1=1, rs2=1)
        assert res == False

        res = ex.branch(f3=1, rs1=-1, rs2=-1)
        assert res == False

        res = ex.branch(f3=1, rs1=0, rs2=1)
        assert res == True

        res = ex.branch(f3=1, rs1=1, rs2=0)
        assert res == True

        res = ex.branch(f3=1, rs1=-1, rs2=1)
        assert res == True

        # BLT
        res = ex.branch(f3=4, rs1=0, rs2=1)
        assert res == True

        res = ex.branch(f3=4, rs1=MASK_32&(-1), rs2=1)
        assert res == True

        res = ex.branch(f3=4, rs1=MASK_32&(-2), rs2=MASK_32&(-1))
        assert res == True

        res = ex.branch(f3=4, rs1=1, rs2=0)
        assert res == False

        res = ex.branch(f3=4, rs1=1, rs2=MASK_32&(-1))
        assert res == False

        res = ex.branch(f3=4, rs1=MASK_32&(-1), rs2=MASK_32&(-2))
        assert res == False

        res = ex.branch(f3=4, rs1=1, rs2=MASK_32&(-2))
        assert res == False

        # BGE
        res = ex.branch(f3=5, rs1=0, rs2=0)
        assert res == True
    
        res = ex.branch(f3=5, rs1=1, rs2=1)
        assert res == True
    
        res = ex.branch(f3=5, rs1=MASK_32&(-1), rs2=MASK_32&(-1))
        assert res == True
    
        res = ex.branch(f3=5, rs1=1, rs2=0)
        assert res == True
    
        res = ex.branch(f3=5, rs1=1, rs2=MASK_32&(-1))
        assert res == True
    
        res = ex.branch(f3=5, rs1=MASK_32&(-1), rs2=MASK_32&(-2))
        assert res == True

        res = ex.branch(f3=5, rs1=0, rs2=1)
        assert res == False
    
        res = ex.branch(f3=5, rs1=MASK_32&(-1), rs2=1)
        assert res == False
    
        res = ex.branch(f3=5, rs1=MASK_32&(-2), rs2=MASK_32&(-1))
        assert res == False

        res = ex.branch(f3=5, rs1=MASK_32&(-2), rs2=1)
        assert res == False

        # BLTU
        res = ex.branch(f3=6, rs1=0x00000000, rs2=0x00000001)
        assert res == True

        res = ex.branch(f3=6, rs1=0xfffffffe, rs2=0xffffffff)
        assert res == True

        res = ex.branch(f3=6, rs1=0x00000000, rs2=0xffffffff)
        assert res == True

        res = ex.branch(f3=6, rs1=0x00000001, rs2=0x00000000)
        assert res == False

        res = ex.branch(f3=6, rs1=0xffffffff, rs2=0xfffffffe)
        assert res == False

        res = ex.branch(f3=6, rs1=0xffffffff, rs2=0x00000000)
        assert res == False

        res = ex.branch(f3=6, rs1=0x80000000, rs2=0x7fffffff)
        assert res == False

        # BGEU
        res = ex.branch(f3=7, rs1=0x00000000, rs2=0x00000000)
        assert res == True
        
        res = ex.branch(f3=7, rs1=0x00000001, rs2=0x00000001)
        assert res == True

        res = ex.branch(f3=7, rs1=0xffffffff, rs2=0xffffffff)
        assert res == True

        res = ex.branch(f3=7, rs1=0x00000001, rs2=0x00000000)
        assert res == True

        res = ex.branch(f3=7, rs1=0xffffffff, rs2=0xfffffffe)
        assert res == True

        res = ex.branch(f3=7, rs1=0xffffffff, rs2=0x00000000)
        assert res == True

        res = ex.branch(f3=7, rs1=0x00000000, rs2=0x00000001)
        assert res == False

        res = ex.branch(f3=7, rs1=0xfffffffe, rs2=0xffffffff)
        assert res == False

        res = ex.branch(f3=7, rs1=0x00000000, rs2=0xffffffff)
        assert res == False

        res = ex.branch(f3=7, rs1=0x7fffffff, rs2=0x80000000)
        assert res == False
    
    def test_EXStage(self, sim):
        ex = EXStage()

        # LUI x24, 0xaffe
        ex.IDEX_i.write(IDEX_t(
            rs1=0,
            rs2=0,
            imm=0xaffe<<12,
            pc=0,
            rd=24,
            we=True,
            wb_sel=0,
            opcode=0b01101
        ))
        sim.process_queue()
        out = ex.EXMEM_o.read()
        assert out.take_branch == False
        assert out.alu_res == 0xaffe<<12
        assert out.rd == 24
        assert out.we == True
        assert out.wb_sel == 0

        # AUIPC x24, 0xaffe
        ex.IDEX_i.write(IDEX_t(
            rs1=0,
            rs2=0,
            imm=0xaffe<<12,
            pc=0x80000000,
            rd=24,
            we=True,
            wb_sel=0,
            opcode=0b00101
        ))
        sim.process_queue()
        out = ex.EXMEM_o.read()
        assert out.take_branch == False
        assert out.alu_res == 0x8AFFE000
        assert out.rd == 24
        assert out.we == True
        assert out.wb_sel == 0

        # JAL x13, 0x2DA89
        ex.IDEX_i.write(IDEX_t(
            rs1=0,
            rs2=0,
            imm=0x2DA8A<<1,
            pc=0x80004000,
            rd=13,
            we=True,
            wb_sel=1,
            opcode=0b11011
        ))
        sim.process_queue()
        out = ex.EXMEM_o.read()
        assert out.take_branch == True
        assert out.alu_res == 0x8005F514
        assert out.rd == 13
        assert out.we == True
        assert out.wb_sel == 1
        assert out.pc4 == 0x80004004

        # JALR x13, x28, 0x401 (note: reg x28 not explictly needed; EXStage receives value of rs1)
        ex.IDEX_i.write(IDEX_t(
            rs1=0x4200,
            rs2=0,
            imm=0x401,
            pc=0x80004000,
            rd=13,
            we=True,
            wb_sel=1,
            opcode=0b11001
        ))
        sim.process_queue()
        out = ex.EXMEM_o.read()
        assert out.take_branch == True
        assert out.alu_res == 0x4600
        assert out.rd == 13
        assert out.we == True
        assert out.wb_sel == 1
        assert out.pc4 == 0x80004004

    def test_exception(self, caplog, sim):
        ex = EXStage()

        pc = 0x80004000

        # --- Misaligned instruction address ---------
        # JAL x13, 0x2DA89
        ex.IDEX_i.write(IDEX_t(
            rs1=0,
            rs2=0,
            imm=0x2DA89<<1,
            pc=pc,
            rd=13,
            opcode=0b11011
        ))
        with pytest.raises(Exception, match = f"Target instruction address misaligned exception at PC = 0x{pc:08X}"):
            sim.process_queue()
        pc += 4

        # JALR x13, rs1, 0xA8A
        ex.IDEX_i.write(IDEX_t(
            rs1=0x80100000,
            rs2=0,
            imm=0xA8A,
            pc=pc,
            rd=13,
            opcode=0b11001
        ))
        with pytest.raises(Exception, match = f"Target instruction address misaligned exception at PC = 0x{pc:08X}"):
            sim.process_queue()
        pc += 4

        # BEQ
        ex.IDEX_i.write(IDEX_t(
            rs1=0,
            rs2=0,
            imm=0xA8B<<1,
            pc=pc,
            funct3=0,
            opcode=0b11000
        ))
        with pytest.raises(Exception, match = f"Target instruction address misaligned exception at PC = 0x{pc:08X}"):
            sim.process_queue()
        pc += 4

        # BNE
        ex.IDEX_i.write(IDEX_t(
            rs1=0,
            rs2=1,
            imm=0xA8B<<1,
            pc=pc,
            funct3=1,
            opcode=0b11000
        ))
        with pytest.raises(Exception, match = f"Target instruction address misaligned exception at PC = 0x{pc:08X}"):
            sim.process_queue()
        pc += 4

        # BLT
        ex.IDEX_i.write(IDEX_t(
            rs1=0,
            rs2=1,
            imm=0xA8B<<1,
            pc=pc,
            funct3=4,
            opcode=0b11000
        ))
        with pytest.raises(Exception, match = f"Target instruction address misaligned exception at PC = 0x{pc:08X}"):
            sim.process_queue()
        pc += 4

        # BGE
        ex.IDEX_i.write(IDEX_t(
            rs1=1,
            rs2=0,
            imm=0xA8B<<1,
            pc=pc,
            funct3=5,
            opcode=0b11000
        ))
        with pytest.raises(Exception, match = f"Target instruction address misaligned exception at PC = 0x{pc:08X}"):
            sim.process_queue()
        pc += 4

        # BLTU
        ex.IDEX_i.write(IDEX_t(
            rs1=0,
            rs2=1,
            imm=0xA8B<<1,
            pc=pc,
            funct3=6,
            opcode=0b11000
        ))
        with pytest.raises(Exception, match = f"Target instruction address misaligned exception at PC = 0x{pc:08X}"):
            sim.process_queue()
        pc += 4

        # BGEU
        ex.IDEX_i.write(IDEX_t(
            rs1=1,
            rs2=0,
            imm=0xA8B<<1,
            pc=pc,
            funct3=7,
            opcode=0b11000
        ))
        with pytest.raises(Exception, match = f"Target instruction address misaligned exception at PC = 0x{pc:08X}"):
            sim.process_queue()
        pc += 4

        # No exception for not-taken branch
        # BEQ
        ex.IDEX_i.write(IDEX_t(
            rs1=1,
            rs2=0,
            imm=0xA8B<<1,
            pc=pc,
            funct3=0,
            opcode=0b11000
        ))
        sim.process_queue()
        pc += 4




# ---------------------------------------
# Test MEMORY
# ---------------------------------------
class TestMEMStage:
    def test_constructor(self):
        mem = MEMStage(Memory(1024))

        # Check Port types
        assert mem.EXMEM_i._type == EXMEM_t
        assert mem.MEMWB_o._type == MEMWB_t
        
    def test_passThrough(self, sim):
        mem = MEMStage(Memory(1024))
        mem.EXMEM_i.write(EXMEM_t(
            rd=1,
            we=1,
            wb_sel=2,
            pc4=0xdeadbeef,
            alu_res=0xaffeaffe
        ))
        sim.process_queue()
        out = mem.MEMWB_o.read()
        assert out.rd == 1
        assert out.we == 1
        assert out.wb_sel == 2
        assert out.pc4 == 0xdeadbeef
        assert out.alu_res == 0xaffeaffe

    def test_load(self, sim):
        mem = MEMStage(Memory(1024))
        # Load memory
        mem.mem.writeRequest(0, 0xdeadbeef, 4)
        mem.mem._tick()
        mem.mem.writeRequest(4, 0xbade0123, 4)
        mem.mem._tick()

        # LB
        mem.EXMEM_i.write(EXMEM_t(
            mem=1, # load
            alu_res=2, # addr
            funct3=0 #lb
        ))
        sim.process_queue()
        assert mem.MEMWB_o.read().mem_rdata == 0xffffffad

        mem.EXMEM_i.write(EXMEM_t(
            mem=1, # load
            alu_res=5, # addr
            funct3=0 #lb
        ))
        sim.process_queue()
        assert mem.MEMWB_o.read().mem_rdata == 0x00000001 

        # LH
        mem.EXMEM_i.write(EXMEM_t(
            mem=1, # load
            alu_res=2, # addr
            funct3=1 # lh
        ))
        sim.process_queue()
        assert mem.MEMWB_o.read().mem_rdata == 0xffffdead

        mem.EXMEM_i.write(EXMEM_t(
            mem=1, # load
            alu_res=4, # addr
            funct3=1 # lh
        ))
        sim.process_queue()
        assert mem.MEMWB_o.read().mem_rdata == 0x00000123 

        # LW
        mem.EXMEM_i.write(EXMEM_t(
            mem=1, # load
            alu_res=0, # addr
            funct3=2 # lw
        ))
        sim.process_queue()
        assert mem.MEMWB_o.read().mem_rdata == 0xdeadbeef

        # LBU
        mem.EXMEM_i.write(EXMEM_t(
            mem=1, # load
            alu_res=2, # addr
            funct3=4 # lbu
        ))
        sim.process_queue()
        assert mem.MEMWB_o.read().mem_rdata == 0xad

        # LHU
        mem.EXMEM_i.write(EXMEM_t(
            mem=1, # load
            alu_res=2, # addr
            funct3=5 # lbu
        ))
        sim.process_queue()
        assert mem.MEMWB_o.read().mem_rdata == 0xdead

    def test_store(self, sim):
        mem = MEMStage(Memory(1024))

        # SB
        mem.EXMEM_i.write(EXMEM_t(
            mem=2, # store
            alu_res=3, # addr
            rs2=0xabadbabe, # wdata
            funct3=0 # sb
        ))
        sim.process_queue()
        mem.mem._tick()
        assert mem.mem.read(3, 1) == 0xbe

        mem.mem.writeRequest(0, 0, 4)
        mem.mem._tick()

        # SH
        mem.EXMEM_i.write(EXMEM_t(
            mem=2, # store
            alu_res=0, # addr
            rs2=0xabadbabe, # wdata
            funct3=1 # sh
        ))
        sim.process_queue()
        mem.mem._tick()
        assert mem.mem.read(0, 2) == 0xbabe

        # SW
        mem.EXMEM_i.write(EXMEM_t(
            mem=2, # store
            alu_res=0, # addr
            rs2=0xabadbabe, # wdata
            funct3=2 # sw
        ))
        sim.process_queue()
        mem.mem._tick()
        assert mem.mem.read(0, 4) == 0xabadbabe

    def test_exception(self, caplog, sim):
        mem = MEMStage(Memory(16))

        # --- Load address misaligned ---------------
        # LH/LHU
        mem.EXMEM_i.write(EXMEM_t(
            mem=1, # load
            alu_res=1, # addr
            funct3=1 # lh
        ))
        sim.process_queue()
        assert f"Misaligned load from address 0x00000001" in caplog.text
        caplog.clear()

        # LW
        mem.EXMEM_i.write(EXMEM_t(
            mem=1, # load
            alu_res=3, # addr
            funct3=2 # lw
        ))
        sim.process_queue()
        assert f"Misaligned load from address 0x00000003" in caplog.text
        caplog.clear()

        # --- Store address misaligned --------------
        # SH
        mem.EXMEM_i.write(EXMEM_t(
            mem=2, # store
            alu_res=1, # addr
            funct3=1 # sh
        ))
        sim.process_queue()
        assert f"Misaligned store to address 0x00000001" in caplog.text
        caplog.clear()

        # SW
        mem.EXMEM_i.write(EXMEM_t(
            mem=2, # store
            alu_res=3, # addr
            funct3=2 # sw
        ))
        sim.process_queue()
        assert f"Misaligned store to address 0x00000003" in caplog.text
        caplog.clear()

# ---------------------------------------
# Test WRITE-BACK
# ---------------------------------------
class TestWBStage:
    def test_constructor(self):
        regf = Regfile()
        wb = WBStage(regf)

        assert wb.MEMWB_i._type == MEMWB_t

    def test_wb(self, sim):
        wb = WBStage(Regfile())

        # ALU op
        wb.MEMWB_i.write(MEMWB_t(
            rd=18,
            we=1,
            alu_res=42,
            pc4=87,
            mem_rdata=0xdeadbeef,
            wb_sel=0
        ))
        sim.process_queue()
        wb.regfile._tick()
        assert wb.regfile.read(18) == 42

        # PC+4 (JAL)
        wb.MEMWB_i.write(MEMWB_t(
            rd=31,
            we=1,
            alu_res=42,
            pc4=87,
            mem_rdata=0xdeadbeef,
            wb_sel=1
        ))
        sim.process_queue()
        wb.regfile._tick()
        assert wb.regfile.read(31) == 87

        # Memory load
        wb.MEMWB_i.write(MEMWB_t(
            rd=4,
            we=1,
            alu_res=42,
            pc4=87,
            mem_rdata=0xdeadbeef,
            wb_sel=2
        ))
        sim.process_queue()
        wb.regfile._tick()
        assert wb.regfile.read(4) == 0xdeadbeef

    def test_no_wb(self, sim):
        wb = WBStage(Regfile())

        wb.regfile.writeRequest(25, 1234)
        wb.regfile._tick()

        val = MEMWB_t(
            we=0,
            rd=25,
            alu_res=24,
            pc4=25,
            mem_rdata=26
        )

        # ALU op
        val.wb_sel = 0
        wb.MEMWB_i.write(val)
        sim.process_queue()
        wb.regfile._tick()
        assert wb.regfile.read(25) == 1234

        # PC+4 (JAL)
        val.wb_sel = 1
        wb.MEMWB_i.write(val)
        sim.process_queue()
        wb.regfile._tick()
        assert wb.regfile.read(25) == 1234

        # Memory load
        val.wb_sel = 2
        wb.MEMWB_i.write(val)
        sim.process_queue()
        wb.regfile._tick()
        assert wb.regfile.read(25) == 1234

# ---------------------------------------
# Test Branch Unit
# ---------------------------------------
def test_branch_unit(sim):
    bu = BranchUnit()

    # Test ports
    assert bu.pc_i._type == int
    assert bu.take_branch_i._type == int
    assert bu.target_i._type == int
    assert bu.npc_o._type == int

    # Test regular PC increment
    bu.pc_i.write(0x80000000)
    bu.take_branch_i.write(0)
    bu.target_i.write(0x40000000)
    sim.process_queue()
    assert bu.npc_o.read() == 0x80000004 

    # Test taken branch
    bu.pc_i.write(0x80000000)
    bu.take_branch_i.write(1)
    bu.target_i.write(0x40000000)
    sim.process_queue()
    assert bu.npc_o.read() == 0x40000000
