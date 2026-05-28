# AI Smart Traffic Management System

## What this does

- Reads your traffic video (`testing/d.mp4`)
- Runs **YOLOv8** to detect and track vehicles (car, bus, truck, motorcycle)
- Counts vehicles crossing a virtual line in each of 4 lanes
- Dynamically adjusts green signal time based on how busy each lane is
- Randomly simulates emergency vehicle detection (turns busiest lane GREEN immediately)
- Saves a fully annotated output video to `output/annotated_output.mp4`
- Logs every cycle to `data/traffic_log.json`

---

## Setup (do this once)

### Step 1 — Install dependencies
Open a terminal in this folder and run:
```
pip install -r requirements.txt
```
This installs: `ultralytics` (YOLOv8), `opencv-python`, `supervision`.

YOLOv8 will automatically download the model weights (`yolov8n.pt`, ~6 MB)
the first time you run the system.

### Step 2 — Put your video in the right place
Copy your traffic video to the `testing/` folder and name it `d.mp4`:
```
testing/d.mp4
```
Or use any name and pass it with `--video`.

---

## Running the system

### Option A — Use your real video (recommended)
```
python main.py --video testing/d.mp4
```

### Option B — Loop the video continuously
```
python main.py --video testing/d.mp4 --loop
```

### Option C — Demo mode (no video needed, simulated data)
```
python main.py --demo
```

Press **Ctrl+C** to stop at any time.

---

## Output files

| File | What it is |
|------|-----------|
| `output/annotated_output.mp4` | Your video with bounding boxes, lane lines, and vehicle counts drawn on |
| `data/traffic_log.json` | JSON log of every cycle: counts, signal states, emergency events |

---

## Project structure

```
smart_traffic/
├── main.py                     ← Run this
├── requirements.txt
├── testing/
│   └── d.mp4                   ← Your traffic video goes here
├── output/
│   └── annotated_output.mp4    ← Generated output video
├── data/
│   └── traffic_log.json        ← Cycle-by-cycle log
└── core/
    ├── detector.py             ← YOLOv8 + lane counting (from your original script)
    ├── traffic_controller.py   ← Adaptive signal timing engine
    ├── emergency.py            ← Emergency vehicle detection
    ├── logger.py               ← JSON logging
    └── display.py              ← Live terminal dashboard
```

---

## How the adaptive timing works

| Traffic level | Vehicle count | Green time |
|---------------|---------------|------------|
| LOW           | 0 – 9         | 10 seconds |
| MEDIUM        | 10 – 24       | 25 seconds |
| HIGH          | 25+           | 45 seconds |

Each cycle, the system picks the **busiest lane** for the next green phase.
Emergency events override the normal cycle immediately and hold green for 30 seconds.

---

## Extending the project

- **Change the counting line position**: edit `line_y = int(h * 0.60)` in `core/detector.py`
- **Add more lanes**: change `num_lanes=4` in `main.py` and add more `LaneCounter` entries
- **Real emergency detection**: see the comments in `core/emergency.py`
- **Web dashboard**: the `data/traffic_log.json` file can feed a React frontend
