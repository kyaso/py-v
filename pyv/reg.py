import copy
import warnings
from pyv.port import Port
from pyv.util import bitVector2num, getBitVector
from pyv.defines import IN, OUT
from pyv.clocked import MemBase, RegBase
import pyv.log as log
from typing import TypeVar, Generic, Type

T = TypeVar('T')

logger = log.getLogger(__name__)

class Reg(RegBase, Generic[T]):
    """Represents a single value register."""

    def __init__(self, type: Type[T], resetVal = 0):
        """Create a new register.

        Args:
            resetVal (int, optional): Reset value. Defaults to 0.
        """
        # Add this register to the global register list
        super().__init__(resetVal)

        self.next = Port(type, IN)          # Next value input
        self.cur = Port(type, OUT)          # Current value output
        self.rst = Port(int, IN)           # Synchronous Reset in (active high)

    def _prepareNextVal(self):
        self._doReset = False

        if self.rst.read() == 1:
            self._doReset = True
        elif self.rst.read() == 0:
            self.nextv = copy.deepcopy(self.next.read())
        else:
            raise Exception("Error: Invalid rst signal!")

    def _tick(self):
        if self._doReset:
            logger.debug(f"Sync reset on register {self.name}. Reset value: {self.resetVal}.")
            self._reset()
        else:
            self.cur.write(self.nextv)

    def _reset(self):
        self.cur.write(self.resetVal)


class ShiftReg(RegBase):
    """Represents a single-valued shift register.

    For optimization reasons, the lists operate from right to left.
    """

    def __init__(self, depth, resetVal = 0):
        # Add this register to the global register list
        super().__init__(resetVal)

        self.depth = depth

        self.serIn = Port(int, IN)          # Serial input
        self.serOut = Port(int, OUT)         # Serial output
        self.rst = Port(int, IN)          # Synchronous reset (active high)

        # Initialize shift register
        self._reset()
        #self.regs = [initVal  for _ in range(0, depth)]

    def _reset(self):
        self.regs = [self.resetVal  for _ in range(0, self.depth)]
        self.updateSerOut()

    def _prepareNextVal(self):
        self._doReset = False

        if self.rst.read() == 1:
            self._doReset = True
        elif self.rst.read() == 0:
            self.nextv = self.serIn.read()
            if self.nextv.bit_length() > 1:
                warnings.warn("ShiftReg serial input value ({}) is wider than 1 bit. Truncating to 1 bit.".format(self.nextv))
                self.nextv = self.nextv & 1

    def _tick(self):
        """Shift elements. Or reset.

        TODO: formulate this better
        For optimization reasons the list is right to left
        """

        if self._doReset:
            logger.debug(f"Sync reset on shift register {self.name}. Reset value: {self.resetVal}.")
            self.regs = [self.resetVal  for _ in range(0, self.depth)]
        else:
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

        self.parEnable = Port(int, IN)
        self.parIn = Port(int, IN)
        self.parOut = Port(int, OUT)
        self.depth = depth
        self.parInNext = 0
        self.parMask = 2**self.depth - 1

    def _prepareNextVal(self):
        self._doReset = False

        if self.rst.read() == 1:
            self._doReset = True
            return

        if not self.parEnable.read():
            super()._prepareNextVal()
        else:
            self.parInNext = self.parIn.read()

    def _tick(self):
        if self._doReset:
            super()._tick()
            self.updateParOut()
        else:
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
            # During the processing of the current cycle, it might occur that
            # an unstable port value is used as the index. However, the port
            # will eventually become stable, so we should "allow" that access
            # by just returning a dummy value, e.g., 0.
            #
            # Note: this exception should never be caused by a running program,
            # because the decoder will only feed-in valid 5 bit indeces.
            try:
                val = self.regs[reg]
            except IndexError:
                logger.warn("Potentially illegal register index 0x{:08X}. This might be normal during cycle processing.".format(reg))
                val = 0

            return val

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
            self.we = True

    def _tick(self):
        """Register file tick.

        Commits a write request (when `we` is set). 
        """
        if not self.we:
            return

        self.regs[self._nextWidx] = self._nextWval

        # TODO: Technically, it shouldn't be the regfile's responsibility to reset
        # the write enables. But we leave it now for safety.
        self.we = False

    def _reset(self):
        """Resets the register file."""
        self.regs = [0  for _ in range(0, 32)]
        # TODO: Similar story as above in _tick(): These signals are driven by external
        # modules, so it's actually not the memories responsibility to reset them.
        # We still do for additional simulation safety.
        self.we = False