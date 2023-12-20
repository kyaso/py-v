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
    "JAL": 0x1B
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
# Exceptions
# --------------------------------

class IllegalInstructionException(Exception):
    def __init__(self, pc, inst):
        msg = f"Illegal instruction @ PC = 0x{pc:08X} detected: '0x{inst:08x}'"
        super().__init__(msg)
