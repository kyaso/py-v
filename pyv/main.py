import time
from models import SingleCycle

def loop_acc():
  print("===== LOOP_ACC ====")
  print("* Creating core instance...")
  core = SingleCycle()
  print("* Loading binary...")
  core.load_binary('../programs/loop_acc/loop_acc.bin')

  # Simulate
  print("* Starting simulation...\n")
  start = time.perf_counter()
  core.run(3000)
  end = time.perf_counter()

  print("Simulation done after {}s.\n".format(end-start)) 

  # Print register and memory contents
  print("x1 = "+str(core.readReg(1)))
  print("x2 = "+str(core.readReg(2)))
  print("x5 = "+str(core.readReg(5)))
  print("pc = "+str(hex(core.readPC())))
  print("mem@4096 = ", core.readDataMem(4096, 4))

def fibonacci():
  print("===== FIBONACCI ====")
  print("* Creating core instance...")
  core = SingleCycle()
  print("* Loading binary...")
  core.load_binary('../programs/fibonacci/fibonacci.bin')

  # Simulate
  print("* Starting simulation...\n")
  start = time.perf_counter()
  core.run(3000)
  end = time.perf_counter()

  print("Simulation done after {}s.\n".format(end-start)) 

  # Print result
  print("Result = ", core.readDataMem(2048, 4))

def main():
  loop_acc()
  fibonacci()

if __name__ == '__main__':
  main()