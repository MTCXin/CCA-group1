# import json
# import matplotlib.pyplot as plt
# import matplotlib.colors as mcolors
# import numpy as np
# from datetime import datetime

# # Define time format and file to use
# time_format = '%Y-%m-%dT%H:%M:%SZ'
# file_name = 'results-2.json'

# # Load JSON file
# with open(file_name, 'r') as file:
#     json_file = json.load(file)

# # Define colors for tasks
# colors = {
#     'parsec-blackscholes': '#CCA000',
#     'parsec-canneal': '#CCCCAA',
#     'parsec-dedup': '#CCACCA',
#     'parsec-ferret': '#AACCCA',
#     'parsec-freqmine': '#0CCA00',
#     'parsec-radix': '#00CCA0',
#     'parsec-vips': '#CC0A00'
# }

# # Initialize task data
# task_data = {}

# # Initialize min_time and max_time to None
# min_time = None
# max_time = None

# # Extract start and end times for each task
# for item in json_file['items']:
#     name = item['status']['containerStatuses'][0]['name']
#     if name not in ['memcached']:  # ignore 'memcached'
#         start_time = datetime.strptime(item['status']['containerStatuses'][0]['state']['terminated']['startedAt'], time_format)
#         end_time = datetime.strptime(item['status']['containerStatuses'][0]['state']['terminated']['finishedAt'], time_format)

#         if min_time is None or start_time < min_time:
#             min_time = start_time
#         if max_time is None or end_time > max_time:
#             max_time = end_time

#         start_sec = (start_time - min_time).total_seconds()
#         duration = (end_time - start_time).total_seconds()

#         if name not in task_data:
#             task_data[name] = []
#         task_data[name].append((start_sec, duration))

# # Normalize start times
# for name in task_data:
#     task_data[name] = [(start_sec - (min_time - datetime(1970, 1, 1)).total_seconds(), dur) for start_sec, dur in task_data[name]]
# print(task_data)
# # Create the plot
# fig, axs = plt.subplots(2, 1, figsize=(10, 10))

# # Task timeline plot
# for idx, (name, times) in enumerate(task_data.items()):
#     for start, duration in times:
#         axs[0].barh(name, duration, left=start, color=colors[name])

# axs[0].set_xlabel('Seconds since first task started')
# axs[0].set_title('Task Execution Timeline')

# # Read and plot latency data
# with open('measure.txt', 'r') as f:
#     lines = f.readlines()

# latencies = []
# times = []

# for line in lines[1:]:
#     parts = line.split()
#     latency = float(parts[12]) / 1000  # convert from microseconds to milliseconds
#     ts_start = int(parts[-2])
#     ts_end = int(parts[-1])
#     midpoint = ((ts_start + ts_end) / 2 - (min_time - datetime(1970, 1, 1)).total_seconds() * 1000) / 1000
#     if (midpoint + 5) >= 0 and (midpoint - 5) <= (max_time - min_time).total_seconds():
#         latencies.append(latency)
#         times.append(midpoint)

# axs[1].plot(times, latencies, marker='o', linestyle='-')
# axs[1].set_xlabel('Seconds since first task started')
# axs[1].set_ylabel('p95 Latency (ms)')
# axs[1].set_title('Tail Latency Over Time')

# plt.tight_layout()
# plt.show()
import json
import matplotlib.pyplot as plt
from datetime import datetime

time_format = '%Y-%m-%dT%H:%M:%SZ'
file_name = 'results-3.json'

with open(file_name, 'r') as file:
    json_file = json.load(file)

colors = {
    'blackscholes': '#CCA000',
    'canneal': '#CCCCAA',
    'dedup': '#CCACCA',
    'ferret': '#AACCCA',
    'freqmine': '#0CCA00',
    'radix': '#00CCA0',
    'vips': '#CC0A00',
    'memcached': '#000000' 
}

node_tasks = {
    'node-a': ['blackscholes', 'memcached'],
    'node-b': ['canneal', 'radix', 'ferret'],
    'node-c': ['dedup', 'vips', 'freqmine']
}

task_data = {}
min_time = None
max_time = None

# extract start & end
for item in json_file['items']:
    name = item['status']['containerStatuses'][0]['name'].replace('parsec-', '')
    if 'memcached' not in name: 
        start_time = datetime.strptime(item['status']['containerStatuses'][0]['state']['terminated']['startedAt'], time_format)
        end_time = datetime.strptime(item['status']['containerStatuses'][0]['state']['terminated']['finishedAt'], time_format)
        
        if min_time is None or start_time < min_time:
            min_time = start_time
        if max_time is None or end_time > max_time:
            max_time = end_time

        if name not in task_data:
            task_data[name] = []
        task_data[name].append((start_time, end_time))
task_data['memcached'] = []
task_data['memcached'].append((min_time, max_time))

tracks = {node: [] for node in node_tasks}  

for node, tasks in node_tasks.items():
    for task in tasks:
        if task in task_data:
            for start_time, end_time in task_data[task]:
                placed = False
                for track in tracks[node]:
                    if not any(st < end_time and et > start_time for st, et in track):
                        track.append((start_time, end_time))
                        placed = True
                        break
                if not placed:
                    tracks[node].append([(start_time, end_time)])

fig, axs = plt.subplots(2, 1, figsize=(15, 10), sharex=True)

for node_index, (node, tracks_list) in enumerate(tracks.items()):
    for track_index, track in enumerate(tracks_list):
        for start_time, end_time in track:
            start_sec = (start_time - min_time).total_seconds()
            duration = (end_time - start_time).total_seconds()
            task_name = [k for k, v in task_data.items() if any((st, et) == (start_time, end_time) for st, et in v)][0]
            color = colors[task_name]
            axs[0].barh(node_index * len(tracks_list) + track_index, duration, left=start_sec, color=color, edgecolor='black', height=0.4, align='center', label=task_name if task_name not in axs[0].get_legend_handles_labels()[1] else "")

handles, labels = axs[0].get_legend_handles_labels()
axs[0].legend(handles, labels, loc='upper right')
axs[0].set_yticks([0.5, 2.5, 4.5])
axs[0].set_yticklabels(['Node A', 'Node B', 'Node C'])
axs[0].set_title('Run3: Task Execution Timeline')

with open('measure3.txt', 'r') as f:
    lines = f.readlines()

latencies = []
times = []

for line in lines[1:]:
    parts = line.split()
    latency = float(parts[12]) / 1000
    ts_start = int(parts[-2])
    ts_end = int(parts[-1])
    midpoint = ((ts_start + ts_end) / 2 - (min_time - datetime(1970, 1, 1)).total_seconds() * 1000) / 1000
    latencies.append(latency)
    times.append(midpoint)

axs[1].plot(times, latencies, 'k-', label='Memcached Tail Latency (p95)')
axs[1].set_xlabel('Seconds since first task started')
axs[1].set_ylabel('p95 Latency (ms)')
axs[1].set_title('Run3: Tail Latency Over Time')

handles, labels = axs[1].get_legend_handles_labels()
axs[1].legend(handles, labels, loc='upper right')
axs[0].grid(True)
axs[1].grid(True)

plt.xlim(right=max(times) + 30)

plt.tight_layout()
plt.show()