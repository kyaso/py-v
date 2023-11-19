import copy
import warnings
from pyv.port import Input, Output
from pyv.util import PyVObj, bitVector2num, getBitVector
from pyv.clocked import Clocked, MemBase, RegBase
import pyv.log as log
from typing import TypeVar, Generic, Type

T = TypeVar('T')

_logger = log.getLogger(__name__)

class Reg(PyVObj, Clocked, Generic[T]):
    """Represents a register."""

    def __init__(self, type: Type[T], resetVal: T = 0):
        """Create a new register.

        Args:
            resetVal (int, optional): Reset value. Defaults to 0.
        """
        super().__init__()

        # Add this register to the global register list
        RegBase.add_to_reg_list(self)

        self.next: Input = Input(type, [None])
        """Next value input"""
        self.cur: Output = Output(type)
        """Current value output"""
        self.rst: Input = Input(int, [None])
        """Synchronous Reset in (active high)"""

        self._nextv = 0
        self._resetVal = resetVal

        # Whether to do a reset on the next tick
        self._doReset = False

    def _prepareNextVal(self):
        """Copies the next value to an internal variable.

        This method is required to prevent the next val input from being
        overridden after the _propagateNextVal() of a potentially preceding register
        has been called.
        """
        self._doReset = False
        self._doTick = False

        if self.rst.read() == 1:
            self._doReset = True
        elif self.rst.read() == 0:
            if self.cur.read() != self.next.read():
                self._nextv = copy.deepcopy(self.next.read())
                self._doTick = True
        else:
            raise Exception("Error: Invalid rst signal!")

    def _tick(self):
        if self._doReset:
            _logger.debug(f"Sync reset on register {self.name}. Reset value: {self._resetVal}.")
            self._reset()
        elif self._doTick:
            self.cur.write(self._nextv)

    def _reset(self):
        self.cur.write(self._resetVal)


class ShiftReg(RegBase):
    """Represents a single-valued shift register.

    For optimization reasons, the lists operate from right to left.
    """

    def __init__(self, depth, resetVal = 0):
        # Add this register to the global register list
        super().__init__(resetVal)

        self.depth = depth

        self.serIn = Input(int)          # Serial input
        self.serOut = Output(int)         # Serial output
        self.rst = Input(int)          # Synchronous reset (active high)

        # Initialize shift register
        self._reset()
        #self.regs = [initVal  for _ in range(0, depth)]

    def _reset(self):
        self.regs = [self._resetVal  for _ in range(0, self.depth)]
        self.updateSerOut()

    def _prepareNextVal(self):
        self._doReset = False

        if self.rst.read() == 1:
            self._doReset = True
        elif self.rst.read() == 0:
            self._nextv = self.serIn.read()
            if self._nextv.bit_length() > 1:
                warnings.warn("ShiftReg serial input value ({}) is wider than 1 bit. Truncating to 1 bit.".format(self._nextv))
                self._nextv = self._nextv & 1

    def _tick(self):
        """Shift elements. Or reset.

        TODO: formulate this better
        For optimization reasons the list is right to left
        """

        if self._doReset:
            _logger.debug(f"Sync reset on shift register {self.name}. Reset value: {self._resetVal}.")
            self.regs = [self._resetVal  for _ in range(0, self.depth)]
        else:
            # Fetch the new value
            self.regs.append(self._nextv)

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

        self.parEnable = Input(int)
        self.parIn = Input(int)
        self.parOut = Output(int)
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


class Regfile(Clocked):
    """RISC-V: Integer register file."""

    def __init__(self):
        MemBase.add_to_mem_list(self)
        self.regs = [0  for _ in range(0, 32)]
        self._nextWIdx = 0
        self._nextWval = 0
        self.we = False
        """Write enable."""
        # Read enable
        self.re = False
        """Read enable"""

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
                _logger.debug(f"Regfile READ: x{reg} = {val}")
            except IndexError:
                _logger.warn("Potentially illegal register index 0x{:08X}. This might be normal during cycle processing.".format(reg))
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

        _logger.debug(f"Regfile WRITE: x{self._nextWidx} changed from {self.regs[self._nextWidx]} to {self._nextWval}")
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