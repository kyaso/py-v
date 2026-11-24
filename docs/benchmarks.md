# Simulator performance benchmarks

These measurements compare the bundled RV32I programs in the single-cycle model with
logging disabled (the default) and with INFO messages written to `run.log`. They measure
host simulator throughput in **simulated cycles per second**.

## Example results

Measured on an Apple M5 (arm64), macOS 27.3, CPython 3.12.16, and xPack RISC-V GCC 15.2.0,
using Py-V commit [`d229dc0`](https://github.com/kyaso/py-v/commit/d229dc0d80724596bcecf431a94472bc1752b157).
The programs were built with the flags in `programs/Makefile`.

| Program | Simulated cycles per run | Logging off (cycles/s) | INFO to file (cycles/s) |
| --- | ---: | ---: | ---: |
| `loop_acc` | 2,010 | 11,893 | 1,465 |
| `fibonacci` | 140 | 5,330 | 722 |
| `endless_loop` | 1,000 | 3,661 | 481 |

Each entry is the median of seven measured runs. Each mode had one extra warm-up run,
which was discarded. The elapsed time printed by `main.py` brackets `core.run()`, so it
includes logging during simulation and excludes process startup, model construction, and
loading the binary. Expect different rates with a different Python version, host workload,
or filesystem.

## Reproduce the comparison

From the repository root, build the binaries as in the main README:

```sh
make -C programs
```

If your GCC toolchain uses a different executable prefix, pass it as `RISCV`. For example,
`make -C programs RISCV=riscv-none-elf-` uses the xPack executable names.

Run the following from the repository root with Python 3.10 or newer. It alternates which
logging mode runs first and calculates each rate directly from the elapsed time reported by
the existing simulation entry point. Each invocation overwrites `run.log` in the working
directory.

```python
"""Run from the root of a Py-V checkout after building its bundled programs."""
import platform
import re
import statistics
import subprocess
import sys

pattern = re.compile(r"===== (.*?) =====.*?Sim done at cycle (\d+) after ([\d.eE+-]+)s\.", re.S)
command = (
    "import logging, main, sys; "
    "logging.disable(logging.NOTSET if sys.argv[1] == 'INFO' else logging.CRITICAL); "
    "main.main()"
)
print(platform.platform(), platform.python_implementation(), platform.python_version(), flush=True)
samples = {}
for run in range(8):
    for mode in (("off", "INFO") if run % 2 == 0 else ("INFO", "off")):
        output = subprocess.check_output([sys.executable, "-c", command, mode], text=True)
        measurements = pattern.findall(output)
        assert len(measurements) == 3, output
        assert "mem@4096 =  ['0xe8', '0x3', '0x0', '0x0']" in output, output
        assert "Result =  ['0x37', '0x0', '0x0', '0x0']" in output, output
        for name, cycles, seconds in measurements:
            print(run, mode, name, cycles, seconds)
            if run:
                samples.setdefault((name, mode), []).append(int(cycles) / float(seconds))

for (name, mode), rates in sorted(samples.items()):
    print(name, mode, round(statistics.median(rates)))
```
