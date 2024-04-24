import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import glob
import os
from mpl_toolkits.axes_grid1.inset_locator import mark_inset

target_folder = './question1-results' 
all_files = glob.glob(os.path.join(target_folder, '*.csv'))

all_data = pd.DataFrame()

for file in all_files:
    df = pd.read_csv(file)
    measurement_type = os.path.basename(file).split('-run')[0]
    df['measurement'] = measurement_type
    all_data = pd.concat([all_data, df], ignore_index=True)


summary = all_data.groupby(['measurement', 'target']) \
    .agg({'p95': ['mean', 'std'], 'QPS': ['mean', 'std']}) \
    .reset_index()


summary.columns = ['measurement', 'target', 'p95_mean', 'p95_std', 'QPS_mean', 'QPS_std']


summary['QPS_mean'] /= 1000
summary['QPS_std'] /= 1000
summary['p95_mean'] /= 1000
summary['p95_std'] /= 1000


markers = {
    'measure-T1-C0': 'o', 'measure-T1-C0-1': 's', 'measure-T2-C0': '^', 'measure-T2-C0-1': 'D'
}

labels = {'measure-T1-C0': 'T=1, C=1', 'measure-T1-C0-1': 'T=1, C=2', 'measure-T2-C0': 'T=2, C=1', 'measure-T2-C0-1': 'T=2, C=2'}


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


# zoom_area = [26, 28.3]  # kQPS
# ax = plt.gca()

# axins = ax.inset_axes([0.05, 0.55, 0.3, 0.3])  

# for measurement in measurements:
#     measurement_data = summary[summary['measurement'] == measurement]
#     axins.errorbar(measurement_data['QPS_mean'], measurement_data['p95_mean'],
#                    xerr=measurement_data['QPS_std'], yerr=measurement_data['p95_std'],
#                    fmt='-', marker=markers['none'], capsize=3)


# axins.set_xlim(zoom_area[0], zoom_area[1])
# axins.set_ylim(5, 9.8)
# axins.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
# axins.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
# axins.xaxis.set_major_locator(ticker.MaxNLocator(nbins=1)) 
# axins.yaxis.set_major_locator(ticker.MaxNLocator(nbins=3))  
# axins.tick_params(labelsize=8) 


# mark_inset(ax, axins, loc1=2, loc2=4, fc="none", ec="0.5")


plt.legend()
plt.show()