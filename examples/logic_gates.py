from pyv.port import Input, Output
from pyv.module import Module
from pyv.simulator import Simulator

# Modules are defined by inheriting from the Module class
class AND(Module):
    def __init__(self, name):
        # Always call the Module constructor
        super().__init__(name)
        # Define input and output ports
        self.A_i = Input(bool)
        self.B_i = Input(bool)
        self.C_o = Output(bool)

    # The process method will be triggered when input values change
    def process(self):
        # Read inputs
        a = self.A_i.read()
        b = self.B_i.read()

        # Perform the AND operation
        c = a & b

        # Write the result to the output port
        self.C_o.write(c)

# Create a simulator instance
sim = Simulator()
# Create an instance of the AND gate module
and_gate = AND("and_gate")
# Add the AND gate to the simulator
sim.addObj(and_gate)
# Initialize the simulator
sim.init()

# Set inputs
and_gate.A_i.write(True)
and_gate.B_i.write(False)
# Run combinatorial logic
sim.run_comb_logic()
# Read output
output = and_gate.C_o.read()
print(f"AND Gate Output: {output}")  # Should print: AND Gate Output: False

# Change inputs
and_gate.B_i.write(True) # Note that A_i remains True
# Run combinatorial logic again
sim.run_comb_logic()
# Read output again
output = and_gate.C_o.read()
print(f"AND Gate Output: {output}")  # Should print: AND Gate Output: True
