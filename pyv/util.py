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