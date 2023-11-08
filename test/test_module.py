from unittest.mock import MagicMock
import pytest
from pyv.port import Input, Output
from pyv.module import Module

class ModA(Module):
    def __init__(self):
        self.A_i = Input(int, self)
        self.A_o = Output(int, self)

@pytest.fixture
def modA() -> Module:
    return ModA()

class TestModule:
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
