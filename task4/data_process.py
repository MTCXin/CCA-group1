import pandas as pd
import glob
import os

source_folder = './question1-results'  
target_folder = './question1-results' 
if not os.path.exists(target_folder):
    os.makedirs(target_folder)

file_pattern = os.path.join(source_folder, 'measure-*.txt')
files = glob.glob(file_pattern)

for file_path in files:
    with open(file_path, 'r') as file:
        lines = []
        for line in file:
            if line.startswith('Warning') or line.startswith("CPU Usage"):
                break
            if line.startswith("#type") or line.startswith("read"):
                lines.append(line)

        df = pd.DataFrame([x.split() for x in lines[1:]],
                          columns=lines[0].split())

        base_name = os.path.basename(file_path)  
        new_file_name = base_name.replace('.txt', '.csv')  
        csv_path = os.path.join(target_folder, new_file_name)

        df.to_csv(csv_path, index=False)