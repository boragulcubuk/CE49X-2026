# -*- coding: utf-8 -*-
import json

path = r"c:\Users\BORA\CE49X\Week02_Python_Modules_and_Data_Science\lab\Lab02_Wave_Energy_Financial_Feasibility.ipynb"
path_new = path.replace(".ipynb", "_NEW.ipynb")
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

cells = nb["cells"]
idx_study = None
idx_map = None
for i, c in enumerate(cells):
    src = "".join(c.get("source", []))
    if "### Study area" in src and "no data overlay" in src:
        idx_study = i
    if idx_study is not None and i == idx_study + 1 and "folium.Map(location=(-31.95" in src:
        idx_map = i
        break

if idx_study is None or idx_map is None:
    raise SystemExit("Study area or map cell not found")

study_cell = cells[idx_study]
map_cell = cells[idx_map]
cells.pop(idx_map)
cells.pop(idx_study)
cells.append(study_cell)
cells.append(map_cell)

nb["cells"] = cells
with open(path_new, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=2)
    f.flush()
import shutil
shutil.copy(path_new, path)
import os
os.remove(path_new)
