import copy
from port import *

# TODO: Maybe make abstract
class RegBase:
    """Base class for registers.

    This class keeps track of all instantiated registers.
    """

    # The list of instantiated registers
    reg_list = []

    def __init__(self):
        # Add register to register list
        self.reg_list.append(self)

    def prepareNextVal(self):
        """Copies the next value to an internal variable.

        This method is required to prevent the next val input from being
        overridden after the tick() of a potentially preceding register
        has been called.
        """

        raise Exception('RegBase: Please implement prepareNextVal().')

    def tick(self):
        """Simulates a clock tick (rising edge).

        The next val of the register becomes the new current val.
        """

        raise Exception('RegBase: Please implement tick().')

    @staticmethod
    def updateRegs():
        """Ticks all registers.

        First, their next values are saved.

        Then the next values are propagated to the current values.
        """

        for r in RegBase.reg_list:
            r.prepareNextVal()
        
        for r in RegBase.reg_list:
            r.tick()

class Reg(RegBase):
    """Represents a single value register."""

    def __init__(self, initVal = 0):
        # Add this register to the global register list
        super().__init__()

        self.next = Port()          # Next value input
        self.cur = Port()           # Current value output
        self.cur.write(initVal)
        self.nextv = 0
    
    def prepareNextVal(self):
        self.nextv = copy.deepcopy(self.next.read())

    def tick(self):
        self.cur.write(copy.deepcopy(self.nextv))

class RegX(Reg):
    """Represents a multivalue register."""

    def __init__(self, *args):
        super().__init__()

        self.next = PortX(*args)    # Next value input
        self.cur = PortX(*args)     # Current value output

class Regfile():
    """Integer register file."""

    def __init__(self):
        self.regs = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

    def read(self, reg: int) -> int:
        """Reads a register.

        Args:
            reg (int): Index of register to read.

        Returns:
            int: The value of the register.
        """

        if reg == 0:
            return 0
        else:
            return self.regs[reg]

    def write(self, reg: int, val: int):
        """Writes a value to a register.

        Args:
            reg (int): Index of register to write.
            val (int): Value to write.
        """

        if reg != 0:
            self.regs[reg] = val