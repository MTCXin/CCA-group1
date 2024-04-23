import json
import sys
from datetime import datetime
import numpy as np

file = sys.argv[1]
time_format = '%Y-%m-%dT%H:%M:%SZ'
files = [file+'-1.json', file+'-2.json', file+'-3.json']

# Initialize dictionaries to hold cumulative task times and counts
task_times = {}
total_times = []

# Process each file
for file_name in files:
    with open(file_name, 'r') as file:
        json_file = json.load(file)
    
    start_times = []
    completion_times = []
    for item in json_file['items']:
        name = item['status']['containerStatuses'][0]['name']
        if str(name) != "memcached":
            try:
                start_time = datetime.strptime(
                        item['status']['containerStatuses'][0]['state']['terminated']['startedAt'],
                        time_format)
                completion_time = datetime.strptime(
                        item['status']['containerStatuses'][0]['state']['terminated']['finishedAt'],
                        time_format)
                
                job_time_seconds = (completion_time - start_time).total_seconds()
                if name not in task_times:
                    task_times[name] = []
                task_times[name].append(job_time_seconds)
                
                start_times.append(start_time)
                completion_times.append(completion_time)
            except KeyError:
                print(f"Job {name} has not completed in {file_name}....")
                sys.exit(0)

    if len(start_times) != 7 and len(completion_times) != 7:
        print(f"You haven't run all the PARSEC jobs in {file_name}. Exiting...")
        sys.exit(0)
    
    total_job_time_seconds = (max(completion_times) - min(start_times)).total_seconds()
    total_times.append(total_job_time_seconds)

# Calculate and print average and standard deviation for each task and total times
print("\nJob Time Statistics (seconds):")
for name, times in task_times.items():
    print(f"{name}: Average = {np.mean(times):.2f}, Std Dev = {np.std(times):.2f}")

print("\nTotal Time Across All Jobs:")
print(f"Average = {np.mean(total_times):.2f}, Std Dev = {np.std(total_times):.2f}")
