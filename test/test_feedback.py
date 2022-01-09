from pyv.module import Module
from pyv.port import Port
from pyv.defines import IN, OUT
from pyv.simulator import Simulator

class A(Module):
    def __init__(self):
        self.IN = Port(IN, self)
        self.OUT = Port(OUT, self)
    
    def process(self):
        self.OUT.write(self.IN.read() * 2)

class B(Module):
    def __init__(self):
        self.IN1 = Port(IN, self)
        self.IN2 = Port(IN, self)
        self.OUT1 = Port(OUT, self)
        self.OUT2 = Port(OUT, self)
    
    def process(self):
        in1 = self.IN1.read()
        in2 = self.IN2.read()

        self.OUT1.write(in1*3)
        self.OUT2.write(in2+5)

class C(Module):
    def __init__(self):
        self.IN1 = Port(IN, self)
        self.IN2 = Port(IN, self)
        self.OUT1 = Port(OUT, self)
        self.OUT2 = Port(OUT, self)

    def process(self):
        in1 = self.IN1.read()
        in2 = self.IN2.read()

        self.OUT1.write(in1*6)
        self.OUT2.write(in2*2)

class Top(Module):
    def __init__(self):
        self.IN = Port(IN, self)
        self.OUT = Port(OUT, self)

        self.A_i = A()
        self.B_i = B()
        self.C_i = C()

        self.A_i.IN.connect(self.IN)
        self.B_i.IN1.connect(self.A_i.OUT)
        self.B_i.IN2.connect(self.C_i.OUT1)
        self.C_i.IN1.connect(self.B_i.OUT1)
        self.C_i.IN2.connect(self.B_i.OUT2)
        self.OUT.connect(self.C_i.OUT2)
    
    def process(self):
        return

def test_feedback():
    dut = Top()
    dut.name = "Top"
    dut.init()
    sim = Simulator()

    dut.IN.write(4)

    sim.run(3) 

    assert dut.OUT.read() == 298