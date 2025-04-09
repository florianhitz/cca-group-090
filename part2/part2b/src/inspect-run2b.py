import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from matplotlib.ticker import ScalarFormatter

fps = os.listdir('results-part2b')

results = {}
for fp in fps:
    with open(f'results-part2b/{fp}', 'r') as f:
        bname = fp.split('_')[0]
        nt = fp.split('_')[1].split('-')[0]

        lines = f.readlines()
        value = [l for l in lines if l.startswith('real')][0]
        m = re.search(r'(\d*)m(\d*.\d*)s', value)

        minutes = float(m.group(1))
        seconds = float(m.group(2))
        total = minutes * 60 + seconds

        if bname not in results:
            results[bname] = []
        results[bname].append({nt: total})

for result in results:
    results[result] = sorted(results[result], key=lambda k: list(k.keys())[0])
    results[result] = [list(r.values())[0] for r in results[result]]
    print(result.ljust(12), results[result])
    results[result] = results[result][0] / np.array(results[result])


xticks = [1, 2, 3, 4]
xtick_labels = ['1', '2', '4', '8']



for benchmark, values in results.items():
    plt.plot(xticks, values, marker='o', label=benchmark)

plt.xlabel('# Threads')
plt.ylabel('Speedup')
plt.yscale('log')
plt.yticks([1, 2, 3, 4, 6, 8], labels=['1', '2', '', '4', '', '8'])

plt.title('PARSEC Benchmark Execution Times Over 100 Runs')
plt.xticks(xticks, labels=xtick_labels)
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('plot-run2b.pdf')

#print(results)
    
    
    
