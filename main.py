import time
from pyv.models.model import Model
from pyv.models.singlecycle import SingleCycleModel

def execute_bin(core_type: str, program_name: str, path_to_bin: str, num_cycles: int) -> Model:
  print("===== "+program_name+" =====")

  # Create core instance
  print("* Creating core instance...")
  if core_type == 'single':
    core = SingleCycleModel()
  
  # Load binary into memory
  print("* Loading binary...")
  core.load_binary(path_to_bin)

  # Simulate
  print("* Starting simulation...\n")

  start = time.perf_counter()
  core.run(num_cycles)
  end = time.perf_counter()

  print(f"Simulation done at cycle {core.getCycles()} after {end-start}s.\n")

  return core

def loop_acc():
  core_type = 'single'
  program_name = 'LOOP_ACC'
  path_to_bin = 'programs/loop_acc/loop_acc.bin'
  num_cycles = 2010

  core = execute_bin(core_type, program_name, path_to_bin, num_cycles)

  # Print register and memory contents
  print("x1 = "+str(core.readReg(1)))
  print("x2 = "+str(core.readReg(2)))
  print("x5 = "+str(core.readReg(5)))
  print("pc = "+str(hex(core.readPC())))
  print("mem@4096 = ", core.readDataMem(4096, 4))
  print("")

def fibonacci():
  core_type = 'single'
  program_name = 'FIBONACCI'
  path_to_bin = 'programs/fibonacci/fibonacci.bin'
  num_cycles = 140

  core = execute_bin(core_type, program_name, path_to_bin, num_cycles)

  # Print result
  print("Result = ", core.readDataMem(2048, 4))
  print("")

def endless_loop():
  core_type = 'single'
  program_name = 'ENDLESS_LOOP'
  path_to_bin = 'programs/endless_loop/endless_loop.bin'
  num_cycles = 1000

  core = execute_bin(core_type, program_name, path_to_bin, num_cycles)

def main():
  loop_acc()
  fibonacci()
  endless_loop()

if __name__ == '__main__':
  main()