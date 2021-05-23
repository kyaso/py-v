from util import MASK_32
class Memory:
    def __init__(self, size = 32):
        self.mem = [ 0 for i in range(0,size) ]

    def read(self, addr, w):
        # TODO: handle misaligned access
        if w == 1: # byte
            return MASK_32 & self.mem[addr]
        elif w == 2: # half word
            return MASK_32 & (self.mem[addr+1]<<8 | self.mem[addr])
        elif w == 4: # word
            return MASK_32 & (self.mem[addr+3]<<24 | self.mem[addr+2]<<16 | self.mem[addr+1]<<8 | self.mem[addr])
        else:
            raise Exception('ERROR (Memory, read): Invalid width {}'.format(w))
    
    def write(self, addr, val, w):
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