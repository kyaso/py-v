from pyv.util import MASK_32
import pyv.log as log
from pyv.clocked import MemBase

logger = log.getLogger(__name__)

# TODO: Check if addr is valid
class Memory(MemBase):
    """Simple memory.

    A memory is represented by a simple list of bytes.

    Byte-ordering: Little-endian
    """

    def __init__(self, size: int = 32):
        """Memory constructor.

        Args:
            size: Size of memory in bytes.
        """
        super().__init__()
        self.mem = [ 0 for i in range(0,size) ]
        """Memory array. List of length `size`."""

        # For tick
        self._nextWaddr = 0
        self._nextWval = 0
        self._nextWwidth = 0
        self._lastAddr = 0 # TODO: redundant with _nextWaddr?

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
        # TODO: handle illegal address

        self.re = True
        self._lastAddr = addr
        # During the processing of the current cycle, it might occur that
        # an unstable port value is used as the address. However, the port
        # will eventually become stable, so we should "allow" that access
        # by just returning a dummy value, e.g., 0.
        #
        # Note: An actual illegal address exception caused by a running
        # program should be handled synchronously, i.e. with the next
        # active clock edge (tick).
        try:
            if w == 1: # byte
                val = MASK_32 & self.mem[addr]
            elif w == 2: # half word
                val = MASK_32 & (self.mem[addr+1]<<8 | self.mem[addr])
            elif w == 4: # word
                val = MASK_32 & (self.mem[addr+3]<<24 | self.mem[addr+2]<<16 | self.mem[addr+1]<<8 | self.mem[addr])
            else:
                raise Exception('ERROR (Memory, read): Invalid width {}'.format(w))
            
            logger.debug("MEM: read value 0x{:08X} from address 0x{:08X}".format(val, addr))
            return val
        except IndexError:
            logger.warn("Potentially illegal memory address 0x{:08X}. This might be normal during cycle processing.".format(addr))
            return 0
    
    def writeRequest(self, addr: int, val: int, w: int):
        """Generate a write request to write data to memory.

        The write is committed with the next `_tick()`.

        Args:
            addr: Starting address for write operation.
            val: Value to write.
            w: Number of bytes to write.
                Accepted values: 1, 2, 4

        Raises:
            Exception: `w` is not from {1,2,4}.
        """

        # TODO: handle misaligned access

        # Set write enable to True, so the write is committed
        # in the next `_tick()`.
        self.we = True
        self._nextWaddr = addr
        self._nextWval = val

        if w == 1 or w == 2 or w == 4:
            self._nextWwidth = w
        else:
            raise Exception('ERROR (Memory, write): Invalid width {}'.format(w)) 

    def _tick(self):
        """Memory tick.

        Commits a write request (when `we` is set).
        """
        # TODO: Check for illegal address
        if (self.re and self._lastAddr == -1) or (self.we and self._nextWaddr == -1):
            pass

        if self.we:
            val = self._nextWval
            w = self._nextWwidth
            addr = self._nextWaddr

            logger.debug("MEM: write 0x{:08X} to address 0x{:08X}".format(val, addr))

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

        # TODO: Technically, it shouldn't be the regfile's responsibility to reset
        # the write and read enables. But we leave it now for safety.
        self.we = False
        self.re = False
    
    # TODO: when memory gets loaded with program *before* simulation, simulation start
    # will cause a reset. So for now, we skip the reset here.
    def _reset(self):
        return
        """Reset memory.

        All elements are set to 0.
        """
        for i in range(0, len(self.mem)):
            self.mem[i] = 0