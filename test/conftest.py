import pytest
from pyv.simulator import Simulator


@pytest.fixture(autouse=True)
def clear_sim():
    yield
    Simulator.clear()
    Simulator.globalSim = None


@pytest.fixture(autouse=True)
def sim() -> Simulator:
    return Simulator()
