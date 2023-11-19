from abc import ABC, abstractmethod


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


class Clocked(ABC):
    """Base class for all clocked elements (Registers, Memories).

    Methods `_tick()` and `_reset()` must be implemented by any class
    inheriting.
    """
    @abstractmethod
    def _tick(self):
        """Tick function of individual clocked element."""

    @abstractmethod
    def _reset(self):
        """Reset function of individual clocked element."""


class RegBase():
    """Base class for registers.

    This class keeps track of all instantiated registers.

    Raises:
        NotImplementedError: The register did not implement `_prepareNextVal()`
    """

    # The list of instantiated registers
    _reg_list = []

    def __init__(self):
        self.name = 'noName'

        # Add register to register list
        RegBase.add_to_reg_list(self)

    @staticmethod
    def add_to_reg_list(obj):
        RegBase._reg_list.append(obj)


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

class MemBase():
    """Base class for all memories.

    This class keeps track of all memories.
    """

    # List of instantiated memories
    _mem_list = []

    def __init__(self):
        # Add to list of memories
        MemBase.add_to_mem_list(self)

    @staticmethod
    def add_to_mem_list(obj):
        MemBase._mem_list.append(obj)

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
