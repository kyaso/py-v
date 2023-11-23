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

    def test_port_init(self, modA: ModA):
        modA._init()
        assert modA.A_i._processMethodHandler._processMethods == [modA.process]
        assert modA.B_i._processMethodHandler._processMethods == []
        assert modA.C_i._processMethodHandler._processMethods == [modA.foo]
