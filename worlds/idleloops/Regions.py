from typing import Dict, List

idle_loops_regions_all: Dict[str, List[str]] = {
    "Menu": ["Z1"],
    "Z1": ["Z2"],
    "Z2": ["Z3"],
    "Z3": [],
}

idle_loops_regions_z1: Dict[str, List[str]] = {
    "Menu": ["Z1"],
    "Z1": []
}
