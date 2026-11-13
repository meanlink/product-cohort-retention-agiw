import math

import numpy as np



def demo_rows():
    rng = np.random.default_rng(1016)
    rows = []
    for cohort_index in range(12):
        size = int(rng.integers(900, 1800))
        survival = 1.0
        for period in range(12):
            if period > 0:
                survival *= rng.uniform(.76, .94)
            retained = int(size * survival)
            rows.append({"cohort": f"2025-{cohort_index + 1:02d}", "period": period,
                         "at_risk": size, "retained": retained})
    return rows

