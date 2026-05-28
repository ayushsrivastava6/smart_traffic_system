"""
core/emergency.py
=================
Emergency vehicle detection.

DEMO MODE : randomly triggers an ambulance every ~20 cycles on the busiest lane.
REAL MODE : extend _real_check() with one of:
  - Audio siren detection  (librosa + trained CNN)
  - YOLO ambulance class   (retrain on ambulance images)
  - RFID reader            (serial port tag matching)
"""

import random


class EmergencyDetector:
    def __init__(self):
        self.last_trigger = -999
        self.cooldown     = 15      # min cycles between triggers

    def check(self, counts, cycle, demo_mode=False):
        """Returns lane_id of emergency, or None."""
        if demo_mode:
            return self._demo_check(counts, cycle)
        return self._real_check(counts, cycle)

    def _demo_check(self, counts, cycle):
        if cycle - self.last_trigger < self.cooldown:
            return None
        if random.random() < 0.10:          # 10% chance each eligible cycle
            self.last_trigger = cycle
            return max(counts, key=counts.get)   # target the busiest lane
        return None

    def _real_check(self, counts, cycle):
        # ── Extend here ──────────────────────────────────────────────
        # Example RFID stub:
        #   import serial
        #   tag = serial.Serial('/dev/ttyUSB0', 9600).readline().decode().strip()
        #   if tag in KNOWN_TAGS: return lane_from_tag(tag)
        # ─────────────────────────────────────────────────────────────
        return None
