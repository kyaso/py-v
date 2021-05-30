from util import MASK_32
class Memory:
    """Simple memory.

    A memory is represented by a simple list of bytes.

    Byte-ordering: Little-endian
    """

    def __init__(self, size: int = 32):
        """Memory constructor.

        Args:
            size: Size of memory in bytes.
        """

        self.mem = [ 0xff for i in range(0,size) ]

    def read(self, addr: int, w: int) -> int:
        """Reads data from memory.

        Args:
            addr: Starting address to read from.
            w: Number of bytes to read.
                Accepted values: 1, 2, 4
        
        Returns:
            A single word containing the read bytes.

        Raises:
            Exception: `w` is not from {1,2,4}.
        """
        # TODO: handle misaligned access
        if w == 1: # byte
            return MASK_32 & self.mem[addr]
        elif w == 2: # half word
            return MASK_32 & (self.mem[addr+1]<<8 | self.mem[addr])
        elif w == 4: # word
            return MASK_32 & (self.mem[addr+3]<<24 | self.mem[addr+2]<<16 | self.mem[addr+1]<<8 | self.mem[addr])
        else:
            raise Exception('ERROR (Memory, read): Invalid width {}'.format(w))
    
    def write(self, addr: int, val: int, w: int):
        """Writes data to memory.

        Args:
            addr: Starting address for write operation.
            val: Value to write.
            w: Number of bytes to write.
                Accepted values: 1, 2, 4

        Raises:
            Exception: `w` is not from {1,2,4}.
        """

        # TODO: handle misaligned access
        if w == 1: # byte
            self.mem[addr] = 0xff & val
        elif w == 2: # half word
            self.mem[addr] = 0xff & val
            self.mem[addr+1] = (0xff00 & val)>>8
        elif w == 4: # word
            self.mem[addr] = 0xff & val
            self.mem[addr+1] = (0xff00 & val)>>8 
            self.mem[addr+2] = (0xff0000 & val)>>16
            self.mem[addr+3] = (0xff000000 & val)>>24
        else:
            raise Exception('ERROR (Memory, write): Invalid width {}'.format(w))