import copy
from pyv.util import PyVObj
from pyv.port import Input, Wire
from pyv.clocked import Clocked, RegList
from pyv.log import logger
from typing import TypeVar, Generic, Type

T = TypeVar('T')


class Reg(PyVObj, Clocked, Generic[T]):
    """Represents a register."""

    def __init__(self, type: Type[T], resetVal: T = 0, sensitive_methods=[]):
        """Create a new register.

        Args:
            resetVal (int, optional): Reset value. Defaults to 0.
            sensitive_methods (list, optional): List of methods to trigger when
                this register's output (current) value changes. By default, no
                sensitive methods will be assigned.
        """
        super().__init__(name='UnnamedRegister')

        # Add this register to the global register list
        RegList.add_to_reg_list(self)

        self.next: Input = Input(type, [None])
        """Next value input"""
        self.cur: Wire = Wire(type, sensitive_methods)
        """Current value output"""
        self.rst: Input = Input(int, [None])
        """Synchronous Reset in (active high)"""

        self._nextv = 0
        self._reset_val = resetVal

        # Whether to do a reset on the next tick
        self._do_reset = False

    def _prepare_next_val(self):
        """Copies the next value to an internal variable.

        This method is required to prevent the next val input from being
        overridden after the _propagateNextVal() of a potentially preceding
        register has been called.
        """
        self._do_reset = False
        self._do_tick = False

        if self.rst.read() == 1:
            self._do_reset = True
        elif self.rst.read() == 0:
            if self.cur.read() != self.next.read():
                self._nextv = copy.deepcopy(self.next.read())
                self._do_tick = True
        else:
            raise Exception("Error: Invalid rst signal!")

    def _tick(self):
        if self._do_reset:
            logger.debug(f"Sync reset on register {self.name}. Reset value: {self._reset_val}.")  # noqa: E501
            self._reset()
        elif self._do_tick:
            self.cur.write(self._nextv)

    def _reset(self):
        self.cur.write(self._reset_val)


class Regfile(Clocked):
    """RISC-V: Integer register file."""

    def __init__(self):
        RegList.add_to_reg_list(self)
        self.regs = [0] * 32
        self._next_w_idx = 0
        self._next_w_val = 0
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
                val = 0

            return val

    def write_request(self, reg: int, val: int):
        """Writes a value to a register.

        The write is committed with the next _tick().

        Args:
            reg (int): Index of register to write.
            val (int): Value to write.
        """
        if reg != 0:
            # self.regs[reg] = val
            self._next_w_idx = reg
            self._next_w_val = val
            self.we = True

    def _prepare_next_val(self):
        # Not needed for now, as we don't have Input ports here
        pass

    def _tick(self):
        """Register file tick.

        Commits a write request (when `we` is set).
        """
        if not self.we:
            return

        logger.debug(f"Regfile WRITE: x{self._next_w_idx} changed from {self.regs[self._next_w_idx]} to {self._next_w_val}")  # noqa: E501
        self.regs[self._next_w_idx] = self._next_w_val

        # TODO: Technically, it shouldn't be the regfile's responsibility to
        # reset the write enables. But we leave it now for safety.
        self.we = False

    def _reset(self):
        """Resets the register file."""
        self.regs = [0] * 32
        # TODO: Similar story as above in _tick(): These signals are driven by
        # external modules, so it's actually not the memories responsibility to
        # reset them. We still do for additional simulation safety.
        self.we = False
