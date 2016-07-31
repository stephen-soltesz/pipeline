#!/usr/bin/env python

import psutil
import sys

while True:
  cpu = psutil.cpu_times_percent(interval=1.0)
  if sys.argv[1] == "sys":
    print cpu.system
  if sys.argv[1] == "user":
    print cpu.system+cpu.user
