import pytest
from pyv.module import Module
from pyv.port import Port
from pyv.simulator import Simulator
from pyv.defines import *
from pyv.reg import Reg, RegBase
from pyv.clocked import Clock
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
        self.inB = Port(IN, self)
        self.outA = Port(OUT, self)
    
    def process(self):
        self.outA.write(self.inA.read() + self.inB.read())

class ExampleTop(Module):
    def __init__(self):
        super().__init__()

        self.inA = Port(IN, self)
        self.inB = Port(IN, self)
        self.out = Port(OUT, self)

        self.A_i = A()
        self.B1_i = B()
        self.B2_i = B()
        self.C_i = C()

        self.B1_i.inA.connect(self.A_i.outA)
        self.B2_i.inA.connect(self.A_i.outB)
        self.C_i.inA.connect(self.B1_i.outA)
        self.C_i.inB.connect(self.B2_i.outA)

        self.out.connect(self.C_i.outA)
        self.A_i.inA.connect(self.inA)
        self.A_i.inB.connect(self.inB) 

    def process(self):
        pass

#####
class Mul(B):
    def __init__(self, fac):
        super().__init__()
        self.fac = fac
    
    def process(self):
        self.outA.write(self.inA.read() * self.fac)

class Add(B):
    def __init__(self, add):
        super().__init__()
        self.add = add
    
    def process(self):
        self.outA.write(self.inA.read() + self.add)

class ExampleTop2(Module):
    def __init__(self):
        super().__init__()

        self.out = Port(IN, self)

        self.reg1 = Reg(42)
        self.reg2 = Reg(0)

        self.A_i = Mul(2)
        self.B_i = Add(10)
        self.C_i = Add(-5)
        self.D_i = Mul(5)

        self.reg1.next.connect(self.D_i.outA)
        self.A_i.inA.connect(self.reg1.cur)
        self.B_i.inA.connect(self.A_i.outA)
        self.reg2.next.connect(self.B_i.outA)
        self.C_i.inA.connect(self.reg2.cur)
        self.D_i.inA.connect(self.C_i.outA)

        self.out.connect(self.D_i.outA)

    def process(self):
        pass


def test_init():
    sim = Simulator()

    assert sim._queue == deque([])
    assert sim._cycles == 0
    assert Simulator.globalSim == sim

def test_queue():
    Clock.clear()

    dut = ExampleTop()
    dut.name = 'ExampleTop'
    dut.init()
    sim = Simulator()
    Clock.reset()

    dut.inA.write(42)
    dut.inB.write(43)
    assert sim._queue == deque([ dut.process, dut.A_i.process ])

    fn = sim._queue.popleft()
    fn()
    assert sim._queue == deque([ dut.A_i.process ])

    fn = sim._queue.popleft()
    fn()
    assert sim._queue == deque([ dut.B1_i.process, dut.B2_i.process ])

    fn = sim._queue.popleft()
    fn()
    assert sim._queue == deque([ dut.B2_i.process, dut.C_i.process ])

    fn = sim._queue.popleft()
    fn()
    assert sim._queue == deque([ dut.C_i.process ])

    fn = sim._queue.popleft()
    fn()
    assert sim._queue == deque([])
    assert dut.out.read() == 42+43

def test_run():
    Clock.clear()

    sim = Simulator()
    dut = ExampleTop2()
    dut.name = 'ExampleTop2'
    dut.init()
    Clock.reset()

    #sim.run(3)
    #assert dut.out.read() == -225

    sim.run(1, False)
    assert dut.out.read() == -25

    sim.run(1, False)
    assert dut.out.read() == 445

    sim.run(1, False)
    assert dut.out.read() == -225

    sim.run(1, False)
    assert dut.out.read() == 4475

    assert sim.getCycles() == 4