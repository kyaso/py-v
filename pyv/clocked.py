class Clock:
    """This class represents the clock.

    For now, clocked elements are:
    - Registers
    - Memories
    """

    def __init__(self):
        pass

    @staticmethod
    def tick():
        """Performs a clock tick (rising edge).

        Applies tick to all registers (`RegBase.tick()`) and memories (`MemBase.tick()`).
        """
        RegBase.tick()
        MemBase.tick()

    @staticmethod
    def reset():
        """Resets registers (`RegBase.reset()`) and memories (`MemBase.reset()`)."""
        RegBase.reset()
        MemBase.reset()

    @staticmethod
    def clear():
        """Clears list of registers (`RegBase.clear()`) and memories (`MemBase.clear()`)."""
        RegBase.clear()
        MemBase.clear()


class Clocked():
    """Base class for all clocked elements (Registers, Memories).

    Raises:
        NotImplementedError: The clocked element did not implement `_tick()`
        NotImplementedError: The clocked element did not implement `_reset()`
    """
    def _tick(self):
        """Tick function of individual clocked element."""
        raise NotImplementedError

    def _reset(self):
        """Reset function of individual clocked element."""
        raise NotImplementedError


class RegBase(Clocked):
    """Base class for registers.

    This class keeps track of all instantiated registers.

    Raises:
        NotImplementedError: The register did not implement `_prepareNextVal()`
    """

    # The list of instantiated registers
    _reg_list = []

    def __init__(self, resetVal):
        self.name = 'noName'

        # Add register to register list
        self._reg_list.append(self)

        self._nextv = 0
        self._resetVal = resetVal

        # Whether to do a reset on the next tick
        self._doReset = False

    @staticmethod
    def tick():
        """Ticks all registers.

        First, their next values are saved (-> `_prepareNextVal()`).

        Then the next values are propagated to the current values.
        """
        for r in RegBase._reg_list:
            r._prepareNextVal()
        
        for r in RegBase._reg_list:
            r._tick()
    
    @staticmethod
    def reset():
        """Resets all registers."""
        for r in RegBase._reg_list:
            r._reset()
    
    @staticmethod
    def clear():
        """Clears the list of registers."""
        RegBase._reg_list = []

    def _prepareNextVal(self):
        """Copies the next value to an internal variable.

        This method is required to prevent the next val input from being
        overridden after the _propagateNextVal() of a potentially preceding register
        has been called.
        """
        raise NotImplementedError

class MemBase(Clocked):
    """Base class for all memories.

    This class keeps track of all memories.

    Raises:
        NotImplementedError: The memory did not implement `read()`
        NotImplementedError: The memory did not implement `writeRequest()`
    """

    # List of instantiated memories
    _mem_list = []

    def __init__(self):
        # Add to list of memories
        MemBase._mem_list.append(self)
        # Disable write by default
        self.we = False
        """Write enable."""
        # Read enable
        self.re = False
        """Read enable"""
    
    @staticmethod
    def tick():
        """Ticks all memories."""
        for m in MemBase._mem_list:
            m._tick()
    
    @staticmethod
    def reset():
        """Resets all memories."""
        for m in MemBase._mem_list:
            m._reset()

    @staticmethod
    def clear():
        """Clears list of memories."""
        MemBase._mem_list = []
    
    def read(self):
        """Read memory."""
        raise NotImplementedError
    
    def writeRequest(self):
        """Generate a write request.
        
        The write will be committed with the next `tick()`.
        (Unless `we` is False)
        """
        raise NotImplementedError