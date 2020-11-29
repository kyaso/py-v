import util

class Core:
    def __init__(self):
        pass

    def i_ADD(self, val1, val2):
        """ ADD[I] instruction

        Parameters:
            val1: Value of register rs1
            val2: rs2 / Sign-extended immediate
        
        Returns:
            Sum of val1 and val2
        """

        return (val1 + val2)
    
    def i_SUB(self, val1, val2):
        """ SUB instruction

        Parameters:
            val1: Value of register rs1
            val2: rs2
        
        Returns:
            Sub of val1 and val2
        """
        
        # We mask here so that Python returns the 2s complement value
        return (0xffffffff & (val1 - val2))

    def i_SLT(self, val1, val2):
        """ SLT[I] instruction

        Parameters:
            val1: Value of register rs1
            val2: rs2 / Sign-extended immediate
        
        Returns:
            1 if val1 < val2 (signed comparison)
            0 otherwise
        """

        msb_r = util.msb_32(val1)
        msb_i = util.msb_32(val2)

        # Check if both operands are positive
        if (msb_r==0) and (msb_i==0):
            if val1 < val2:
                return 1
            else:
                return 0
        # val1 negative; val2 positive
        elif (msb_r==1) and (msb_i==0):
            return 1
        # val1 positive, val2 negative
        elif (msb_r==0) and (msb_i==1):
            return 0
        # both negative
        else:
            if val2 < val1:
                return 1
            else:
                return 0

    def i_SLTU(self, val1, val2):
        """ SLT[I]U instruction

        Parameters:
            val1: Value of register rs1
            val2: rs2 / Sign-extended immediate
        
        Returns:
            1 if val1 < val2 (unsigned comparison)
            0 otherwise
        """

        if val1 < val2:
            return 1
        else:
            return 0
    
    def i_AND(self, val1, val2):
        """ AND[I] instruction

        Parameters:
            val1: Value of register rs1
            val2: rs2 / Sign-extended immediate
        
        Returns:
            Bitwise AND of val1 and val2 (val1 & val2)
        """

        return (val1 & val2)

    def i_OR(self, val1, val2):
        """ OR[I] instruction

        Parameters:
            val1: Value of register rs1
            val2: rs2 / Sign-extended immediate
        
        Returns:
            Bitwise OR of val1 and val2 (val1 | val2)
        """

        return (val1 | val2)

    def i_XOR(self, val1, val2):
        """ XOR[I] instruction

        Parameters:
            val1: Value of register rs1
            val2: rs2 / Sign-extended immediate
        
        Returns:
            Bitwise XOR of val1 and val2 (val1 ^ val2)
        """

        return (val1 ^ val2)
    
    def i_SLL(self, val1, val2):
        """ SLL[I] instruction

        Parameters:
            val1: Value of register rs1
            val2: rs2 / Sign-extended immediate
        
        Returns:
            Logical left shift of val1 by val2 (5 bits)
        """

        return (util.MASK_32 & (val1<<(0x1f&val2))) # Mask so that bits above bit 31 turn to zero (for Python)

    def i_SRL(self, val1, val2):
        """ SRL[I] instruction

        Parameters:
            val1: Value of register rs1
            val2: rs2 / Sign-extended immediate
        
        Returns:
            Logical right shift of val1 by val2 (5 bits)
        """

        return (util.MASK_32 & (val1>>(0x1f&val2))) # Mask so that bits above bit 31 turn to zero (for Python)

    def i_SRA(self, val1, val2):
        """ SRA[I] instruction

        Parameters:
            val1: Value of register rs1
            val2: rs2 / Sign-extended immediate
        
        Returns:
            Arithmetic right shift of val1 by val2 (5 bits)
        """

        msb_r = util.msb_32(val1)
        shamt = 0x1f & val2
        rshift = (util.MASK_32 & (val1>>shamt)) # Mask so that bits above bit 31 turn to zero (for Python)
        if msb_r==0:
            return rshift 
        else:
            # Fill upper bits with 1s
            return (util.MASK_32 & (rshift | (0xffffffff<<(util.XLEN-shamt)))) 
            
    def i_LUI(self, imm):
        """LUI instruction

        Parameters:
            imm:    Sign-extended immediate

        Returns:
            imm + 12 lower bits zeroes
        """

        return (util.MASK_32 & (imm<<12))

    def i_AUIPC(self, pc, imm):
        """AUIPC instruction

        Parameters:
            pc:     Current PC
            imm:    Sign-extended immediate
        
        Returns:
            Upper-immediate + PC
        """
        
        upper_imm = (util.MASK_32 & (imm<<12))
        return (util.MASK_32 & (pc + imm))
            