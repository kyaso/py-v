import copy
import warnings
from pyv.port import Input, Output
from pyv.util import PyVObj, bitVector2num, getBitVector
from pyv.clocked import Clocked, MemBase, RegBase
from pyv.log import logger
from typing import TypeVar, Generic, Type

T = TypeVar('T')


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
            logger.debug(f"Sync reset on register {self.name}. Reset value: {self._resetVal}.")
            self._reset()
        elif self._doTick:
            self.cur.write(self._nextv)

    def _reset(self):
        self.cur.write(self._resetVal)


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
                logger.debug(f"Regfile READ: x{reg} = {val}")
            except IndexError:
                logger.warn(f"Potentially illegal register index 0x{reg:08X}. This might be normal during cycle processing.")
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

        logger.debug(f"Regfile WRITE: x{self._nextWidx} changed from {self.regs[self._nextWidx]} to {self._nextWval}")
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