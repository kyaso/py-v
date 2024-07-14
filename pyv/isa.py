"""ISA definitions.

"""

# Note: Least-significant 2 bits of opcode ignored here, as they are always
# '11'
OPCODES = {
    "LOAD": 0x00,
    "OP-IMM": 0x04,
    "AUIPC": 0x05,
    "STORE": 0x08,
    "OP": 0x0C,
    "LUI": 0x0D,
    "BRANCH": 0x18,
    "JALR": 0x19,
    "JAL": 0x1B,
    "SYSTEM": 0x1C
}

# --------------------------------
# Instruction formats
# --------------------------------

INST_R = {
    OPCODES["OP"]
}

INST_I = {
    OPCODES["LOAD"],
    OPCODES["OP-IMM"],
    OPCODES["JALR"]
}

INST_S = {
    OPCODES["STORE"]
}

INST_B = {
    OPCODES["BRANCH"]
}

INST_U = {
    OPCODES["AUIPC"],
    OPCODES["LUI"]
}

INST_J = {
    OPCODES["JAL"]
}

# Instructions that write back into the register file
# REG_OPS = [
#     OPCODES["LOAD"],
#     OPCODES["OP-IMM"],
#     OPCODES["AUIPC"],
#     OPCODES["OP"],
#     OPCODES["LUI"],
#     OPCODES["JALR"],
#     OPCODES["JAL"]
# ]
REG_OPS = set.union(INST_R, INST_I, INST_U, INST_J)

# --------------------------------
# Registers
# --------------------------------
I_REGS = {
    "x0": 0, "x1": 1, "x2": 2, "x3": 3,
    "x4": 4, "x5": 5, "x6": 6, "x7": 7,
    "x8": 8, "x9": 9, "x10": 10, "x11": 11,
    "x12": 12, "x13": 13, "x14": 14, "x15": 15,
    "x16": 16, "x17": 17, "x18": 18, "x19": 19,
    "x20": 20, "x21": 21, "x22": 22, "x23": 23,
    "x24": 24, "x25": 25, "x26": 26, "x27": 27,
    "x28": 28, "x29": 29, "x30": 30, "x31": 31,
}


# --------------------------------
# Exceptions
# --------------------------------

class IllegalInstructionException(Exception):
    def __init__(self, pc, inst):
        msg = f"Illegal instruction @ PC = 0x{pc:08X} detected: '0x{inst:08x}'"
        super().__init__(msg)


# --------------------------------
# Ziscr
# --------------------------------
CSR_F3 = {
    "CSRRW": 0b001,
    "CSRRS": 0b010,
    "CSRRC": 0b011,
    "CSRRWI": 0b101,
    "CSRRSI": 0b110,
    "CSRRCI": 0b111
}


# --------------------------------
# Control and Status Registers (CSR)
# --------------------------------
CSR = {
    "misa": {
        "addr": 0x301
    },
    "mtvec": {
        "addr": 0x305,
        "read_mask": 0xFFFF_FFF1
    },
    "mepc": {
        "addr": 0x341,
        "read_mask": 0xFFFF_FFFE
    },
    "mcause": {
        "addr": 0x342
    },
}
