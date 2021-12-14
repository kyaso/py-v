import pytest
from test.fixtures import clear_reg_list
from serial.ser_adder import SerAdder
from util import getBitVector

def test_ser_adder():
    clear_reg_list()

    dut = SerAdder()

    depth = 8

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

                # Carry reset is supposed to stay active for one cycle.
                # So we pull it down to 0 after the dut.process().
                dut.C_rst_i.write(0)

                # Verify emitted sum bit
                assert dut.S_o.read() == sum_exp[i]
            
            # We have added all bits: Reset carry
            dut.C_rst_i.write(1)