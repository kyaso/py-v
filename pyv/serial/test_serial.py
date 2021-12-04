import pytest
from reg import RegBase
from test.fixtures import clear_reg_list
from serial.ser_adder import SerAdder
from util import getBitVector

def test_ser_adder_depth():
    clear_reg_list()

    dut = SerAdder(2)
    dut = SerAdder(4)
    dut = SerAdder(8)
    dut = SerAdder(16)
    dut = SerAdder(32)
    dut = SerAdder(64)

    with pytest.raises(Exception):
        dut = SerAdder(9)

def test_ser_adder():
    clear_reg_list()

    depth = 8
    dut = SerAdder(depth)

    assert dut.depth == depth

    # Test all possible input values
    for a in range(0, 2**depth):
        # Convert a to bit vector
        a_vec = getBitVector(a, depth)
        for b in range(0, 2**depth):
            # Convert b to bit vector
            b_vec = getBitVector(b, depth)
            # Calculate sum bit vector
            sum_exp = getBitVector(a+b, depth)

        # Feed bits of a and b to Adder
        # Note: LSB first
        for i in reversed(range(0, depth)):
            dut.A_i.write(a_vec[i])
            dut.B_i.write(b_vec[i])

            # Cycle
            dut.process()
            RegBase.updateRegs()

            # Verify emitted sum bit
            assert dut.S_o.read() == sum_exp[i]