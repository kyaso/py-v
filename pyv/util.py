"""Utility stuff."""

# XLEN
XLEN = 32

# 32 bit mask
MASK_32 = 0xffffffff

def msb_32(val) -> int:
    """Returns the MSB of a 32 bit value."""

    return (val & 0x80000000)>>31

def getBit(val, idx: int) -> int:
    """Gets a bit."""

    return 1&(val>>idx)

def getBits(val, hiIdx: int, loIdx: int) -> int:
    """Returns a bit slice of a value.

    Args:
        val: Original value.
        hiIdx: Upper (high) index of slice.
        loIdx: Lower index of slice.

    Returns:
        The bit slice.
    """

    return (~(MASK_32<<(hiIdx-loIdx+1)) & (val>>loIdx))

def signext(val, width: int):
    """Sign-extends a value (`val`) of width `width` bits to 32-bits."""

    msb = getBit(val, width-1)

    if msb: #1
        val = MASK_32&( (-1)<<width | val )

    return val

def getBitVector(val: int):
    """Convert a number into a list with its binary representation.

    The list is assumed to be in "MSB-at-index-0" ordering.

    Args:
        val (int): The value that we want to express as a binary list.
    """
    return [1 if digit=='1' else 0 for digit in bin(val)[2:]]

def bitVector2num(bitVec: list):
    """Convert a bit list to a number.

    The list is assumed to be in "MSB-at-index-0" ordering.

    Args:
        bitVec (list): The bit list that we want to convert to a number.
    """
    bitStr = ''.join(str(b)  for b in bitVec)
    return int(bitStr, 2)