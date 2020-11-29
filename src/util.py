# XLEN
XLEN = 32

# 32 bit mask
MASK_32 = 0xffffffff

def msb_32(val):
    """
    Return the MSB of a 32 bit value
    """
    return (val & 0x80000000)>>31