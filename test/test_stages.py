import pytest
from test.fixtures import clear_reg_list
from pyv.stages import *
from pyv.reg import *
from pyv.util import MASK_32
from pyv.mem import Memory

def test_sanity():
    assert True

# ---------------------------------------
# Test FETCH
# ---------------------------------------
def test_IFStage():
    clear_reg_list()

    fetch = IFStage(Memory(1024))

    # SW a0,-20(s0) = SW, x10, -20(x8)
    fetch.imem.write(0, 0xfea42623, 4)
    fetch.npc_i.write(0x00000000)

    fetch.process()
    RegBase.updateRegs()

    out = fetch.IFID_o.read()
    assert out['inst'] == 0xfea42623
    assert out['pc'] == 0x00000000

# ---------------------------------------
# Test DECODE
# ---------------------------------------
class TestIDStage:
    def test_constructor(self):
        regf = Regfile()
        dec = IDStage(regf)

        assert regf == dec.regfile

        in_ports = ['inst', 'pc']
        assert len(dec.IFID_i.val) == len(in_ports)
        for port in in_ports:
            assert (port in dec.IFID_i.val)
        
        out_ports = ['rs1', 'rs2', 'imm', 'pc', 'rd', 'we', 'wb_sel', 'opcode', 'funct3', 'funct7', 'mem']
        assert len(dec.IDEX_o.val) == len(out_ports)
        for port in out_ports:
            assert (port in dec.IDEX_o.val)

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
        assert out['mem'] == 2

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
        assert out['mem'] == 0

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
        assert out['mem'] == 0

        # Test wb_sel
        res = decode.wb_sel(0b11011)
        assert res == 1
        res = decode.wb_sel(0)
        assert res == 2
        res = decode.wb_sel(0b01100)
        assert res == 0

        # Test LOAD
        # LW x15, x8, 0x456
        regf.write(8, 0x40000000)
        decode.IFID_i.write('inst', 0x45642783)
        decode.process()
        out = decode.IDEX_o.read()
        assert out['rs1'] == 0x40000000
        assert out['imm'] == 0x456
        assert out['pc'] == 0x80000004
        assert out['rd'] == 15
        assert out['we'] == True
        assert out['wb_sel'] == 2
        assert out['opcode'] == 0b00000
        assert out['funct3'] == 0b010
        assert out['mem'] == 1

# ---------------------------------------
# Test EXECUTE
# ---------------------------------------
class TestEXStage:
    def test_constructor(self):
        ex = EXStage()

        in_ports = ['rd',
                    'we',
                    'imm',
                    'pc',
                    'rs1',
                    'rs2',
                    'mem',
                    'wb_sel',
                    'opcode',
                    'funct3',
                    'funct7'
                   ]
        assert len(ex.IDEX_i.val) == len(in_ports)
        for port in in_ports:
            assert (port in ex.IDEX_i.val)

        out_ports = ['rd',
                     'we',
                     'wb_sel',
                     'take_branch',
                     'alu_res',
                     'pc4',
                     'rs2',
                     'mem',
                     'funct3'
                     ]
        assert len(ex.EXMEM_o.val) == len(out_ports)
        for port in out_ports:
            assert (port in ex.EXMEM_o.val)
        
    def test_passThrough(self):
        ex = EXStage()

        ex.IDEX_i.write('rd', 1,
                        'we', 1,
                        'wb_sel', 2,
                        'rs2', 23,
                        'mem', 1,
                        'funct3', 5
                       )
        #ex.process()
        assert ex.EXMEM_o['rd'].read() == 1
        assert ex.EXMEM_o['we'].read() == 1
        assert ex.EXMEM_o['wb_sel'].read() == 2
        assert ex.EXMEM_o['rs2'].read() == 23
        assert ex.EXMEM_o['mem'].read() == 1
        assert ex.EXMEM_o['funct3'].read() == 5

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
    
    def test_EXStage(self):
        ex = EXStage()

        # Test pass throughs
        ex.IDEX_i.write('rd', 24,
                        'we', True,
                        'wb_sel', 2,
                        'rs2', 0xdeadbeef,
                        'mem', 2,
                        'funct3', 5)
        #ex.process()
        out = ex.EXMEM_o.read()
        assert out['rd'] == 24
        assert out['we'] == True
        assert out['wb_sel'] == 2
        assert out['rs2'] == 0xdeadbeef
        assert out['mem'] == 2
        assert out['funct3'] == 5

        # LUI x24, 0xaffe
        ex.IDEX_i.write('rs1', 0,
                        'rs2', 0,
                        'imm', 0xaffe<<12,
                        'pc', 0,
                        'rd', 24,
                        'we', True,
                        'wb_sel', 0,
                        'opcode', 0b01101)
        ex.process()
        out = ex.EXMEM_o.read()
        assert out['take_branch'] == False
        assert out['alu_res'] == 0xaffe<<12
        assert out['rd'] == 24
        assert out['we'] == True
        assert out['wb_sel'] == 0

        # AUIPC x24, 0xaffe
        ex.IDEX_i.write('rs1', 0,
                        'rs2', 0,
                        'imm', 0xaffe<<12,
                        'pc', 0x80000000,
                        'rd', 24,
                        'we', True,
                        'wb_sel', 0,
                        'opcode', 0b00101)
        ex.process()
        out = ex.EXMEM_o.read()
        assert out['take_branch'] == False
        assert out['alu_res'] == 0x8AFFE000
        assert out['rd'] == 24
        assert out['we'] == True
        assert out['wb_sel'] == 0

        # JAL x13, 0x2DA89
        ex.IDEX_i.write('rs1', 0,
                        'rs2', 0,
                        'imm', 0x2DA89<<1,
                        'pc', 0x80004000,
                        'rd', 13,
                        'we', True,
                        'wb_sel', 1,
                        'opcode', 0b11011)
        ex.process()
        out = ex.EXMEM_o.read()
        assert out['take_branch'] == True
        assert out['alu_res'] == 0x8005F512
        assert out['rd'] == 13
        assert out['we'] == True
        assert out['wb_sel'] == 1
        assert out['pc4'] == 0x80004004

        # JALR x13, x28, 0x401 (note: reg x28 not explictly needed; EXStage receives value of rs1)
        ex.IDEX_i.write('rs1', 0x4200,
                        'rs2', 0,
                        'imm', 0x401,
                        'pc', 0x80004000,
                        'rd', 13,
                        'we', True,
                        'wb_sel', 1,
                        'opcode', 0b11001)
        ex.process()
        out = ex.EXMEM_o.read()
        assert out['take_branch'] == True
        assert out['alu_res'] == 0x4600
        assert out['rd'] == 13
        assert out['we'] == True
        assert out['wb_sel'] == 1
        assert out['pc4'] == 0x80004004




# ---------------------------------------
# Test MEMORY
# ---------------------------------------
class TestMEMStage:
    def test_constructor(self):
        mem = MEMStage(Memory(1024))

        # Check inputs
        in_ports = ['alu_res', 'pc4', 'we', 'wb_sel', 'rs2', 'mem', 'funct3', 'rd']
        assert len(mem.EXMEM_i.val) == len(in_ports)
        for port in in_ports:
            assert (port in mem.EXMEM_i.val)

        # Check outputs
        out_ports = ['rd', 'we', 'alu_res', 'pc4', 'mem_rdata', 'wb_sel']
        assert len(mem.MEMWB_o.val) == len(out_ports)
        for port in out_ports:
            assert (port in mem.MEMWB_o.val)
        
    def test_passThrough(self):
        mem = MEMStage(Memory(1024))
        mem.EXMEM_i.write('rd', 1,
                          'we', 1,
                          'wb_sel', 2,
                          'pc4', 0xdeadbeef,
                          'alu_res', 0xaffeaffe
                         )
        mem. process()
        assert mem.EXMEM_i['rd'].read() == 1
        assert mem.EXMEM_i['we'].read() == 1
        assert mem.EXMEM_i['wb_sel'].read() == 2
        assert mem.EXMEM_i['pc4'].read() == 0xdeadbeef
        assert mem.EXMEM_i['alu_res'].read() == 0xaffeaffe

    def test_load(self):
        mem = MEMStage(Memory(1024))
        # Load memory
        mem.mem.write(0, 0xdeadbeef, 4)
        mem.mem.write(4, 0xbade0123, 4)

        # LB
        mem.EXMEM_i.write('mem', 1) # load
        mem.EXMEM_i.write('alu_res', 2) # addr
        mem.EXMEM_i.write('funct3', 0) # lb
        mem.process()
        assert mem.MEMWB_o['mem_rdata'].read() == 0xffffffad

        mem.EXMEM_i.write('mem', 1) # load
        mem.EXMEM_i.write('alu_res', 5) # addr
        mem.EXMEM_i.write('funct3', 0) # lb
        mem.process()
        assert mem.MEMWB_o['mem_rdata'].read() == 0x00000001 

        # LH
        mem.EXMEM_i.write('mem', 1) # load
        mem.EXMEM_i.write('alu_res', 2) # addr
        mem.EXMEM_i.write('funct3', 1) # lh
        mem.process()
        assert mem.MEMWB_o['mem_rdata'].read() == 0xffffdead

        mem.EXMEM_i.write('mem', 1) # load
        mem.EXMEM_i.write('alu_res', 4) # addr
        mem.EXMEM_i.write('funct3', 1) # lh
        mem.process()
        assert mem.MEMWB_o['mem_rdata'].read() == 0x00000123 

        # LW
        mem.EXMEM_i.write('mem', 1) # load
        mem.EXMEM_i.write('alu_res', 0) # addr
        mem.EXMEM_i.write('funct3', 2) # lw
        mem.process()
        assert mem.MEMWB_o['mem_rdata'].read() == 0xdeadbeef

        # LBU
        mem.EXMEM_i.write('mem', 1) # load
        mem.EXMEM_i.write('alu_res', 2) # addr
        mem.EXMEM_i.write('funct3', 4) # lbu
        mem.process()
        assert mem.MEMWB_o['mem_rdata'].read() == 0xad

        # LHU
        mem.EXMEM_i.write('mem', 1) # load
        mem.EXMEM_i.write('alu_res', 2) # addr
        mem.EXMEM_i.write('funct3', 5) # lbu
        mem.process()
        assert mem.MEMWB_o['mem_rdata'].read() == 0xdead

    def test_store(self):
        mem = MEMStage(Memory(1024))

        # SB
        mem.EXMEM_i.write('mem', 2) # store
        mem.EXMEM_i.write('alu_res', 3) # addr
        mem.EXMEM_i.write('rs2', 0xabadbabe) # wdata
        mem.EXMEM_i.write('funct3', 0) # sb
        mem.process()
        assert mem.mem.read(3, 1) == 0xbe

        mem.mem.write(0, 0, 4)

        # SH
        mem.EXMEM_i.write('mem', 2) # store
        mem.EXMEM_i.write('alu_res', 0) # addr
        mem.EXMEM_i.write('rs2', 0xabadbabe) # wdata
        mem.EXMEM_i.write('funct3', 1) # sh
        mem.process()
        assert mem.mem.read(0, 2) == 0xbabe

        # SW
        mem.EXMEM_i.write('mem', 2) # store
        mem.EXMEM_i.write('alu_res', 0) # addr
        mem.EXMEM_i.write('rs2', 0xabadbabe) # wdata
        mem.EXMEM_i.write('funct3', 2) # sw
        mem.process()
        assert mem.mem.read(0, 4) == 0xabadbabe

# ---------------------------------------
# Test WRITE-BACK
# ---------------------------------------
class TestWBStage:
    def test_constructor(self):
        regf = Regfile()
        wb = WBStage(regf)

        in_ports = ['rd', 'we', 'alu_res', 'pc4', 'mem_rdata', 'wb_sel']
        assert len(wb.MEMWB_i.val) == len(in_ports)
        for port in in_ports:
            assert (port in wb.MEMWB_i.val)

    def test_wb(self):
        wb = WBStage(Regfile())

        # ALU op
        wb.MEMWB_i.write('rd', 18,
                         'we', 1,
                         'alu_res', 42,
                         'pc4', 87,
                         'mem_rdata', 0xdeadbeef,
                         'wb_sel', 0
                        )
        wb.process()
        assert wb.regfile.read(18) == 42

        # PC+4 (JAL)
        wb.MEMWB_i.write('rd', 31,
                         'we', 1,
                         'alu_res', 42,
                         'pc4', 87,
                         'mem_rdata', 0xdeadbeef,
                         'wb_sel', 1
                        )
        wb.process()
        assert wb.regfile.read(31) == 87

        # Memory load
        wb.MEMWB_i.write('rd', 4,
                         'we', 1,
                         'alu_res', 42,
                         'pc4', 87,
                         'mem_rdata', 0xdeadbeef,
                         'wb_sel', 2
                        )
        wb.process()
        assert wb.regfile.read(4) == 0xdeadbeef

    def test_no_wb(self):
        wb = WBStage(Regfile())

        wb.regfile.write(25, 1234)
        wb.MEMWB_i.write('we', 0,
                         'rd', 25,
                         'alu_res', 24,
                         'pc4', 25,
                         'mem_rdata', 26
                        )

        # ALU op
        wb.MEMWB_i.write('wb_sel', 0)
        wb.process()
        assert wb.regfile.read(25) == 1234

        # PC+4 (JAL)
        wb.MEMWB_i.write('wb_sel', 1)
        wb.process()
        assert wb.regfile.read(25) == 1234

        # Memory load
        wb.MEMWB_i.write('wb_sel', 2)
        wb.process()
        assert wb.regfile.read(25) == 1234

# ---------------------------------------
# Test Branch Unit
# ---------------------------------------
def test_branch_unit():
    bu = BranchUnit()

    # Test constructor
    in_ports = ['pc', 'take_branch', 'target']
    out_ports = ['npc']

    # Test regular PC increment
    bu.pc_i.write(0x80000000)
    bu.take_branch_i.write(0)
    bu.target_i.write(0x40000000)
    bu.process()
    assert bu.npc_o.read() == 0x80000004 

    # Test taken branch
    bu.pc_i.write(0x80000000)
    bu.take_branch_i.write(1)
    bu.target_i.write(0x40000000)
    bu.process()
    assert bu.npc_o.read() == 0x40000000