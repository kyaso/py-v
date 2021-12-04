import pytest
from pyv.reg import RegBase

def clear_reg_list():
    """Removes all registers."""
    RegBase.reg_list = []