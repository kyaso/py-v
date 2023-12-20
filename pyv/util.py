"""Utility stuff."""

import warnings


# TODO: Move this class to its own module
class PyVObj:
    """This class represent all Py-V objects (such as modules, ports,
    registers). Currently, this is used for initializing the names of every
    object in the design.
    """
    def __init__(self, name="noName") -> None:
        self.name = name
        """Name of this object"""
        self._visited = False

    def _init(self, parent=None):
        """Initializes the object.

        This includes the following steps:
        - Set the name of each child PyVObj instance
        - Recursively call `_init()` for each child `PyVObj` instance
        """
        if self._visited:
            return
        self._visited = True

        for key in self.__dict__:
            obj = self.__dict__[key]
            if isinstance(obj, (PyVObj)):
                obj.name = self.name + "." + key
                obj._init(self)


# XLEN
XLEN = 32

# 32 bit mask
MASK_32 = 0xffffffff


def msb_32(val) -> int:
    """Returns the MSB of a 32 bit value."""

    return (val & 0x80000000) >> 31


def getBit(val, idx: int) -> int:
    """Gets a bit."""

    return (val >> idx) & 1


def getBits(val, hiIdx: int, loIdx: int) -> int:
    """Returns a bit slice of a value.

    Args:
        val: Original value.
        hiIdx: Upper (high) index of slice.
        loIdx: Lower index of slice.

    Returns:
        The bit slice.
    """

    return (~(MASK_32 << (hiIdx - loIdx + 1)) & (val >> loIdx))


def signext(val, width: int):
    """Sign-extends a value (`val`) of width `width` bits to 32-bits."""

    msb = getBit(val, width - 1)

    if msb:  # 1
        val = MASK_32 & ((-1) << width | val)

    return val


def getBitVector(val: int, len: int = 0):
    """Convert a number into a list with its binary representation.

    The list is assumed to be in "MSB-at-index-0" ordering.

    Args:
        val (int): The value that we want to express as a binary list.
        len (int): Use this to pass a fixed length which the output vector
            should have. The bitlength of `val` must be less-than or equal to
            `len`, otherwise an exception is raised.

            A  value of 0 (default) will result in the minimum length needed to
            hold the binary representation of `val`.

    Returns:
        A list containing the bits of `val`.
    """
    if len == 0:
        return [1 if digit == '1' else 0 for digit in bin(val)[2:]]
    elif len >= val.bit_length():
        leading_zeros = [0 for _ in range(len - val.bit_length())]
        return (leading_zeros
                + [1 if digit == '1' else 0 for digit in bin(val)[2:]])
    else:
        num_trunc_bits = val.bit_length() - len
        warnings.warn(f"Util getBitVector(): Requested vector length ({len}) shorter than bit_length of value ({val.bit_length()}). Truncating upper {num_trunc_bits} bits.")  # noqa: E501
        return [
            1 if digit == '1' else 0 for digit in bin(val)[2 + num_trunc_bits:]
        ]


def bitVector2num(bitVec: list):
    """Convert a bit list to a number.

    The list is assumed to be in "MSB-at-index-0" ordering.

    Args:
        bitVec (list): The bit list that we want to convert to a number.

    Returns:
        Integer value of input bit vector.
    """
    bitStr = ''.join(str(b) for b in bitVec)
    return int(bitStr, 2)
