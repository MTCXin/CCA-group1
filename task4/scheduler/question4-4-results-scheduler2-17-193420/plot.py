import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import numpy as np

# log.txt
with open('log.txt') as f:
    logs = f.readlines()

# measure.txt
with open('measure.txt') as f:
    measures = f.readlines()

# parse log.txt
scheduler_start_time = None
scheduler_end_time = None
memcached_cores = []
batch_jobs = {'blackscholes': [], 'canneal': [], 'dedup': [], 'ferret': [], 'freqmine': [], 'radix': [], 'vips': []}

for log in logs:
    parts = log.split()
    timestamp_str = parts[0]
    timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%f")

    if parts[1] == 'start' and parts[2] == 'scheduler':
        scheduler_start_time = timestamp
    elif parts[1] == 'end' and parts[2] == 'scheduler':
        scheduler_end_time = timestamp
    elif parts[1] == 'start' and parts[2] == 'memcached':
        cores = eval(parts[3])
        memcached_cores.append((timestamp, len(cores)))
    elif parts[1] == 'update_cores' and parts[2] == 'memcached':
        cores = eval(parts[3])
        memcached_cores.append((timestamp, len(cores)))
    elif parts[1] == 'start' and parts[2] in batch_jobs:
        job = parts[2]
        batch_jobs[job].append((timestamp, 'start'))
    elif parts[1] == 'pause' and parts[2] in batch_jobs:
        job = parts[2]
        batch_jobs[job].append((timestamp, 'pause'))
    elif parts[1] == 'unpause' and parts[2] in batch_jobs:
        job = parts[2]
        batch_jobs[job].append((timestamp, 'unpause'))
    elif parts[1] == 'end' and parts[2] in batch_jobs:
        job = parts[2]
        batch_jobs[job].append((timestamp, 'end'))

# parse measure.txt
intervals = int(measures[0].split('=')[1].strip())
timestamp_start = int(measures[1].split(':')[1].strip())
timestamp_end = int(measures[2].split(':')[1].strip())

p95_latency = []
qps = []
interval_duration = (timestamp_end - timestamp_start) / intervals / 1000  # Convert to seconds

for measure in measures[4:]:
    if measure.startswith('read'):
        parts = measure.split()
        p95_latency.append(float(parts[12]))
        qps.append(float(parts[16]))

# align
time_axis = [datetime.datetime.fromtimestamp(timestamp_start/1000.0)-datetime.timedelta(hours=2) + datetime.timedelta(seconds=i * interval_duration) for i in range(intervals)]
timestamp_latency = zip(time_axis, p95_latency)
timestamp_latency = [l for (t, l) in timestamp_latency if t >= scheduler_start_time and t <= scheduler_end_time]

print(timestamp_latency)

timestamp_latency_violation = [l for l in timestamp_latency if l >= 1000.0]

print(timestamp_latency_violation)
print(len(timestamp_latency_violation)/len(timestamp_latency))
time_axis_start_time = scheduler_start_time
time_axis_end_time = scheduler_end_time
time_axis = [(t - time_axis_start_time).total_seconds() for t in time_axis]

# A: p95 latency QPS
fig, (axA, axB, axC) = plt.subplots(3, 1, sharex=True, figsize=(12, 18))

axA.plot(time_axis, [p / 1000 for p in p95_latency], color='blue', label='p95 Latency (ms)', linewidth=2)
axA.axhline(y=1, color='r', linestyle='--', label='Target 1ms Latency')
axA.set_ylabel('p95 Latency (ms)')
axA.set_ylim(0, 2.5)
axA.legend(loc='upper left')

axA2 = axA.twinx()
axA2.fill_between(time_axis, 0, [q / 1000 for q in qps], color='green', alpha=0.3, label='QPS (kQPS)')
axA2.set_ylabel('QPS (kQPS)')
axA2.set_ylim(0, 100)
axA2.legend(loc='upper right')
axA2.set_title('1A')

# B: memcached CPU QPS
core_times = [(t[0] - time_axis_start_time).total_seconds() for t in memcached_cores]
core_values = [t[1] for t in memcached_cores]


for i in range(len(core_times) - 1):
    axB.plot([core_times[i], core_times[i + 1]], [core_values[i], core_values[i]], color='orange')
axB.plot([core_times[-1], (time_axis_end_time - time_axis_start_time).total_seconds()], [core_values[-1], core_values[-1]], color='orange')

axB.set_ylabel('Memcached CPU Cores')
axB.set_ylim(0, 4)
axB.set_yticks(range(0, 5))  
axB.legend(loc='upper left')
axB.set_title('1B')

axB2 = axB.twinx()
axB2.fill_between(time_axis, 0, [q / 1000 for q in qps], color='green', alpha=0.3, label='QPS (kQPS)')
axB2.set_ylabel('QPS (kQPS)')
axB2.set_ylim(0, 100)
axB2.legend(loc='upper right')

# C: batch job
job_colors = {
    'blackscholes': '#CCA000', 'canneal': '#CCCCAA', 'dedup': '#CCACCA', 
    'ferret': '#AACCCA', 'freqmine': '#0CCA00', 'radix': '#00CCA0', 'vips': '#CC0A00'
}

for job, events in batch_jobs.items():
    for i in range(len(events)):
        start_event = events[i]
        if start_event[1] in ['start', 'unpause']:
            for j in range(i + 1, len(events)):
                end_event = events[j]
                if end_event[1] in ['pause', 'end']:
                    start_time_sec = (start_event[0] - time_axis_start_time).total_seconds()
                    end_time_sec = (end_event[0] - time_axis_start_time).total_seconds()
                    axC.barh(job, end_time_sec - start_time_sec, left=start_time_sec, color=job_colors[job], edgecolor='black')
                    break

axC.set_yticks(list(batch_jobs.keys()))
axC.set_xlabel('Time (s)')
axC.set_ylabel('Batch Jobs')
axC.grid(True)


axC.set_xlim(0, (time_axis_end_time - time_axis_start_time).total_seconds())

plt.show()