#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt

df1 = pd.read_csv('results/t1c1-run1.txt', delim_whitespace=True)
df2 = pd.read_csv('results/t1c2-run1.txt', delim_whitespace=True)
df3 = pd.read_csv('results/t2c1-run1.txt', delim_whitespace=True)
df4 = pd.read_csv('results/t2c2-run1.txt', delim_whitespace=True)

plt.figure()

plt.plot(df1['target'], df1['p95'], label='T=1, C=1 (run 1)', marker='o')
plt.plot(df2['target'], df2['p95'], label='T=1, C=2 (run 1)', marker='o')
plt.plot(df3['target'], df3['p95'], label='T=2, C=1 (run 1)', marker='o')
plt.plot(df4['target'], df4['p95'], label='T=2, C=2 (run 1)', marker='o')

plt.legend()
plt.show()

#print(df.columns[7])

