import pandas as pd
import glob
import os
import re
import numpy as np

source_folder = './question1-results'  
target_folder = './question1-results' 
if not os.path.exists(target_folder):
    os.makedirs(target_folder)

pattern = r"time: ([\d.]+) - CPU usage: \[([\d.]+), ([\d.]+), [\d.]+, [\d.]+\]"

file_pattern = os.path.join(source_folder, 'measure-*.txt')
files = glob.glob(file_pattern)

for file_path in files:
    # read cpu usage
    cpu_usage_path = file_path.replace("measure", "server")
    with open(cpu_usage_path, 'r') as cpu_file:
        lines = []
        lines.append("time CPU0 CPU1 CPU_total")
        for line in cpu_file:
            # Extract time
            p_match = re.search(pattern, line)
            if p_match:
                time_value = float(p_match.group(1))
                cpu_0 = float(p_match.group(2))
                cpu_1 = float(p_match.group(3))
                cpu_total = 0.0
                if "-C0-run" in cpu_usage_path:
                    cpu_total = cpu_0
                elif "-C0,1-run" in cpu_usage_path:
                    cpu_total = cpu_0 + cpu_1
                lines.append("{} {} {} {}".format(time_value, cpu_0, cpu_1, cpu_total))
        
        df_cpu = pd.DataFrame([x.split() for x in lines[1:]],
                          columns=lines[0].split())
        base_name = os.path.basename(cpu_usage_path)  
        new_file_name = base_name.replace('.txt', '.csv')  
        csv_path = os.path.join(target_folder, new_file_name)
        df_cpu.to_csv(csv_path, index=False)
    
    # read measurements
    with open(file_path, 'r') as file:
        lines = []
        for line in file:
            if line.startswith('Warning') or line.startswith("CPU Usage"):
                break
            if line.startswith("#type") or line.startswith("read"):
                lines.append(line)

        df_latency = pd.DataFrame([x.split() for x in lines[1:]],
                          columns=lines[0].split())
        base_name = os.path.basename(file_path)  
        new_file_name = base_name.replace('.txt', '.csv')  
        csv_path = os.path.join(target_folder, new_file_name)

        df_latency.to_csv(csv_path, index=False)

        # interleave data from both measurements
        interleaved_data = []
        interleaved_data.append("p95 QPS target ts_start ts_end cpu_usage")
        
        for index, row in df_latency.iterrows():
            time_start = row["ts_start"]
            time_end = row["ts_end"]

            # Filter based on the time range
            filtered_cpu_df = df_cpu[(df_cpu["time"] > time_start) & (df_cpu["time"] <= time_end)]

            # Calculate the average CPU usage for the time range
            if len(filtered_cpu_df) > 1:
                print(filtered_cpu_df)
                print(filtered_cpu_df["CPU_total"][1:])
                avg_cpu_usage_for_range = np.mean([float(i) for i in filtered_cpu_df["CPU_total"][1:]])
                print(avg_cpu_usage_for_range)
            else:
                avg_cpu_usage_for_range = None

            interleaved_data.append("{} {} {} {} {} {}".format(row["p95"], row["QPS"], row["target"], time_start, time_end, avg_cpu_usage_for_range))

        df_interleaved_data = pd.DataFrame([x.split() for x in interleaved_data[1:]],
                          columns=interleaved_data[0].split())
        base_name = os.path.basename(file_path)  
        new_file_name = base_name.replace('.txt', '.csv').replace("measure", "all_data")
        csv_path = os.path.join(target_folder, new_file_name)
        df_interleaved_data.to_csv(csv_path, index=False)

