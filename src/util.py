# XLEN
XLEN = 32

# 32 bit mask
MASK_32 = 0xffffffff

def msb_32(val) -> int:
    return (val & 0x80000000)>>31

def getBit(val, idx: int) -> int:
    return 1&(val>>idx)

def getBits(val, hiIdx: int, loIdx: int) -> int:
    return (~(MASK_32<<(hiIdx-loIdx+1)) & (val>>loIdx))

def signext(val, width: int):
    msb = getBit(val, width-1)

    if msb: #1
        val = MASK_32&( (-1)<<width | val )

    return val