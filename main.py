"""
main.py — AI Smart Traffic Management System
=============================================
Usage:
  python main.py --demo                          # simulated data, no video needed
  python main.py --video testing/d.mp4           # your real traffic video
  python main.py --video testing/d.mp4 --loop    # loop video continuously
"""

import argparse
import time
import sys
import os

# Make sure we can import from core/
sys.path.insert(0, os.path.dirname(__file__))

from core.detector          import VehicleDetector
from core.traffic_controller import TrafficController
from core.emergency         import EmergencyDetector
from core.logger            import TrafficLogger
from core.display           import ConsoleDisplay


def run(video_path=None, demo_mode=False, loop=False):
    print("\n" + "="*55)
    print("   AI Smart Traffic Management System")
    print("="*55)

    os.makedirs("output", exist_ok=True)
    os.makedirs("data",   exist_ok=True)

    logger    = TrafficLogger()
    display   = ConsoleDisplay()
    emergency = EmergencyDetector()

    print("\n[1/3] Loading vehicle detector...")
    detector = VehicleDetector(
        video_path  = video_path,
        output_path = "output/annotated_output.mp4",
        demo_mode   = demo_mode,
    )

    print("[2/3] Starting traffic controller (4 lanes)...")
    controller = TrafficController(num_lanes=4)

    print("[3/3] System ready.\n")
    print("  Press Ctrl+C to stop.\n")
    print("-" * 55)

    cycle = 0
    try:
        while True:
            cycle += 1

            # ── Get vehicle counts ──────────────────────────────────
            if demo_mode:
                counts = detector.get_demo_counts(cycle)
            else:
                counts = detector.process_frame()
                if counts is None:
                    if loop:
                        print("\n  [Video ended — looping]\n")
                        detector.reset()
                        continue
                    else:
                        print("\n  Video finished. Use --loop to repeat.\n")
                        break

            # ── Emergency check ─────────────────────────────────────
            emerg_lane = emergency.check(counts, cycle, demo_mode=demo_mode)

            # ── Update signal timings ───────────────────────────────
            controller.update(counts, emergency_lane=emerg_lane)

            # ── Log & display ───────────────────────────────────────
            logger.log_cycle(cycle, counts, controller.get_states(), emerg_lane)
            display.render(cycle, counts, controller.get_states(), emerg_lane)

            # Pace the loop (demo needs a delay; video mode processes as fast as possible)
            if demo_mode:
                time.sleep(1.0)

    except KeyboardInterrupt:
        pass

    print("\n" + "="*55)
    print("  Stopped.")
    logger.print_summary()
    if not demo_mode:
        detector.release()
        print("  Annotated video saved: output/annotated_output.mp4")
    print("="*55 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="AI Smart Traffic Management System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --demo
  python main.py --video testing/d.mp4
  python main.py --video testing/d.mp4 --loop
        """
    )
    parser.add_argument("--video", type=str, default=None,
                        help="Path to traffic video file")
    parser.add_argument("--demo",  action="store_true",
                        help="Run with simulated data (no video needed)")
    parser.add_argument("--loop",  action="store_true",
                        help="Loop video when it ends")
    args = parser.parse_args()

    if not args.demo and args.video is None:
        print("\n  No --video given. Starting in DEMO mode.")
        print("  Tip: run  python main.py --video testing/d.mp4  to use your file.\n")
        args.demo = True

    run(video_path=args.video, demo_mode=args.demo, loop=args.loop)


if __name__ == "__main__":
    main()
