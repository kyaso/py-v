import pytest
from pyv.port import Input, Output
from pyv.module import Module
from pyv.simulator import Simulator


class ModA(Module):
    def __init__(self, name):
        super().__init__(name)
        self.A_i = Input(int)
        self.A_o = Output(int)

        self.B_i = Input(int, [None])
        self.C_i = Input(int, [self.foo])

    def foo(self):
        pass

    def process(self):
        pass


class ModB(Module):
    def __init__(self, name):
        super().__init__(name)
        self.A_i = Input(int)


@pytest.fixture
def modA() -> Module:
    return ModA('ModA')


@pytest.fixture
def modB() -> Module:
    return ModB('ModB')


class TestModule:
    def test_init(self, modA: ModA):
        assert modA.name == 'ModA'

    def test_port_init(self, modA: ModA):
        modA._init()
        assert modA.A_i._process_method_handler._process_methods == [modA.process]
        assert modA.B_i._process_method_handler._process_methods == []
        assert modA.C_i._process_method_handler._process_methods == [modA.foo]

    def test_port_init_without_process_method(self, modB: ModB):
        modB._init()
        assert modB.A_i._process_method_handler._process_methods == []


class TestOnStable:
    class DummyModule(Module):
        def __init__(self, name='UnnamedModule'):
            super().__init__(name)
            self.register_stable_callbacks([self.stable_callback_1, self.stable_callback_2])

        def stable_callback_1(self):
            pass

        def stable_callback_2(self):
            pass

    def test_stable_callbacks_are_registered_in_module(self):
        dut = self.DummyModule()
        assert dut.stable_callback_1 in dut._stable_callbacks
        assert dut.stable_callback_2 in dut._stable_callbacks

    def test_stable_callbacks_are_added_to_sim_on_init(self, sim: Simulator):
        dut = self.DummyModule()
        dut._init()
        assert dut.stable_callback_1 in sim._stable_callbacks
        assert dut.stable_callback_2 in sim._stable_callbacks
