#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt

def get_df(config):
    df1 = pd.read_csv(f'../result/log/4-1-a/{config}-run1.txt', delim_whitespace=True)
    df2 = pd.read_csv(f'../result/log/4-1-a/{config}-run2.txt', delim_whitespace=True)
    df3 = pd.read_csv(f'../result/log/4-1-a/{config}-run3.txt', delim_whitespace=True)

    df = pd.DataFrame({
        'QPS': df1['QPS'],
        'run1': df1['p95']/1000,
        'run2': df2['p95']/1000,
        'run3': df3['p95']/1000,
    })
    
    df['mean'] = df[['run1', 'run2', 'run3']].mean(axis=1)
    df['std'] = df[['run1', 'run2', 'run3']].std(axis=1)

    df = df.sort_values(by='QPS')
    
    return df

df11 = get_df('t1c1')
df12 = get_df('t1c2')
df21 = get_df('t2c1')
df22 = get_df('t2c2')

plt.figure()

plt.errorbar(df11['QPS'], df11['mean'], yerr=df11['std'], fmt='-o', label='T=1, C=1')
plt.errorbar(df12['QPS'], df12['mean'], yerr=df12['std'], fmt='-^', label='T=1, C=2')
plt.errorbar(df21['QPS'], df21['mean'], yerr=df21['std'], fmt='-s', label='T=2, C=1')
plt.errorbar(df22['QPS'], df22['mean'], yerr=df22['std'], fmt='-P', label='T=2, C=2')

plt.xlabel('Achieved QPS')
plt.ylabel('95th percentile Latency [ms]')

plt.legend()
plt.title('memcached Performance varying Threads(T) and Cores(C)')
plt.savefig('../result/fig/part4_1_a.png')
# plt.show()

