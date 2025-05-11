#!/usr/bin/env python3
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def process_data(cores=1, run=1):
    df1 = pd.read_csv(f'../log/4-1-d/t2c{cores}-run{run}.txt', delim_whitespace=True)
    df1['ts_start'] = pd.to_datetime(df1['ts_start'], unit='ms').dt.round('1s').dt.time
    
    df2 = pd.read_csv(f'../log/4-1-d/cpu{cores}-run{run}.txt', delim_whitespace=True, skiprows=2, skipfooter=2)
    df2 = df2.rename(columns={df2.columns[0]: 'ts_start'})
    df2['ts_start'] = pd.to_datetime(df2['ts_start']).dt.round('1s').dt.time
    
    ts = df1['ts_start']
    intervals = list(zip(ts[:-1], ts[1:]))
    
    avg = [df2[df2['ts_start'] >= intervals[0][0]].iloc[0]['%CPU']]
    for start, end in intervals:
        mask = (df2['ts_start'] >= start) & (df2['ts_start'] < end)
        avg.append(df2.loc[mask, '%CPU'].mean())
    
    df = df1.merge(df2, how='left')
    df['avg'] = avg
    
    df = df.sort_values(by='QPS')

    return df


parser = argparse.ArgumentParser(description="Plot QPS and CPU utilization")
parser.add_argument("cores", type=int, choices=[1, 2], help="Number of CPU cores (1 or 2)")
args = parser.parse_args()

CORES = args.cores

df11 = process_data(cores=CORES, run=1)
df12 = process_data(cores=CORES, run=2)
df13 = process_data(cores=CORES, run=3)

df = pd.DataFrame({
    'QPS': df11['QPS'],
    'CPU': np.mean([df11['avg'], df12['avg'], df13['avg']], axis=0),
    'p95': np.mean([df11['p95'], df12['p95'], df13['p95']], axis=0),
})

fig, ax = plt.subplots()

ax.plot(df['QPS'], df['p95']/1000, label='QPS', c='blue', marker='.')
ax.set_xlabel('Achieved QPS')
ax.set_ylabel('95th percentile Latency [ms]')
ax.hlines(0.8, df['QPS'].iloc[0], df['QPS'].iloc[-1], colors='black', linestyles='dashed')

ax2 = ax.twinx()
ax2.plot(df['QPS'], df['CPU'], label='CPU (mvg. avg.)', c='red', marker="v")
ax2.set_ylabel('CPU Usage [%]')


lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(
    lines1 + lines2, 
    labels1 + labels2,
    loc='upper left'
)

plt.title(f'QPS and CPU utilization Threads=2 Cores={CORES}')
plt.savefig(f'../fig/part4-1-d-{CORES}.png')
# plt.show()
