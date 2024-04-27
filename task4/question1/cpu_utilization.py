from __future__ import print_function
from time import sleep, time
import psutil

print("Measuring CPU utilization (%) per core")

for i in range(250):
    print("time: {} - CPU usage: {}".format((time() * 1000), psutil.cpu_percent(interval=None, percpu=True)))
    sleep(1)