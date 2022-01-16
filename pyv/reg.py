import copy
import warnings
from pyv.port import *
from pyv.util import bitVector2num, getBitVector
from pyv.defines import IN, OUT
from pyv.clocked import MemBase, RegBase

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
    
    def _reset(self):
        self.cur.write(self.resetVal)

class RegX(Reg):
    """Represents a multivalue register."""

    def __init__(self, *args):
        super().__init__()

        self.next = PortX(IN, None, *args)    # Next value input
        self.cur = PortX(OUT, None, *args)     # Current value output
    
    def _reset(self):
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
        self._reset()
        #self.regs = [initVal  for _ in range(0, depth)]

        # Write output
        self.updateSerOut()
    
    def _reset(self):
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


class Regfile(MemBase):
    """RISC-V: Integer register file."""

    def __init__(self):
        super().__init__()
        self.regs = [0  for _ in range(0, 32)]
        self._nextWIdx = 0
        self._nextWval = 0

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

    def writeRequest(self, reg: int, val: int):
        """Writes a value to a register.

        The write is committed with the next _tick().

        Args:
            reg (int): Index of register to write.
            val (int): Value to write.
        """
        if reg != 0:
            # self.regs[reg] = val
            self._nextWidx = reg
            self._nextWval = val
            self._we = True
    
    def _tick(self):
        """Register file tick.

        Commits a write request (when `_we` is set). 
        """
        if not self._we:
            return

        self.regs[self._nextWidx] = self._nextWval

        # TODO: Technically, it shouldn't be the regfile's responsibility to reset
        # the write enable after a write. But we leave it now for safety.
        self._we = False

    def _reset(self):
        """Resets the register file."""
        self.regs = [0  for _ in range(0, 32)]
        self._we = False