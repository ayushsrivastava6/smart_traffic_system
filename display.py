"""
core/display.py
===============
Live terminal dashboard — clears and redraws each cycle.
Works on Linux, macOS, and Windows 10+ (ANSI support required).
"""

import os

R  = "\033[91m"   # red
G  = "\033[92m"   # green
Y  = "\033[93m"   # yellow
C  = "\033[96m"   # cyan
B  = "\033[1m"    # bold
RS = "\033[0m"    # reset
CL = "\033[2J\033[H"  # clear screen


def _bar(n, mx=50, w=14):
    filled = min(int(n / mx * w), w)
    return "█" * filled + "░" * (w - filled)


def _sig_color(state):
    return {
        "GREEN":           G,
        "EMERGENCY_GREEN": Y,
        "RED":             R,
    }.get(state, RS)


def _cong_color(level):
    return {"LOW": G, "MEDIUM": Y, "HIGH": R}.get(level, RS)


class ConsoleDisplay:
    def render(self, cycle, counts, lane_states, emergency_lane):
        print(CL, end="")

        print(f"{B}{C}{'═'*58}{RS}")
        print(f"{B}{C}   AI Smart Traffic Management System  —  Cycle {cycle:>4}{RS}")
        print(f"{B}{C}{'═'*58}{RS}\n")

        if emergency_lane is not None:
            print(f"{B}{Y}  🚨 EMERGENCY — Lane {emergency_lane} has PRIORITY GREEN{RS}")
            print(f"{Y}  All other lanes forced RED{RS}\n")

        # Table header
        print(f"  {'Lane':<5} {'Signal':<22} {'Count':<18} {'Congestion':<14} {'Green'}")
        print(f"  {'─'*60}")

        for s in lane_states:
            lid  = s["lane_id"]
            sig  = s["state"]
            cnt  = s["vehicle_count"]
            cong = s["congestion"]
            gt   = s["green_time"]
            tr   = s["time_remaining"]
            pct  = s["congestion_pct"]

            sc = _sig_color(sig)
            cc = _cong_color(cong)

            sig_str = f"{sc}{sig:<14}{RS}"
            if sig in ("GREEN", "EMERGENCY_GREEN") and tr > 0:
                sig_str += f"{C} {tr:>2}s left{RS}"
            else:
                sig_str += "         "

            bar_str  = f"{_bar(cnt)} {cnt:>3}"
            cong_str = f"{cc}{cong:<8}{RS} {pct:>3}%"

            print(f"  {lid:<5} {sig_str}  {bar_str}  {cong_str}  {gt}s")

        total   = sum(s["vehicle_count"] for s in lane_states)
        busiest = max(lane_states, key=lambda s: s["vehicle_count"])

        print(f"\n  {'─'*58}")
        print(f"  Total vehicles : {B}{total}{RS}")
        print(f"  Busiest lane   : {B}Lane {busiest['lane_id']}{RS} "
              f"— {busiest['vehicle_count']} vehicles ({busiest['congestion']})")
        print(f"\n  {C}Ctrl+C to stop  |  Output: output/annotated_output.mp4{RS}")
