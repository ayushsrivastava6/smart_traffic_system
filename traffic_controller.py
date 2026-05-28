"""
core/traffic_controller.py
==========================
Adaptive signal timing engine.

Logic:
  1. Receives vehicle counts from detector each cycle
  2. Calculates congestion level per lane (LOW / MEDIUM / HIGH)
  3. Assigns green time proportional to congestion
  4. Picks the next GREEN lane by priority (busiest first)
  5. Handles emergency override (pre-empts normal cycle)
"""

TIMING_TABLE = {
    "LOW":    10,
    "MEDIUM": 25,
    "HIGH":   45,
}

THRESHOLDS = {
    "LOW":    (0,  10),
    "MEDIUM": (10, 25),
    "HIGH":   (25, 9999),
}


def congestion_level(count):
    for level, (lo, hi) in THRESHOLDS.items():
        if lo <= count < hi:
            return level
    return "LOW"


def congestion_pct(count):
    return min(100, int(count / 50 * 100))


class LaneSignal:
    def __init__(self, lane_id):
        self.lane_id        = lane_id
        self.state          = "RED"
        self.vehicle_count  = 0
        self.congestion     = "LOW"
        self.green_time     = TIMING_TABLE["LOW"]
        self.time_remaining = 0

    def update(self, count):
        self.vehicle_count = count
        self.congestion    = congestion_level(count)
        self.green_time    = TIMING_TABLE[self.congestion]

    def to_dict(self):
        return {
            "lane_id":        self.lane_id,
            "state":          self.state,
            "vehicle_count":  self.vehicle_count,
            "congestion":     self.congestion,
            "green_time":     self.green_time,
            "time_remaining": self.time_remaining,
            "congestion_pct": congestion_pct(self.vehicle_count),
        }


class TrafficController:
    def __init__(self, num_lanes=4):
        self.lanes             = [LaneSignal(i) for i in range(num_lanes)]
        self.active_lane       = 0
        self.cycle_timer       = 0
        self.emergency_active  = False
        self.emergency_lane_id = None

    def update(self, counts, emergency_lane=None):
        for lane_id, count in counts.items():
            self.lanes[lane_id].update(count)

        if emergency_lane is not None:
            self._activate_emergency(emergency_lane)
            return

        if self.emergency_active:
            self._clear_emergency()

        self.cycle_timer += 1
        current_green = self.lanes[self.active_lane].green_time

        if self.cycle_timer >= current_green:
            self._next_lane()

        for lane in self.lanes:
            if lane.lane_id == self.active_lane:
                lane.state          = "GREEN"
                lane.time_remaining = max(0, current_green - self.cycle_timer)
            else:
                lane.state          = "RED"
                lane.time_remaining = 0

    def _next_lane(self):
        self.cycle_timer = 0
        others = [l for l in self.lanes if l.lane_id != self.active_lane]
        others.sort(key=lambda l: l.vehicle_count, reverse=True)
        self.active_lane = others[0].lane_id

    def _activate_emergency(self, lane_id):
        self.emergency_active  = True
        self.emergency_lane_id = lane_id
        for lane in self.lanes:
            if lane.lane_id == lane_id:
                lane.state          = "EMERGENCY_GREEN"
                lane.time_remaining = 30
            else:
                lane.state          = "RED"
                lane.time_remaining = 0

    def _clear_emergency(self):
        self.emergency_active  = False
        self.emergency_lane_id = None
        self.cycle_timer       = 0

    def get_states(self):
        return [l.to_dict() for l in self.lanes]
