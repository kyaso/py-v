from abc import ABC, abstractmethod


class Clock:
    """This class represents the clock.

    For now, clocked elements are:
    - Registers
    - Memories
    """

    @staticmethod
    def tick():
        """Performs a clock tick (rising edge).

        First, saves the current inputs (`RegList.prepare_next_val()`,
        `MemList.prepare_next_val()`). Then, applies tick to all registers
        (`RegList.tick()`) and memories (`MemList.tick()`).
        """
        RegList.prepare_next_val()
        MemList.prepare_next_val()
        RegList.tick()
        MemList.tick()

    @staticmethod
    def reset():
        """Resets registers (`RegList.reset()`) and memories
        (`MemList.reset()`).
        """
        RegList.reset()
        MemList.reset()

    @staticmethod
    def clear():
        """Clears list of registers (`RegList.clear()`) and memories
        (`MemList.clear()`).
        """
        RegList.clear()
        MemList.clear()


class Clocked(ABC):
    """Base class for all clocked elements.

    Methods `_prepare_next_val()`, `_tick()`, and `_reset()` must be
    implemented by any class inheriting.
    """
    @abstractmethod
    def _prepare_next_val(self):
        """Saves current input(s)"""

    @abstractmethod
    def _tick(self):
        """Tick function of individual clocked element."""

    @abstractmethod
    def _reset(self):
        """Reset function of individual clocked element."""


class RegList():
    """This class keeps track of all instantiated registers.
    """

    # The list of instantiated registers
    _reg_list = []

    @staticmethod
    def add_to_reg_list(obj):
        """Adds a register object to the global list of registers.

        Args:
            obj: The register object
        """
        RegList._reg_list.append(obj)

    @staticmethod
    def prepare_next_val():
        """Saves inputs of registers"""
        for r in RegList._reg_list:
            r._prepare_next_val()

    @staticmethod
    def tick():
        """Ticks all registers."""
        for r in RegList._reg_list:
            r._tick()

    @staticmethod
    def reset():
        """Resets all registers."""
        for r in RegList._reg_list:
            r._reset()

    @staticmethod
    def clear():
        """Clears the list of registers."""
        RegList._reg_list = []


class MemList():
    """Base class for all memories.

    This class keeps track of all memories.
    """

    # List of instantiated memories
    _mem_list = []

    @staticmethod
    def add_to_mem_list(obj):
        """Add memory to global list of memories.

        Args:
            obj: The memory object.
        """
        MemList._mem_list.append(obj)

    @staticmethod
    def prepare_next_val():
        """Saves inputs of memories."""
        for m in MemList._mem_list:
            m._prepare_next_val()

    @staticmethod
    def tick():
        """Ticks all memories."""
        for m in MemList._mem_list:
            m._tick()

    @staticmethod
    def reset():
        """Resets all memories."""
        for m in MemList._mem_list:
            m._reset()

    @staticmethod
    def clear():
        """Clears list of memories."""
        MemList._mem_list = []
