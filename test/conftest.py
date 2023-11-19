import pytest
from pyv.clocked import Clock
from pyv.simulator import Simulator

@pytest.fixture(autouse=True)
def clear_clock():
    yield
    Clock.clear()

@pytest.fixture
def sim() -> Simulator:
    return Simulator()
