from pyv.port import Input, Output
from pyv.module import Module
from pyv.simulator import Simulator


# Modules are defined by inheriting from the Module class
class NOT(Module):
    def __init__(self):
        # Always call the Module constructor
        super().__init__()
        # Define input and output ports
        self.A_i = Input(bool)
        self.B_o = Output(bool)

    # The process method will be triggered whenever an input value changes
    def process(self):
        # Read input
        a = self.A_i.read()

        # Perform the NOT operation
        b = not a

        # Write the result to the output port
        self.B_o.write(b)


# Modules are defined by inheriting from the Module class
class AND(Module):
    def __init__(self):
        # Always call the Module constructor
        super().__init__()
        # Define input and output ports
        self.A_i = Input(bool)
        self.B_i = Input(bool)
        self.C_o = Output(bool)

    # The process method will be triggered whenever an input value changes
    def process(self):
        # Read inputs
        a = self.A_i.read()
        b = self.B_i.read()

        # Perform the AND operation
        c = a & b

        # Write the result to the output port
        self.C_o.write(c)


###############################################################################

# Create a simulator instance
sim = Simulator()
# Create an instance of the AND gate module
and_gate = AND()
# Create an instance of the NOT gate module
not_gate = NOT()
# Add the gates to the simulator
sim.addObj(and_gate)
sim.addObj(not_gate)
# Initialize the simulator
sim.init()

# Set inputs
and_gate.A_i.write(True)
and_gate.B_i.write(False)
not_gate.A_i.write(True)
# Run combinatorial logic
sim.run_comb_logic()
# Read output
output_and = and_gate.C_o.read()
output_not = not_gate.B_o.read()

print(f"AND Gate Output: {output_and}")  # Should print: AND Gate Output: False
print(f"NOT Gate Output: {output_not}")  # Should print: NOT Gate Output: False

# Change inputs to AND gate
and_gate.B_i.write(True) # Note that A_i remains True
# Run combinatorial logic again
sim.run_comb_logic()
# Read output again
output = and_gate.C_o.read()
print(f"AND Gate Output: {output}")  # Should print: AND Gate Output: True

# Now, let's build a NAND gate using the NOT and AND gates
class NAND(Module):
    def __init__(self):
        super().__init__()
        self.A_i = Input(bool)
        self.B_i = Input(bool)
        self.C_o = Output(bool)

        # Instantiate the AND gate
        self.and_gate = AND()
        # Connect the inputs of the AND gate to the NAND gate inputs
        self.and_gate.A_i.connect(self.A_i)
        self.and_gate.B_i.connect(self.B_i)

        # Instantiate the NOT gate
        self.not_gate = NOT()
        # Connect the output of the AND gate to the NOT gate input
        # Note that the << operator can be used for connecting ports as well.
        # It is equivalent to the connect method, check the documentation for
        # more details.
        self.not_gate.A_i << self.and_gate.C_o

        # Connect the output of the NOT gate to the NAND gate output
        self.C_o << self.not_gate.B_o

    # We don't need to define a process() method here because the
    # NOT and AND gates will handle the logic for us.
    # Whenever the inputs of the NAND gate change, those changes will propagate
    # to the AND gate, thus triggering its process method.


# Create an instance of the NAND gate
nand_gate = NAND()
# Add the NAND gate to the simulator
sim.addObj(nand_gate)
# Initialize the simulator again
sim.init()
# Set inputs for the NAND gate
nand_gate.A_i.write(True)
nand_gate.B_i.write(True)
# Run combinatorial logic for the NAND gate
sim.run_comb_logic()
# Read output for the NAND gate
output_nand = nand_gate.C_o.read()
print(f"NAND Gate Output: {output_nand}")  # Should print: NAND Gate Output: False
# Change inputs for the NAND gate
nand_gate.B_i.write(False)  # Note that A_i remains True
# Run combinatorial logic again for the NAND gate
sim.run_comb_logic()
# Read output again for the NAND gate
output_nand = nand_gate.C_o.read()
print(f"NAND Gate Output: {output_nand}")  # Should print: NAND Gate Output: True
