import pytest
from pyv.simulator import Simulator

@pytest.fixture
def sim():
    return Simulator()
