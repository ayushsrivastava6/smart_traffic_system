"""
core/detector.py
================
Vehicle detection and per-lane counting using YOLOv8 + ByteTrack + supervision.

Based on your original script, upgraded to:
  - Count vehicles per lane (4 lanes = 4 virtual counting lines)
  - Use persistent tracking so each vehicle is counted once per crossing
  - Return live counts to the traffic controller every cycle
  - Write a fully annotated output video with lane overlays and trails
"""

import cv2
import math
import random
from collections import defaultdict

VEHICLE_CLASSES = [2, 3, 5, 7]   # COCO: car, motorcycle, bus, truck


class LaneCounter:
    """
    Manages one virtual counting line for one lane.
    Counts a vehicle when its bounding-box centre crosses the line.
    """
    def __init__(self, lane_id, line_start, line_end, color=(0, 255, 0)):
        self.lane_id = lane_id
        self.start   = line_start   # (x, y)
        self.end     = line_end     # (x, y)
        self.color   = color
        self.counted = {}           # track_id → True (so each vehicle counted once)
        self.total   = 0

    def check_crossing(self, track_id, cx, cy):
        x1, y1 = self.start
        x2, _  = self.end
        in_x   = min(x1, x2) < cx < max(x1, x2)
        near_y = abs(cy - y1) < 8          # 8-pixel crossing tolerance
        if in_x and near_y and track_id not in self.counted:
            self.counted[track_id] = True
            self.total += 1
            return True
        return False

    def draw(self, frame):
        cv2.line(frame, self.start, self.end, self.color, 2)
        label = f"Lane {self.lane_id}: {self.total}"
        cv2.putText(frame, label,
                    (self.start[0], self.start[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.color, 2)


class VehicleDetector:
    def __init__(self, video_path=None, output_path="output/annotated_output.mp4",
                 demo_mode=False):
        self.video_path   = video_path
        self.output_path  = output_path
        self.demo_mode    = demo_mode
        self.cap          = None
        self.sink         = None
        self.model        = None
        self.track_history = defaultdict(list)
        self.frame_idx    = 0
        self.lane_counters = []

        if not demo_mode:
            self._load_model()
            self._open_video()
            self._setup_lanes()

    # ── Setup ──────────────────────────────────────────────────────────

    def _load_model(self):
        try:
            from ultralytics import YOLO
            self.model = YOLO("yolov8n.pt")
            print("  ✓ YOLOv8n loaded.")
        except ImportError:
            raise SystemExit("\n  ERROR: Run: pip install ultralytics\n")

    def _open_video(self):
        try:
            import supervision as sv
        except ImportError:
            raise SystemExit("\n  ERROR: Run: pip install supervision\n")

        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            raise SystemExit(f"\n  ERROR: Cannot open video: {self.video_path}\n")

        self.video_info = sv.VideoInfo.from_video_path(self.video_path)
        self.sink       = sv.VideoSink(self.output_path, self.video_info)
        self.sink.__enter__()
        print(f"  ✓ Video: {self.video_path}")
        print(f"  ✓ Output: {self.output_path}")

    def _setup_lanes(self):
        """
        Divide the frame into 4 equal vertical strips.
        Place a horizontal counting line at 60% down each strip.
        """
        w      = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h      = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        lane_w = w // 4
        line_y = int(h * 0.60)
        colors = [
            (0, 255, 0),
            (255, 165, 0),
            (0, 200, 255),
            (200, 0, 255),
        ]
        for i in range(4):
            self.lane_counters.append(LaneCounter(
                lane_id    = i,
                line_start = (i * lane_w + 10, line_y),
                line_end   = ((i + 1) * lane_w - 10, line_y),
                color      = colors[i],
            ))
        print(f"  ✓ 4 lane counters ready (frame {w}×{h})")

    # ── Per-frame processing ───────────────────────────────────────────

    def process_frame(self):
        """
        Read one frame, run YOLOv8 + ByteTrack, update lane counts.
        Returns {lane_id: count} or None when video ends.
        """
        ret, frame = self.cap.read()
        if not ret:
            return None

        self.frame_idx += 1

        results = self.model.track(
            frame,
            classes = VEHICLE_CLASSES,
            persist = True,
            tracker = "bytetrack.yaml",
            verbose = False,
        )

        annotated = results[0].plot()

        if results[0].boxes.id is not None:
            boxes     = results[0].boxes.xywh.cpu()
            track_ids = results[0].boxes.id.int().cpu().tolist()

            for box, tid in zip(boxes, track_ids):
                cx, cy, bw, bh = float(box[0]), float(box[1]), float(box[2]), float(box[3])

                # Draw movement trail
                trail = self.track_history[tid]
                trail.append((cx, cy))
                if len(trail) > 30:
                    trail.pop(0)
                for j in range(1, len(trail)):
                    cv2.line(annotated,
                             (int(trail[j-1][0]), int(trail[j-1][1])),
                             (int(trail[j][0]),   int(trail[j][1])),
                             (200, 200, 200), 1)

                # Check lane line crossings
                for lc in self.lane_counters:
                    if lc.check_crossing(tid, cx, cy):
                        x1 = int(cx - bw / 2); y1 = int(cy - bh / 2)
                        x2 = int(cx + bw / 2); y2 = int(cy + bh / 2)
                        cv2.rectangle(annotated, (x1, y1), (x2, y2), lc.color, 3)

        # Draw lane lines and labels
        for lc in self.lane_counters:
            lc.draw(annotated)

        total = sum(lc.total for lc in self.lane_counters)
        cv2.putText(annotated, f"Total: {total}  Frame: {self.frame_idx}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        if self.sink:
            self.sink.write_frame(annotated)

        return {lc.lane_id: lc.total for lc in self.lane_counters}

    # ── Demo / simulation ──────────────────────────────────────────────

    def get_demo_counts(self, cycle):
        base = [
            15 + 10 * math.sin(cycle * 0.3),
            5  +  3 * math.sin(cycle * 0.1),
            30 + 12 * math.sin(cycle * 0.2),
            20 +  8 * math.cos(cycle * 0.25),
        ]
        if cycle % 10 == 0:
            base[2] += 20
        return {i: max(0, int(b + random.randint(-3, 3))) for i, b in enumerate(base)}

    # ── Cleanup ────────────────────────────────────────────────────────

    def reset(self):
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.track_history.clear()

    def release(self):
        if self.cap:
            self.cap.release()
        if self.sink:
            try:
                self.sink.__exit__(None, None, None)
            except Exception:
                pass
