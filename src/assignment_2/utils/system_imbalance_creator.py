"""Simple script for creating the json file for system imbalance."""

import json

import numpy as np

imbalance_dict: dict[str, list[int]] = {}
for i in range(1, 5):
    imbalance_list = np.random.randint(0, 2, size=24).tolist()
    imbalance_dict[str(i)] = imbalance_list

with open("src/assignment_2/data/system_imbalance.json", "w") as f:
    json.dump(imbalance_dict, f, indent=4)
