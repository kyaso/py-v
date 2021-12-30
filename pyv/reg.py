import copy
import warnings
from pyv.port import *
from pyv.util import bitVector2num, getBitVector
from pyv.defines import IN, OUT

# TODO: Maybe make abstract
class RegBase:
    """Base class for registers.

    This class keeps track of all instantiated registers.
    """

    # The list of instantiated registers
    reg_list = []

    def __init__(self, resetVal):
        # Add register to register list
        self.reg_list.append(self)

        self.nextv = 0
        self.resetVal = resetVal

    def _prepareNextVal(self):
        """Copies the next value to an internal variable.

        This method is required to prevent the next val input from being
        overridden after the _tick() of a potentially preceding register
        has been called.
        """

        raise Exception('RegBase: Please implement _prepareNextVal().')

    def _tick(self):
        """Simulates a clock _tick (rising edge).

        The next val of the register becomes the new current val.
        """

        raise Exception('RegBase: Please implement _tick().')
    
    @staticmethod
    def _updateRegs():
        """_ticks all registers.

        First, their next values are saved.

        Then the next values are propagated to the current values.
        """

        for r in RegBase.reg_list:
            r._prepareNextVal()
        
        for r in RegBase.reg_list:
            r._tick()
    
    @staticmethod
    def reset():
        """Reset all registers."""

        for r in RegBase.reg_list:
            r.reset()
    
    @staticmethod
    def _clearRegList():
        """Clear the list of registers."""

        RegBase.reg_list = []

class Reg(RegBase):
    """Represents a single value register."""

    def __init__(self, resetVal = 0):
        # Add this register to the global register list
        super().__init__(resetVal)

        self.next = Port(IN)          # Next value input
        self.cur = Port(OUT)           # Current value output
    
    def _prepareNextVal(self):
        self.nextv = self.next.read()

    def _tick(self):
        self.cur.write(self.nextv)
    
    def reset(self):
        self.cur.write(self.resetVal)

class RegX(Reg):
    """Represents a multivalue register."""

    def __init__(self, *args):
        super().__init__()

        self.next = PortX(IN, None, *args)    # Next value input
        self.cur = PortX(OUT, None, *args)     # Current value output
    
    def reset(self):
        """Reset all subports.

        For now: 0

        Args:
            resetVal: The reset value.
        """
        self.cur.write(0)

class ShiftReg(RegBase):
    """Represents a single-valued shift register.
    
    For optimization reasons, the lists operate from right to left.
    """

    def __init__(self, depth, resetVal = 0):
        # Add this register to the global register list
        super().__init__(resetVal)

        self.depth = depth

        self.serIn = Port()          # Serial input
        self.serOut = Port()         # Serial output

        # Initialize shift register
        self.reset()
        #self.regs = [initVal  for _ in range(0, depth)]

        # Write output
        self.updateSerOut()
    
    def reset(self):
        self.regs = [self.resetVal  for _ in range(0, self.depth)] 

    def _prepareNextVal(self):
        self.nextv = self.serIn.read()
        if self.nextv.bit_length() > 1:
            warnings.warn("ShiftReg serial input value ({}) is wider than 1 bit. Truncating to 1 bit.".format(self.nextv))
            self.nextv = self.nextv & 1

    def _tick(self):
        """Shift elements.

        TODO: formulate this better
        For optimization reasons the list is right to left
        """

        # Fetch the new value
        self.regs.append(self.nextv)

        # Perform shift
        # We move the list elements left by one
        self.regs = self.regs[1:]

        # Update output
        self.updateSerOut()

    def updateSerOut(self):
        """Updates the output value of the shift register."""

        # Last register value is visible at the output.
        # This is index 0 of the register list
        self.serOut.write(self.regs[0])

class ShiftRegParallel(ShiftReg):
    def __init__(self, depth, resetVal = 0):
        super().__init__(depth, resetVal)

        self.parEnable = Port()
        self.parIn = Port()
        self.parOut = Port()
        self.depth = depth
        self.parInNext = 0
        self.parMask = 2**self.depth - 1
    
    def _prepareNextVal(self):
        if not self.parEnable.read():
            super()._prepareNextVal()
        else:
            self.parInNext = self.parIn.read()

    def _tick(self):
        if not self.parEnable.read():
            super()._tick()
            self.updateParOut()
        else:
            # Check whether the input is not wider as our depth
            # If it is, we issue a warning and only take the lower `depth` bit
            if self.parInNext.bit_length() > self.depth:
                warnings.warn("ShiftRegParallel: Parallel input value is wider than register depth. Register has depth {}, value is {}".format(self.depth, self.parInNext))
                self.parInNext = self.parInNext & self.parMask
            self.regs = getBitVector(self.parInNext, self.depth)
            self.updateSerOut()
            self.updateParOut()
    
    def updateParOut(self):
        self.parOut.write(bitVector2num(self.regs))


class Regfile():
    """RISC-V: Integer register file."""

    def __init__(self):
        self.regs = [0  for _ in range(0, 32)]

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
    
    def reset(self):
        """Reset the register file."""

        self.regs = [0  for _ in range(0, 32)]