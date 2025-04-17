from collections import deque
from unittest.mock import MagicMock
import pytest
from pyv.port import Constant, Input, Output, PortList, Wire
from pyv.module import Module
from pyv.simulator import Simulator


class TestPort:
    def test_init(self):
        A = Input(int)
        assert type(A._val) is int
        assert A._val == 0
        assert A._process_method_handler._process_methods == []

        A = Output(float)
        assert type(A._val) is float
        assert A._val == 0

    def test_read(self):
        A = Input(int)
        A._val = 42
        assert A.read() == 42

    def test_write(self):
        A = Input(int)
        A.write(123)
        assert A._val == 123

    def test_root_driver(self):
        # Chain A->B
        A = Input(int)
        B = Input(int)
        B.connect(A)

        assert A._root_driver == A
        assert B._root_driver == A

        # Chain C->D->E
        C = Input(int)
        D = Input(int)
        E = Input(int)
        D.connect(C)
        E.connect(D)
        assert C._root_driver == C
        assert D._root_driver == C
        assert E._root_driver == C

        # Now do A-B->C-D-E
        C.connect(B)
        assert C._root_driver == A
        assert D._root_driver == A
        assert E._root_driver == A

        # Write something to A
        A.write(42)
        assert A.read() == 42
        assert B.read() == 42
        assert C.read() == 42
        assert D.read() == 42
        assert E.read() == 42

    def test_root_driver_downstream_inputs(self):
        #        ┌── B(I)
        #  A(I) ─┤
        #        └── C(O)
        A = Input(int)
        B = Input(int)
        C = Output(int)

        B.connect(A)
        C.connect(A)

        assert A._downstream_inputs == [B]
        assert B._downstream_inputs == []
        assert C._downstream_inputs == []

        #       ┌── E(I)
        # D(O) ─┤
        #       └── F(O) ── G(I)
        D = Output(int)
        E = Input(int)
        F = Output(int)
        G = Input(int)

        E.connect(D)
        F.connect(D)
        G.connect(F)

        assert D._downstream_inputs == [E, G]

        # Connect D to B
        #                        ┌── E(I)
        #      ┌── B(I) ── D(O) ─┤
        # A(I)─┤                 └── F(O) ── G(I)
        #      └── C(O)
        D.connect(B)
        assert D._downstream_inputs == []
        assert A._downstream_inputs == [B, E, G]

    def test_connect(self):
        A = Input(int)
        B = Input(int)
        C = Input(int)
        D = Input(int)
        B.connect(A)
        C.connect(B)
        D.connect(B)

        # Check children
        assert A._children == [B]
        assert B._children == [C, D]
        assert C._children == []
        assert D._children == []

        # Check parents
        assert A._parent is None
        assert B._parent == A
        assert C._parent == B
        assert D._parent == B

        # Check root driver attribute
        assert A._root_driver == A
        assert B._root_driver == A
        assert C._root_driver == A
        assert D._root_driver == A

        # Write to A
        A.write(410)
        assert B.read() == 410
        assert C.read() == 410
        assert D.read() == 410

        # Test reverse connect order
        A = Input(int)
        B = Input(int)
        C = Input(int)
        C.connect(B)
        B.connect(A)
        assert A._children == [B]
        assert B._children == [C]
        A.write(420)
        assert B.read() == 420
        assert C.read() == 420

    def test_connect_shortcut(self):
        A = Input(int)
        B = Input(int)
        connect = A.connect = MagicMock()
        A << B
        connect.assert_called_once_with(B)

    def test_wire(self):
        A = Input(int)
        B = Input(int)
        C = Input(int)
        D = Input(int)
        W = Wire(int)

        # Connect wire W to port A
        W.connect(A)

        # The other ports are connected to wire W
        B.connect(W)
        C.connect(W)
        D.connect(W)

        # Write a value to A
        A.write(42)
        # Read the other ports
        assert B.read() == 42
        assert C.read() == 42
        assert D.read() == 42

    def test_errors(self):
        A = Input(int)

        # Connecting a port to two parents
        B = Input(int)
        C = Input(int)
        A.connect(B)
        with pytest.raises(Exception):
            A.connect(C)

        # Non-root port calls write
        with pytest.raises(Exception):
            A.write(42)

        # Wrong type write
        D = Input(float)
        with pytest.raises(TypeError):
            D.write("hello")

        # Connect port to itself
        with pytest.raises(Exception):
            D.connect(D)

        # Invalid driver type
        with pytest.raises(Exception):
            D.connect("foo")

    def test_connect_wrong_type(self):
        A = Input(int)
        B = Input(float)

        with pytest.raises(Exception):
            B.connect(A)

    def test_default_val(self, sim):
        # This tests checks whether the forced propagation on the
        # very first write works.
        class modA(Module):
            def __init__(self):
                super().__init__()
                self.pi = Input(int)  # Default value: 0
                self.po = Output(int)

            def process(self):
                # Simply add 3 to the input
                self.po.write(self.pi.read() + 3)

        # Initialize module
        A = modA()
        A.name = 'A'
        A._init()

        # Write 0. The port has the same default value.
        # However, since this is the first write, the
        # propagation should be forced.
        A.pi.write(0)
        sim.step()
        assert A.po.read() == 3

        # Now, we write the same value again, but this time
        # the process method shouldn't have been called.
        A.process = MagicMock()
        A.pi.write(0)
        sim.step()
        A.process.assert_not_called()

    def test_readOutput(self):
        p = Output(int)
        p.write(4)
        assert p.read() == 4

    def test_sensitive_methods(self, caplog):
        def foo():
            pass

        def bar():
            pass

        # (also don't allow any duplicates)
        p = Input(int, sensitive_methods=[foo, bar, bar])
        assert p._process_method_handler._process_methods == [foo, bar]

    def test_sensitive_methods_get_added_to_simq_on_init(self, sim):
        def foo():
            pass

        def bar():
            pass

        p = Input(int, sensitive_methods=[foo, bar])
        p._init(parent=None)
        assert sim._change_queue == deque([foo, bar])

    def test_basic_change(self, sim):
        def foo():
            pass

        def bar():
            pass

        p = Input(int, sensitive_methods=[foo, bar])

        p.write(42)
        assert sim._change_queue == deque([foo, bar])

    def test_downstream_change(self, sim: Simulator):
        def fooA(): pass
        def fooB(): pass
        def fooE(): pass
        def fooG(): pass
        #                        ┌── E(I)
        #      ┌── B(I) ── D(O) ─┤
        # A(I)─┤                 └── F(O) ── G(I)
        #      └── C(O)
        A = Input(int, [fooA])
        B = Input(int, [fooB])
        C = Output(int)

        B.connect(A)
        C.connect(A)

        D = Output(int)
        E = Input(int, [fooE])
        F = Output(int)
        G = Input(int, [fooG])

        E.connect(D)
        F.connect(D)
        G.connect(F)

        D.connect(B)

        A.write(42)
        assert sim._change_queue == deque([fooA, fooB, fooE, fooG])

    def test_constant(self):
        c = Constant(42)
        assert c._val == 42
        assert c._type == int

        assert c.read() == 42

        p = Input(int)
        p.connect(c)
        assert p.read() == 42

    def test_visited(self):
        A = Input(int)
        B = Output(int)
        mod = Module()

        assert A._visited == False
        assert B._visited == False

        A._init(mod)
        B._init(mod)

        assert A._visited == True
        assert B._visited == True


class TestPortList:
    def test_port_list(self):
        PortList.clear()
        A = Input(int)
        B = Input(int)
        C = Output(int)
        D = Wire(int)
        E = Constant(5)

        assert PortList.port_list == [A, B, C, D, E]

        PortList.clear()
        assert PortList.port_list == []

    def test_filter(self):
        PortList.clear()
        A = Input(int)
        A.name = 'top.mod1.A'
        B = Input(int)
        B.name = 'top.mod1.B'
        C = Output(int)
        C.name = 'top.mod2.C'
        D = Wire(int)
        D.name = 'top.mod2.D'
        E = Constant(5)
        E.name = 'top.mod2.sub1.E'

        PortList.filter([
            'top.mod1'
        ])
        assert PortList.port_list_filtered == [A, B]

        PortList.port_list_filtered = []
        PortList.filter([
            'mod2'
        ])
        assert PortList.port_list_filtered == [C, D, E]

        PortList.port_list_filtered = []
        PortList.filter([
            'mod1.A', 'sub1'
        ])
        assert PortList.port_list_filtered == [A, E]

        PortList.port_list_filtered = []
        PortList.filter([
            'mod1.A', 'mod1.A', 'sub1'
        ])
        assert PortList.port_list_filtered == [A, E]

        PortList.clear()
        assert PortList.port_list_filtered == []

    def test_log_ports(self):
        PortList.clear()
        A = Input(int)
        A.name = 'top.mod1.A'
        A.read = MagicMock()

        B = Input(int)
        B.name = 'top.mod1.B'
        B.read = MagicMock()

        C = Output(int)
        C.name = 'top.mod2.C'
        C.read = MagicMock()

        D = Wire(int)
        D.name = 'top.mod2.D'
        D.read = MagicMock()

        E = Constant(5)
        E.name = 'top.mod2.sub1.E'
        E.read = MagicMock()

        # First, test logging all ports
        PortList.log_ports()
        assert A.read.call_count == 1
        assert B.read.call_count == 1
        assert C.read.call_count == 1
        assert D.read.call_count == 1
        assert E.read.call_count == 1

        # Now, filter some ports
        PortList.port_list_filtered = []
        PortList.filter([
            'mod2'
        ])
        PortList.log_ports()
        assert A.read.call_count == 1
        assert B.read.call_count == 1
        assert C.read.call_count == 2
        assert D.read.call_count == 2
        assert E.read.call_count == 2
