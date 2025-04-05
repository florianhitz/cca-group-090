import os
import re
import pandas as pd
import matplotlib as plt

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

print(results)
    
    
    
