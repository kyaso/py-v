.globl main
main:
lui x5, 1
li x2, 1000
li x1, 0
loop:
addi x1, x1, 1
bne x1, x2, loop
sw x1, 0(x5)
end:
j end
