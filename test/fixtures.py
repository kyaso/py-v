import pytest
from pyv.simulator import Simulator, _EventQueue

@pytest.fixture
def sim() -> Simulator:
    return Simulator()

@pytest.fixture
def eq() -> _EventQueue:
    return _EventQueue()
