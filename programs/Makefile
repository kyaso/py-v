RISCV=riscv64-unknown-elf-
RISCV_GCC_OPTS=-march=rv32i -mabi=ilp32 -nostdlib -nostartfiles common/crt.S

all: loop_acc fibonacci endless_loop

.PHONY: loop_acc
loop_acc: loop_acc/loop_acc.S
	$(RISCV)gcc $(RISCV_GCC_OPTS) $< -o $@/$@.out
	$(RISCV)objdump -d $@/$@.out > $@/$@.out.dmp
	$(RISCV)objcopy -O binary $@/$@.out $@/$@.bin
	hexdump $@/$@.bin > $@/$@.bin.dmp

.PHONY: fibonacci
fibonacci: fibonacci/fibonacci.c
	$(RISCV)gcc $(RISCV_GCC_OPTS) $< -o $@/$@.out
	$(RISCV)objdump -d $@/$@.out > $@/$@.out.dmp
	$(RISCV)objcopy -O binary $@/$@.out $@/$@.bin
	hexdump $@/$@.bin > $@/$@.bin.dmp

.PHONY: endless_loop
endless_loop: endless_loop/endless_loop.S
	$(RISCV)gcc $(RISCV_GCC_OPTS) $< -o $@/$@.out
	$(RISCV)objdump -d $@/$@.out > $@/$@.out.dmp
	$(RISCV)objcopy -O binary $@/$@.out $@/$@.bin
	hexdump $@/$@.bin > $@/$@.bin.dmp

.PHONY: clean
clean:
	rm -rf */*.bin */*.out */*.dmp