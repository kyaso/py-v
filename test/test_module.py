from unittest.mock import MagicMock
import pytest
from pyv.port import Input, Output
from pyv.module import Module

class ModA(Module):
    def __init__(self, name):
        super().__init__(name)
        self.A_i = Input(int)
        self.A_o = Output(int)

        self.B_i = Input(int, [None])
        self.C_i = Input(int, [self.foo])

    def foo(self):
        pass

@pytest.fixture
def modA() -> Module:
    return ModA('ModA')

class TestModule:
    def test_init(self, modA: ModA):
        assert modA.name == 'ModA'

    def test_port_connect_with_assignment_operator(self, modA: ModA):
        connect = modA.A_o.connect = MagicMock()
        modA.A_o = modA.A_i
        connect.assert_called_once_with(modA.A_i)

        # This should do default assignment
        modA.A_o = 42
        assert modA.A_o == 42
        assert connect.call_count == 1

        modA.foo = modA.A_i
        assert modA.foo == modA.A_i
        assert connect.call_count == 1

    def test_port_init(self, modA: ModA):
        modA.init()
        assert modA.A_i._processMethods == [modA.process]
        assert modA.A_o._processMethods == []
        assert modA.B_i._processMethods == []
        assert modA.C_i._processMethods == [modA.foo]
