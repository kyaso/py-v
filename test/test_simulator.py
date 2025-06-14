import pytest
from pyv.module import Module
from pyv.port import Input, Output, PortList, Wire
from pyv.simulator import Simulator, _EventQueue
from pyv.reg import Reg
from pyv.clocked import Clock
from collections import deque
from queue import PriorityQueue
from unittest.mock import MagicMock


@pytest.fixture
def eq() -> _EventQueue:
    return _EventQueue()


# Build a simple example circuit
class A(Module):
    def __init__(self):
        super().__init__()
        self.inA = Input(int)
        self.inB = Input(int)

        self.outA = Output(int)
        self.outB = Output(int)

    def process(self):
        self.outA.write(self.inA.read())
        self.outB.write(self.inB.read())


class B(Module):
    def __init__(self):
        super().__init__()
        self.inA = Input(int)
        self.outA = Output(int)

    def process(self):
        self.outA.write(self.inA.read())


class C(Module):
    def __init__(self):
        super().__init__()
        self.inA = Input(int)
        self.inB = Input(int)
        self.outA = Output(int)

    def process(self):
        self.outA.write(self.inA.read() + self.inB.read())


class ExampleTop(Module):
    def __init__(self):
        super().__init__()

        self.inA = Input(int)
        self.inB = Input(int)
        self.out = Output(int)

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

        self.out = Input(int)

        self.reg1 = Reg(int, 42)
        self.reg2 = Reg(int, 0)

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


class TestSimulator:
    def test_init(self, sim: Simulator):
        assert sim._change_queue == deque([])
        assert sim._cycles == 0
        assert Simulator.globalSim == sim

    def test_obj_registry(self, sim: Simulator):
        dut = ExampleTop()
        sim.addObj(dut)
        assert sim._objs == [dut]

        dut2 = ExampleTop()
        sim.addObj(dut2)
        assert sim._objs == [dut, dut2]

    def test_obj_registry_invalid_type(self, sim: Simulator):
        class InvalidObj:
            pass

        with pytest.raises(TypeError):
            sim.addObj(InvalidObj())

    def test_obj_init(self, sim: Simulator):
        dut = ExampleTop()
        dut2 = ExampleTop()
        sim.addObj(dut)
        sim.addObj(dut2)
        dut._init = MagicMock()
        dut2._init = MagicMock()
        sim.init()
        dut._init.assert_called_once()
        dut2._init.assert_called_once()

    def test_probes(self, sim: Simulator):
        dut = ExampleTop()
        dut.name = 'ExampleTop'
        dut._init()
        PortList.filter = MagicMock()
        sim.set_probes(['ExampleTop.inA', 'ExampleTop.B1_i'])
        PortList.filter.assert_called_once_with(['ExampleTop.inA', 'ExampleTop.B1_i'])

    def test_queue(self, sim: Simulator):
        dut = ExampleTop()
        dut.name = 'ExampleTop'
        dut._init()
        # Clear pre-populated process queue; we want to test it in isolation here
        sim._change_queue = deque()
        Clock.reset()

        dut.inA.write(42)
        dut.inB.write(43)
        assert sim._change_queue == deque([dut.process, dut.A_i.process])

        fn = sim._change_queue.popleft()
        fn()
        assert sim._change_queue == deque([dut.A_i.process])

        fn = sim._change_queue.popleft()
        fn()
        assert sim._change_queue == deque([dut.B1_i.process, dut.B2_i.process])

        fn = sim._change_queue.popleft()
        fn()
        assert sim._change_queue == deque([dut.B2_i.process, dut.C_i.process])

        fn = sim._change_queue.popleft()
        fn()
        assert sim._change_queue == deque([dut.C_i.process])

        fn = sim._change_queue.popleft()
        fn()
        assert sim._change_queue == deque([])
        assert dut.out.read() == 42 + 43

    def test_run(self, sim: Simulator):
        dut = ExampleTop2()
        dut.name = 'ExampleTop2'
        dut._init()

        sim._process_events = MagicMock()
        Clock.reset()

        sim.run(4)
        assert dut.out.read() == -2225

        # sim.step()
        # assert dut.out.read() == -25

        # sim.step()
        # assert dut.out.read() == 445

        # sim.step()
        # assert dut.out.read() == -225

        # sim.step()
        # assert dut.out.read() == 4475

        assert sim.get_cycles() == 4
        assert sim._process_events.call_count == 5


class TestStep:
    def test_step(self, sim: Simulator):
        pe = sim._process_events = MagicMock()
        pq = sim._process_changes = MagicMock()

        sim.step()
        assert pe.call_count == 2
        assert pq.call_count == 2
        assert sim._cycles == 1

    def test_comb_step(self, sim: Simulator):
        class Foo(Module):
            def __init__(self):
                super().__init__()
                self.A_i = Input(int)
                self.pass_o = Output(int)
                self.reg_o = Output(int)
                self.comb_o = Output(int)

                self.reg = Reg(int, 42)
                self.reg_w = Wire(int)

                self.reg.next << self.A_i
                self.pass_o << self.A_i
                self.reg_o << self.reg.cur
                self.reg_w << self.reg.cur

            def process(self):
                a = self.A_i.read()
                r = self.reg_w.read()
                sum = a + r
                self.comb_o.write(sum)

        foo = Foo()
        foo._init()
        sim.reset()

        foo.A_i.write(10)
        sim.run_comb_logic()
        assert foo.pass_o.read() == 10
        assert foo.reg_o.read() == 42
        assert foo.comb_o.read() == 52

        foo.A_i.write(20)
        # This should make sure that the process method gets executed after the
        # clock tick to get the correct output value
        sim.step()
        assert foo.pass_o.read() == 20
        assert foo.reg_o.read() == 20
        assert foo.comb_o.read() == 40


class TestEventQueue:
    def test_init(self, eq: _EventQueue):
        assert isinstance(eq._queue, PriorityQueue)

    def test_add_event(self, eq: _EventQueue):
        def callback():
            pass

        eq.add_event(101, callback)
        event = eq._queue.get(False)
        time = event[0]
        cb = event[2]
        assert time == 101
        assert cb == callback

    def test_add_events_with_same_time(self, eq: _EventQueue):
        callback1 = MagicMock()
        callback2 = MagicMock()

        eq.add_event(101, callback1)
        eq.add_event(101, callback2)

        assert len(eq._queue.queue) == 2

    def test_add_negative_time_event(self, eq: _EventQueue):
        with pytest.raises(Exception):
            eq.add_event(-1, None)

    def test_get_event(self, eq: _EventQueue):
        eq.add_event(1, None)
        eq.add_event(20, None)
        eq.add_event(3, None)

        assert eq.get_next_event()[0] == 1
        assert eq.get_next_event()[0] == 3
        assert eq.get_next_event()[0] == 20

    def test_next_event_time(self, eq: _EventQueue):
        eq.add_event(42, None)
        eq.add_event(20, None)
        eq.add_event(100, None)

        assert eq.next_event_time() == 20
        eq.get_next_event()
        assert eq.next_event_time() == 42

    def test_get_num_events(self, eq: _EventQueue):
        eq.add_event(1, None)
        eq.add_event(1, None)
        assert eq._get_num_events() == 2

        eq.add_event(1, None)
        assert eq._get_num_events() == 3

        eq.get_next_event()
        assert eq._get_num_events() == 2

    def test_empty(self, eq: _EventQueue):
        with pytest.raises(Exception):
            eq.get_next_event()


class TestEvents:
    def test_event_queue_exists(self, sim: Simulator):
        assert isinstance(sim._event_queue, _EventQueue)

    def test_add_event_absolute(self, sim: Simulator):
        def callback():
            pass
        sim._cycles = 100

        add_event = sim._event_queue.add_event = MagicMock()
        sim.post_event_abs(1024, callback)
        add_event.assert_called_once_with(1024, callback)

    def test_add_event_relative(self, sim: Simulator):
        def callback():
            pass
        sim._cycles = 100
        add_event = sim._event_queue.add_event = MagicMock()
        sim.post_event_rel(42, callback)
        add_event.assert_called_once_with(142, callback)

    def test_process_events(self, sim: Simulator):
        callback1 = MagicMock()
        callback1.__qualname__ = "cb1"  # We have to manually set this here, as MagicMock does not have this attr
        callback2 = MagicMock()
        callback2.__qualname__ = "cb2"
        callback3 = MagicMock()
        callback3.__qualname__ = "cb3"
        callback4 = MagicMock()
        callback4.__qualname__ = "cb4"

        sim.post_event_abs(5, callback1)   # event1
        sim.post_event_abs(11, callback3)  # event3
        sim.post_event_abs(10, callback2)  # event2
        sim.post_event_abs(11, callback4)  # event4

        sim._cycles = 1
        sim._process_events()
        assert sim._event_queue._get_num_events() == 4
        assert sim._event_queue.next_event_time() == 5

        sim._cycles = 5
        sim._process_events()
        callback1.assert_called_once()
        assert sim._event_queue._get_num_events() == 3
        assert sim._event_queue.next_event_time() == 10

        sim._cycles = 10
        sim._process_events()
        callback2.assert_called_once()
        assert sim._event_queue._get_num_events() == 2
        assert sim._event_queue.next_event_time() == 11

        sim._cycles = 11
        sim._process_events()
        callback3.assert_called_once()
        callback4.assert_called_once()
        assert sim._event_queue.next_event_time() == -1

    def test_invalid_event_time(self, sim: Simulator):
        sim._cycles = 10
        with pytest.raises(Exception):
            sim.post_event_abs(5, None)

        with pytest.raises(Exception):
            sim.post_event_rel(-1, None)


class TestOnStable:
    def test_stable_callbacks_are_triggered_during_cycle(self, sim: Simulator):
        cb1 = MagicMock()
        cb2 = MagicMock()
        Simulator._stable_callbacks = [cb1, cb2]
        sim._cycle()
        cb1.assert_called_once()
        cb2.assert_called_once()

    def test_stable_callbacks_are_cleared_on_sim_clear(self, sim: Simulator):
        sim.clear()
        assert Simulator._stable_callbacks == []

    def test_register_stable_callback(self, sim: Simulator):
        cb1 = MagicMock()
        cb2 = MagicMock()
        cb3 = MagicMock()
        Simulator._stable_callbacks = [cb1, cb2]
        Simulator.register_stable_callback(cb3)
        assert Simulator._stable_callbacks == [cb1, cb2, cb3]
