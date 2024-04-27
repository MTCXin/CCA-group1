import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import glob
import os
from mpl_toolkits.axes_grid1.inset_locator import mark_inset

target_folder = './question1-results' 
all_files = glob.glob(os.path.join(target_folder, 'all_data*.csv'))

all_data = pd.DataFrame()

for file in all_files:
    df = pd.read_csv(file)
    measurement_type = os.path.basename(file).split('-run')[0]
    df['measurement'] = measurement_type
    all_data = pd.concat([all_data, df], ignore_index=True)


summary = all_data.groupby(['measurement', 'target']) \
    .agg({'p95': ['mean', 'std'], 'QPS': ['mean', 'std'], 'cpu_usage': ['mean', 'std']}) \
    .reset_index()


summary.columns = ['measurement', 'target', 'p95_mean', 'p95_std', 'QPS_mean', 'QPS_std', 'CPU_mean', 'CPU_std']


summary['QPS_mean'] /= 1000
summary['QPS_std'] /= 1000
summary['p95_mean'] /= 1000
summary['p95_std'] /= 1000


markers = {
    'all_data-T1-C0': 'o', 'all_data-T2-C0,1': 's', 'all_data-T2-C0': '^',
      'all_data-T1-C0,1': 'D'
}

labels = {'all_data-T1-C0': 'T=1, C=1', 'all_data-T1-C0,1': 'T=1, C=2', 
          'all_data-T2-C0': 'T=2, C=1', 'all_data-T2-C0,1': 'T=2, C=2'}


all_files = glob.glob(os.path.join(target_folder, '*.csv'))


plt.figure(figsize=(12, 8))
measurements = all_data['measurement'].unique()

for measurement in measurements:
    measurement_data = summary[summary['measurement'] == measurement]
    plt.errorbar(measurement_data['QPS_mean'], measurement_data['p95_mean'],
                 xerr=measurement_data['QPS_std'], yerr=measurement_data['p95_std'],
                 fmt='-', marker=markers[measurement], capsize=3, label=labels[measurement])


plt.xlabel('QPS (k)')
plt.ylabel('p95 Latency (ms)')
plt.title('p95 Latency vs. QPS with 3 times measurement')
plt.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
plt.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
plt.minorticks_on()

plt.legend()
plt.show()

measurements = all_data['measurement'].unique()

for measurement in measurements:
    fig, ax1 = plt.subplots(figsize=(12, 8))
    ax1.set_ylim([0, 2])
    ax1.set_xlim([0, 130])

    ax1.axhline(y=1, color='tab:brown', linestyle='--', label='SLO latency')
    measurement_data = summary[summary['measurement'] == measurement]
    ax1.plot(measurement_data['QPS_mean'], measurement_data['p95_mean'],
                marker='^', color='darkgreen', label='p95 latency')
    
    
    ax1.set_xlabel('QPS (k)')
    ax1.set_ylabel('p95 Latency (ms)', color='darkgreen')
    ax1.tick_params(axis='y', colors='darkgreen')
    fig.suptitle(labels[measurement])
    ax1.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
    ax1.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
    ax1.minorticks_on()

    ax2 = ax1.twinx()
    ax2.set_ylim([0, 200])

    ax2.plot(measurement_data['QPS_mean'], measurement_data['CPU_mean'],
                marker='o', color='tab:blue', label='CPU utilization')
    
    ax2.set_ylabel('CPU utilization (%)', color='tab:blue')
    ax2.tick_params(axis='y', colors='tab:blue')
    fig.legend(loc="lower right", borderaxespad=6)
    plt.tight_layout()
    plt.show()