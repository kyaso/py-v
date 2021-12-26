import pytest
from pyv.module import Module
from pyv.port import Port
from pyv.simulator import Simulator
from pyv.defines import *
from collections import deque

# Build a simple example circuit
class A(Module):
    def __init__(self):
        self.inA = Port(IN, self)
        self.inB = Port(IN, self)

        self.outA = Port(OUT, self)
        self.outB = Port(OUT, self)
    
    def process(self):
        self.outA.write(self.inA.read())
        self.outB.write(self.inB.read())

class B(Module):
    def __init__(self):
        self.inA = Port(IN, self)
        self.outA = Port(OUT, self)
    
    def process(self):
        self.outA.write(self.inA.read())

class C(Module):
    def __init__(self):
        self.inA = Port(IN, self)
        self.outA = Port(OUT, self)
    
    def process(self):
        self.outA.write(self.inA.read())

class D(Module):
    def __init__(self):
        self.inA = Port(IN, self)
        self.inB = Port(IN, self)
        self.outA = Port(OUT, self)
    
    def process(self):
        self.outA.write(self.inA.read() + self.inB.read())

class ExampleTop(Module):
    def __init__(self):
        self.inA = Port(IN, self)
        self.inB = Port(IN, self)
        self.out = Port(OUT, self)

        self.A_i = A()
        self.B_i = B()
        self.C_i = C()
        self.D_i = D()

        self.B_i.inA.connect(self.A_i.outA)
        self.C_i.inA.connect(self.A_i.outB)
        self.D_i.inA.connect(self.B_i.outA)
        self.D_i.inB.connect(self.C_i.outA)

        self.out.connect(self.D_i.outA)
        self.A_i.inA.connect(self.inA)
        self.A_i.inB.connect(self.inB) 
    
    def process(self):
        pass

def test_init():
    sim = Simulator()

    assert sim._queue == deque([])
    assert sim._cycles == 0
    assert Simulator.globalSim == sim

def test_queue():
    dut = ExampleTop()
    sim = Simulator()

    dut.inA.write(42)
    dut.inB.write(43)
    assert sim._queue == deque([ dut.A_i.process ])

    fn = sim._queue.popleft()
    fn()
    assert sim._queue == deque([ dut.B_i.process, dut.C_i.process ])

    fn = sim._queue.popleft()
    fn()
    assert sim._queue == deque([ dut.C_i.process, dut.D_i.process ])

    fn = sim._queue.popleft()
    fn()
    assert sim._queue == deque([ dut.D_i.process ])

    fn = sim._queue.popleft()
    fn()
    assert sim._queue == deque([])
    assert dut.out.read() == 42+43
