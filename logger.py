"""
core/logger.py
==============
Logs every traffic cycle to data/traffic_log.json.
Prints a summary when the system stops.
"""

import json
import os
from datetime import datetime

LOG_PATH = "data/traffic_log.json"


class TrafficLogger:
    def __init__(self):
        os.makedirs("data", exist_ok=True)
        self.records = []
        self.emergency_count = 0
        self.start_time = datetime.now()

    def log_cycle(self, cycle, counts, lane_states, emergency_lane):
        record = {
            "cycle":          cycle,
            "timestamp":      datetime.now().isoformat(),
            "counts":         counts,
            "lane_states":    lane_states,
            "emergency_lane": emergency_lane,
        }
        self.records.append(record)
        if emergency_lane is not None:
            self.emergency_count += 1

        # Write to file every 10 cycles
        if cycle % 10 == 0:
            self._flush()

    def _flush(self):
        with open(LOG_PATH, "w") as f:
            json.dump(self.records, f, indent=2)

    def print_summary(self):
        elapsed = (datetime.now() - self.start_time).seconds
        total_vehicles = sum(
            sum(r["counts"].values()) for r in self.records
        ) if self.records else 0

        print(f"\n  Session summary")
        print(f"  ─────────────────────────────")
        print(f"  Total cycles     : {len(self.records)}")
        print(f"  Runtime          : {elapsed}s")
        print(f"  Emergency events : {self.emergency_count}")
        print(f"  Log saved to     : {LOG_PATH}")
        self._flush()
