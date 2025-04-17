from pyv.module import Module
from pyv.port import Input, Output
from pyv.util import MASK_32, PyVObj
from pyv.log import logger
from pyv.clocked import Clocked, MemList


class ReadPort(PyVObj):
    """Read port"""
    def __init__(
        self,
        re_i: Input[bool],
        width_i: Input[int],
        addr_i: Input[int],
        rdata_o: Output[int]
    ):
        super().__init__(name='UnnamedReadPort')

        self.re_i = re_i
        """Read-enable input"""
        self.width_i = width_i
        """Data width input (1, 2, or 4)"""
        self.addr_i = addr_i
        """Address input (also for write)"""
        self.rdata_o = rdata_o
        """Read port 0 Read data output"""


class WritePort(PyVObj):
    """Write port"""
    def __init__(
        self,
        we_i: Input[bool],
        wdata_i: Input[int]
    ):
        super().__init__(name='UnnamedWritePort')

        self.we_i = we_i
        """Write-enable input"""
        self.wdata_i = wdata_i
        """Write data input"""

# TODO: Check if addr is valid


class Memory(Module, Clocked):
    """Simple memory module with 2 read ports and 1 write port

    A memory is represented by a simple list of bytes.

    Byte-ordering: Little-endian
    """

    def __init__(self, size: int = 32):
        """Memory constructor.

        Args:
            size: Size of memory in bytes.
        """
        super().__init__(name='UnnamedMemory')
        MemList.add_to_mem_list(self)
        self.mem = [0 for i in range(0, size)]
        """Memory array. List of length `size`."""

        # Read port 0
        self.read_port0 = ReadPort(
            re_i=Input(bool, [self.process_read0]),
            width_i=Input(int, [self.process_read0]),
            addr_i=Input(int, [self.process_read0]),
            rdata_o=Output(int)
        )

        # Read port 1
        self.read_port1 = ReadPort(
            re_i=Input(bool, [self.process_read1]),
            width_i=Input(int, [self.process_read1]),
            addr_i=Input(int, [self.process_read1]),
            rdata_o=Output(int)
        )

        # Write port (uses addr, width from read port 0)
        self.write_port = WritePort(
            we_i=Input(bool, [None]),
            wdata_i=Input(int, [None])
        )

    def _read(self, addr, w):
        # During the processing of the current cycle, it might occur that
        # an unstable port value is used as the address. However, the port
        # will eventually become stable, so we should "allow" that access
        # by just returning a dummy value, e.g., 0.
        #
        # Note: An actual illegal address exception caused by a running
        # program should be handled synchronously, i.e. with the next
        # active clock edge (tick).
        try:
            if w == 1:  # byte
                val = MASK_32 & self.mem[addr]
            elif w == 2:  # half word
                val = MASK_32 & (self.mem[addr + 1] << 8 | self.mem[addr])
            elif w == 4:  # word
                val = MASK_32 & (
                    self.mem[addr + 3] << 24
                    | self.mem[addr + 2] << 16
                    | self.mem[addr + 1] << 8
                    | self.mem[addr])
            else:
                raise Exception(
                    f'ERROR (Memory ({self.name}), read): Invalid width {w}')

            logger.debug(f"MEM ({self.name}): read value {val:08X} from address {addr:08X}")  # noqa: E501
        except IndexError:
            val = 0

        return val

    def _process_read(self, read_port):
        re = read_port.re_i.read()
        addr = read_port.addr_i.read()
        w = read_port.width_i.read()

        if re:
            val = self._read(addr, w)
        else:
            val = 0

        read_port.rdata_o.write(val)

    def process_read0(self):
        self._process_read(self.read_port0)

    def process_read1(self):
        self._process_read(self.read_port1)

    def _prepare_next_val(self):
        # We need this also in Memory, because it could happen that these pins
        # are driven by registers, so we save the values first before the
        # registers tick.
        self.we_next = self.write_port.we_i.read()
        self.addr_next = self.read_port0.addr_i.read()
        self.wdata_next = self.write_port.wdata_i.read()
        self.w_next = self.read_port0.width_i.read()

    def _tick(self):
        we = self.we_next
        addr = self.addr_next
        wdata = self.wdata_next
        w = self.w_next

        if we:
            if not (w == 1 or w == 2 or w == 4):
                raise Exception(
                    f'ERROR (Memory ({self.name}), write): Invalid width {w}')
            logger.debug(
                f"MEM {self.name}: write {wdata:08X} to address {addr:08X}")

            if w == 1:  # byte
                self.mem[addr] = 0xff & wdata
            elif w == 2:  # half word
                self.mem[addr] = 0xff & wdata
                self.mem[addr + 1] = (0xff00 & wdata) >> 8
            elif w == 4:  # word
                self.mem[addr] = 0xff & wdata
                self.mem[addr + 1] = (0xff00 & wdata) >> 8
                self.mem[addr + 2] = (0xff0000 & wdata) >> 16
                self.mem[addr + 3] = (0xff000000 & wdata) >> 24

    # TODO: when memory gets loaded with program *before* simulation,
    # simulation start will cause a reset. So for now, we skip the reset here.
    def _reset(self):
        return
        """Reset memory.

        All elements are set to 0.
        """
        for i in range(0, len(self.mem)):
            self.mem[i] = 0
