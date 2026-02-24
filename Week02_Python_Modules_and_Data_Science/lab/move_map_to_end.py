# -*- coding: utf-8 -*-
import json

with open('Lab02_Wave_Energy_Financial_Feasibility.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

cells = nb['cells']
# Find Study area markdown and map code (consecutive)
take = []
for i, c in enumerate(cells):
    s = ''.join(c.get('source', []))
    if '### Study area' in s and 'no data overlay' in s:
        take.append((i, c))
    elif 'folium.Map(location=(-31.95' in s and 'Single location map' in s:
        take.append((i, c))

if len(take) != 2:
    print('Found', len(take), 'cells')
    exit(1)

# Remove in reverse order
for i, _ in sorted(take, reverse=True):
    cells.pop(i)

# Append at end
for _, c in take:
    cells.append(c)

nb['cells'] = cells
with open('Lab02_Wave_Energy_Financial_Feasibility.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=2)
print('Map moved to end.')
