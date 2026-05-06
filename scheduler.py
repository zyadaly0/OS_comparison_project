"""
CPU Scheduling Comparison Simulator
====================================
Compares Round Robin (RR) and Shortest Job First (SJF) scheduling algorithms.

Author: Teaching Assistant – Operating Systems
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


# ─────────────────────────────────────────────
#  DATA MODEL
# ─────────────────────────────────────────────

@dataclass
class Process:
    """Represents a single process with scheduling attributes."""
    pid: str
    arrival: int
    burst: int

    # Populated after scheduling
    start_time: int = -1
    finish_time: int = -1
    waiting_time: int = 0
    turnaround_time: int = 0
    response_time: int = -1
    remaining: int = field(init=False)

    def __post_init__(self):
        self.remaining = self.burst

    def reset(self):
        """Reset computed fields so the same process can be re-scheduled."""
        self.remaining = self.burst
        self.start_time = -1
        self.finish_time = -1
        self.waiting_time = 0
        self.turnaround_time = 0
        self.response_time = -1

    def clone(self) -> "Process":
        """Return a fresh copy suitable for scheduling."""
        p = Process(self.pid, self.arrival, self.burst)
        p.reset()
        return p


# ─────────────────────────────────────────────
#  VALIDATION UTILITIES
# ─────────────────────────────────────────────

class ValidationError(Exception):
    pass


def validate_process_inputs(pid: str, arrival_str: str, burst_str: str,
                              existing_pids: List[str]) -> Tuple[str, int, int]:
    """
    Validate raw string inputs for a process.
    Returns (pid, arrival, burst) on success, raises ValidationError otherwise.
    """
    pid = pid.strip()
    if not pid:
        raise ValidationError("Process ID cannot be empty.")
    if pid in existing_pids:
        raise ValidationError(f"Duplicate Process ID '{pid}'. Each ID must be unique.")

    try:
        arrival = int(arrival_str.strip())
    except ValueError:
        raise ValidationError("Arrival Time must be a non-negative integer.")
    if arrival < 0:
        raise ValidationError("Arrival Time cannot be negative.")

    try:
        burst = int(burst_str.strip())
    except ValueError:
        raise ValidationError("Burst Time must be a positive integer.")
    if burst <= 0:
        raise ValidationError("Burst Time must be greater than zero.")

    return pid, arrival, burst


def validate_quantum(quantum_str: str) -> int:
    """Validate and return the time quantum."""
    try:
        q = int(quantum_str.strip())
    except ValueError:
        raise ValidationError("Time Quantum must be a positive integer.")
    if q <= 0:
        raise ValidationError("Time Quantum must be greater than zero.")
    return q


# ─────────────────────────────────────────────
#  SCHEDULING ALGORITHMS
# ─────────────────────────────────────────────

def schedule_rr(processes: List[Process], quantum: int) -> Tuple[List[Process], List[Tuple[str, int, int]], List[Tuple[int, str, List[str]]]]:
    """
    Round Robin Scheduling (with arrival times).

    Returns:
        procs      – updated list of Process objects with metrics filled in
        gantt      – list of (pid, start, end) tuples for Gantt chart
        rq_history – list of (time, running_pid, [queued_pids]) snapshots
                     captured once per scheduling decision, used by the
                     Ready Queue View panel (Gap 1 requirement).
    """
    procs = [p.clone() for p in processes]
    procs.sort(key=lambda p: (p.arrival, p.pid))

    gantt: List[Tuple[str, int, int]] = []
    # Each snapshot: (time_point, pid_on_cpu, [pids_waiting_in_queue])
    rq_history: List[Tuple[int, str, List[str]]] = []

    time = 0
    ready: List[Process] = []
    completed = 0
    n = len(procs)
    idx = 0  # index into arrival-sorted procs

    # Seed first arrivals
    while idx < n and procs[idx].arrival <= time:
        ready.append(procs[idx])
        idx += 1

    while completed < n:
        if not ready:
            # CPU idle – jump to next arrival
            time = procs[idx].arrival
            while idx < n and procs[idx].arrival <= time:
                ready.append(procs[idx])
                idx += 1
            continue

        proc = ready.pop(0)

        # Record response time (first time on CPU)
        if proc.response_time == -1:
            proc.response_time = time - proc.arrival

        # Record start (first time on CPU overall)
        if proc.start_time == -1:
            proc.start_time = time

        # Run for min(quantum, remaining)
        run = min(quantum, proc.remaining)

        # Snapshot ready-queue state at this scheduling decision.
        # Captured AFTER popping the running process so the queue shows only
        # processes waiting behind it — exactly what students expect to see.
        rq_history.append((time, proc.pid, [p.pid for p in ready]))

        gantt.append((proc.pid, time, time + run))
        time += run
        proc.remaining -= run

        # Admit any newly arrived processes before re-queuing current one
        while idx < n and procs[idx].arrival <= time:
            ready.append(procs[idx])
            idx += 1

        if proc.remaining == 0:
            proc.finish_time = time
            proc.turnaround_time = proc.finish_time - proc.arrival
            proc.waiting_time = proc.turnaround_time - proc.burst
            completed += 1
        else:
            # Preempted – goes to back of queue
            ready.append(proc)

    return procs, gantt, rq_history


def schedule_sjf(processes: List[Process]) -> Tuple[List[Process], List[Tuple[str, int, int]]]:
    """
    Shortest Job First – Non-Preemptive (with arrival times).

    Returns:
        updated list of Process objects with metrics filled in,
        gantt  – list of (pid, start, end) tuples for Gantt chart
    """
    procs = [p.clone() for p in processes]
    gantt: List[Tuple[str, int, int]] = []
    time = 0
    completed = 0
    n = len(procs)
    done = [False] * n

    while completed < n:
        # Find all arrived, not-yet-done processes
        available = [
            procs[i] for i in range(n)
            if not done[i] and procs[i].arrival <= time
        ]

        if not available:
            # CPU idle – jump forward
            next_arrival = min(procs[i].arrival for i in range(n) if not done[i])
            time = next_arrival
            continue

        # Pick shortest burst; break ties by arrival time, then pid
        proc = min(available, key=lambda p: (p.burst, p.arrival, p.pid))
        idx = procs.index(proc)

        # First time on CPU
        proc.response_time = time - proc.arrival
        proc.start_time = time

        gantt.append((proc.pid, time, time + proc.burst))
        time += proc.burst

        proc.finish_time = time
        proc.turnaround_time = proc.finish_time - proc.arrival
        proc.waiting_time = proc.turnaround_time - proc.burst
        done[idx] = True
        completed += 1

    return procs, gantt


def schedule_srtf(processes: List[Process]) -> Tuple[List[Process], List[Tuple[str, int, int]]]:
    """
    Shortest Remaining Time First – SRTF (Preemptive SJF).

    At every time unit the scheduler inspects all arrived, unfinished processes
    and runs the one with the smallest *remaining* burst time.  If a newly
    arrived process has a shorter remaining time than the currently running one,
    the current process is preempted immediately.

    Algorithm:
    ──────────
    1.  Advance time one unit at a time.
    2.  Collect all processes that have arrived and still have work left.
    3.  Pick the one with the smallest remaining time
        (tie-break: earliest arrival, then lexicographic PID).
    4.  Run it for exactly 1 unit, decrement its remaining time.
    5.  Record Gantt segments by merging consecutive units of the same PID.
    6.  Compute WT, TAT, RT from finish / start bookkeeping.

    Returns:
        procs – list of Process objects with all metrics filled in
        gantt – list of (pid, start, end) — contiguous, cumulative timeline
    """
    if not processes:
        return [], []

    procs = [p.clone() for p in processes]
    n = len(procs)

    # Build a lookup so we can mark finish times efficiently
    proc_map: Dict[str, Process] = {p.pid: p for p in procs}

    # Gantt is built by accumulating 1-unit slices then merging adjacent same-PID
    raw_gantt: List[Tuple[str, int, int]] = []   # 1-unit slices before merging

    time = 0
    completed = 0

    # Find the simulation end time (sum of all bursts + max arrival, upper bound)
    max_time = max(p.arrival for p in procs) + sum(p.burst for p in procs) + 1

    while completed < n and time < max_time:
        # All arrived, not yet finished processes
        available = [p for p in procs if p.arrival <= time and p.remaining > 0]

        if not available:
            # CPU idle this unit — advance and check again
            time += 1
            continue

        # Select process with shortest remaining time; break ties by arrival, pid
        current = min(available, key=lambda p: (p.remaining, p.arrival, p.pid))

        # Record first time on CPU (response time)
        if current.response_time == -1:
            current.response_time = time - current.arrival

        # Record absolute first start time
        if current.start_time == -1:
            current.start_time = time

        # Run for exactly 1 time unit
        raw_gantt.append((current.pid, time, time + 1))
        current.remaining -= 1
        time += 1

        # Check for completion
        if current.remaining == 0:
            current.finish_time = time
            current.turnaround_time = current.finish_time - current.arrival
            current.waiting_time = current.turnaround_time - current.burst
            completed += 1

    # ── Merge consecutive 1-unit slices of the same PID into one Gantt block ──
    # This keeps the Gantt readable: instead of 30 individual blocks for a
    # process with burst=30, we show one uninterrupted block (when no preemption
    # occurred) or several blocks separated only where preemptions happened.
    gantt: List[Tuple[str, int, int]] = []
    if raw_gantt:
        cur_pid, cur_start, cur_end = raw_gantt[0]
        for pid, start, end in raw_gantt[1:]:
            if pid == cur_pid and start == cur_end:
                # Same process, consecutive — extend the current block
                cur_end = end
            else:
                gantt.append((cur_pid, cur_start, cur_end))
                cur_pid, cur_start, cur_end = pid, start, end
        gantt.append((cur_pid, cur_start, cur_end))

    return procs, gantt


# ─────────────────────────────────────────────
#  METRICS HELPERS
# ─────────────────────────────────────────────

def compute_averages(procs: List[Process]) -> Dict[str, float]:
    n = len(procs)
    return {
        "avg_wt":  sum(p.waiting_time    for p in procs) / n,
        "avg_tat": sum(p.turnaround_time for p in procs) / n,
        "avg_rt":  sum(p.response_time   for p in procs) / n,
    }


def fairness_index(procs: List[Process]) -> float:
    """Jain's Fairness Index based on waiting times (1.0 = perfectly fair)."""
    wts = [p.waiting_time for p in procs]
    n = len(wts)
    if n == 0:
        return 1.0
    s = sum(wts)
    sq = sum(w * w for w in wts)
    return (s * s) / (n * sq) if sq > 0 else 1.0


# ─────────────────────────────────────────────
#  COLOUR PALETTE  (distinct colours per PID)
# ─────────────────────────────────────────────

PROCESS_COLORS = [
    "#4E9AF1", "#F06C6C", "#56C785", "#F5A623",
    "#A78BFA", "#F472B6", "#22D3EE", "#FB923C",
    "#84CC16", "#E879F9", "#2DD4BF", "#FACC15",
]

IDLE_COLOR = "#9CA3AF"


def pid_color(pid: str, pid_list: List[str]) -> str:
    """Return a consistent colour for a given PID."""
    try:
        idx = pid_list.index(pid)
        return PROCESS_COLORS[idx % len(PROCESS_COLORS)]
    except ValueError:
        return "#CCCCCC"


# ─────────────────────────────────────────────
#  GANTT CHART DRAWING
# ─────────────────────────────────────────────

def draw_gantt(canvas: tk.Canvas, gantt: List[Tuple[str, int, int]],
               pid_list: List[str], title: str):
    """
    Draw a Gantt chart on a Tkinter Canvas widget.

    Correctness guarantees
    ──────────────────────
    • Time is cumulative: every segment's x1 = MARGIN_LEFT + segment.start * scale
      and x2 = MARGIN_LEFT + segment.end * scale, so blocks are placed purely by
      their absolute start/end times — never by sequential pixel accumulation.
    • Each block starts exactly where the previous one ended because x2 of block N
      equals x1 of block N+1 (both computed from the same scale and their start/end
      values which are already contiguous in the gantt list).
    • Block width = (end - start) * scale  →  directly proportional to duration.
    • Timeline labels show the actual integer time values from the gantt data.
    • CPU-idle gaps are filled with an explicit grey "IDLE" block so the timeline
      is always visually contiguous with no unexplained white space.

    Args:
        canvas   : target Canvas (inside a horizontally-scrollable frame)
        gantt    : list of (pid, start, end) — produced by schedule_rr / schedule_sjf
        pid_list : ordered list of all process PIDs (for stable colour mapping)
        title    : text rendered above the chart
    """
    canvas.delete("all")
    if not gantt:
        return

    # ── Layout constants ──────────────────────────────────────────────────────
    MARGIN_LEFT = 70       # px reserved on the left for the "CPU" y-label
    MARGIN_RIGHT = 30      # px of padding after the last bar
    MARGIN_TOP   = 14      # px above the title text
    TITLE_H      = 22      # height reserved for the title
    BAR_Y        = MARGIN_TOP + TITLE_H + 8   # top edge of the bar row
    BAR_H        = 46      # height of each process bar
    TICK_H       = 7       # length of the tick mark below the bar
    LABEL_PAD    = 3       # gap between tick bottom and time-label top
    MIN_PX_PER_UNIT = 20  # minimum pixels per 1 time unit (ensures readability)

    FONT_BAR   = ("Consolas", 10, "bold")
    FONT_TIME  = ("Consolas", 8)
    FONT_TITLE = ("Segoe UI", 11, "bold")
    FONT_YAXIS = ("Segoe UI", 9, "bold")

    # ── Fill idle gaps so the timeline is always contiguous ──────────────────
    # Build a complete segment list that includes IDLE slots for any gap between
    # consecutive gantt entries.  The scheduling algorithms never emit idle slots
    # explicitly, so we insert them here purely for display purposes.
    full_segments: List[Tuple[str, int, int]] = []
    for i, (pid, start, end) in enumerate(gantt):
        if i == 0 and start > 0:
            # Gap before the very first segment
            full_segments.append(("IDLE", 0, start))
        elif i > 0:
            prev_end = gantt[i - 1][2]
            if start > prev_end:
                full_segments.append(("IDLE", prev_end, start))
        full_segments.append((pid, start, end))

    # ── Total timeline span ───────────────────────────────────────────────────
    t_start = full_segments[0][1]   # always 0 (or first arrival)
    t_end   = full_segments[-1][2]  # last finish time
    total_span = max(t_end - t_start, 1)

    # ── Determine scale (pixels per time unit) ────────────────────────────────
    # Use the canvas's ACTUAL rendered width (winfo_width returns the real pixel
    # width after the window is laid out; fall back to the configured width if
    # the window hasn't been shown yet).
    canvas.update_idletasks()
    actual_w = canvas.winfo_width()
    if actual_w < 50:                       # widget not yet mapped
        actual_w = int(canvas["width"])

    avail_w = actual_w - MARGIN_LEFT - MARGIN_RIGHT
    # Choose the larger of: (fit everything in the visible area) vs MIN_PX_PER_UNIT
    scale = max(avail_w / total_span, MIN_PX_PER_UNIT)

    # ── Total canvas dimensions (may exceed visible width → horizontal scroll) ─
    total_px_w = MARGIN_LEFT + total_span * scale + MARGIN_RIGHT
    canvas_h   = BAR_Y + BAR_H + TICK_H + LABEL_PAD + 14 + 6  # bars + ticks + labels + padding

    canvas.config(height=int(canvas_h))
    canvas.config(scrollregion=(0, 0, int(total_px_w), int(canvas_h)))

    # ── Title ─────────────────────────────────────────────────────────────────
    # Centred over the visible canvas width (not the scrollable total width)
    canvas.create_text(
        actual_w // 2, MARGIN_TOP,
        text=title, font=FONT_TITLE, fill="#1E293B", anchor="n"
    )

    # ── Y-axis label ──────────────────────────────────────────────────────────
    canvas.create_text(
        MARGIN_LEFT - 12, BAR_Y + BAR_H // 2,
        text="CPU", font=FONT_YAXIS, fill="#64748B", angle=90
    )

    # ── Helper: convert an absolute time value to a canvas x-coordinate ───────
    def time_to_x(t: int) -> float:
        """
        Map time t → pixel x.
        x1 of any segment = time_to_x(segment.start)
        x2 of any segment = time_to_x(segment.end)
        Because both use the SAME scale and SAME MARGIN_LEFT, consecutive
        segments are guaranteed to share an x boundary: x2(N) == x1(N+1).
        """
        return MARGIN_LEFT + (t - t_start) * scale

    # ── Draw segments ─────────────────────────────────────────────────────────
    drawn_tick_times: set = set()   # avoid overprinting duplicate tick labels

    for seg_pid, seg_start, seg_end in full_segments:
        x1 = time_to_x(seg_start)   # left edge  — absolute, from start time
        x2 = time_to_x(seg_end)     # right edge — absolute, from end   time
        # width = x2 - x1 = (seg_end - seg_start) * scale  ✓ proportional to duration

        is_idle = (seg_pid == "IDLE")
        color   = IDLE_COLOR if is_idle else pid_color(seg_pid, pid_list)
        label   = "IDLE"    if is_idle else seg_pid

        # Bar rectangle
        canvas.create_rectangle(
            x1, BAR_Y, x2, BAR_Y + BAR_H,
            fill=color,
            outline="#FFFFFF",
            width=2
        )

        # PID / IDLE label — only if the bar is wide enough to fit text
        bar_px = x2 - x1
        if bar_px >= 16:
            canvas.create_text(
                (x1 + x2) / 2, BAR_Y + BAR_H / 2,
                text=label,
                font=FONT_BAR,
                fill="#FFFFFF" if not is_idle else "#374151"
            )

        # ── Tick + time label at the LEFT edge of this segment ────────────────
        # Only draw if this time value hasn't been labelled yet (prevents
        # duplicate labels when two adjacent segments share a boundary).
        if seg_start not in drawn_tick_times:
            tx = x1
            canvas.create_line(
                tx, BAR_Y + BAR_H,
                tx, BAR_Y + BAR_H + TICK_H,
                fill="#64748B", width=1
            )
            canvas.create_text(
                tx, BAR_Y + BAR_H + TICK_H + LABEL_PAD,
                text=str(seg_start),
                font=FONT_TIME, fill="#475569", anchor="n"
            )
            drawn_tick_times.add(seg_start)

    # ── Final tick + label at the very end of the timeline ────────────────────
    if t_end not in drawn_tick_times:
        xf = time_to_x(t_end)
        canvas.create_line(
            xf, BAR_Y + BAR_H,
            xf, BAR_Y + BAR_H + TICK_H,
            fill="#64748B", width=1
        )
        canvas.create_text(
            xf, BAR_Y + BAR_H + TICK_H + LABEL_PAD,
            text=str(t_end),
            font=FONT_TIME, fill="#475569", anchor="n"
        )


# ─────────────────────────────────────────────
#  COMPARISON GENERATOR
# ─────────────────────────────────────────────

def generate_comparison(rr_procs, rr_avg, rr_fair,
                         sjf_procs, sjf_avg, sjf_fair,
                         quantum: int,
                         srtf_procs=None, srtf_avg=None, srtf_fair=None) -> str:
    """
    Generate a full textual comparison report.

    Accepts two-algorithm (RR + SJF) or three-algorithm (RR + SJF + SRTF) data.
    When srtf_procs is None the report falls back to the original two-algorithm
    format so no existing call-site is broken.
    """
    three = srtf_procs is not None

    lines = []
    lines.append("═" * 70)
    lines.append("  📊  COMPARISON & ANALYSIS REPORT")
    if three:
        lines.append("       Round Robin  |  SJF (Non-Preemptive)  |  SRTF (Preemptive SJF)")
    lines.append("═" * 70)

    # ── Helper: pick best among 2 or 3 values (lower = better) ──────────────
    def best2(a, b):
        return "RR" if a < b else ("SJF" if b < a else "TIE")

    def best3(r, s, t):
        """Return label of the smallest value among rr(r), sjf(s), srtf(t)."""
        m = min(r, s, t)
        winners = []
        if r == m: winners.append("RR")
        if s == m: winners.append("SJF")
        if t == m: winners.append("SRTF")
        return "/".join(winners)

    if three:
        wt_w  = best3(rr_avg["avg_wt"],  sjf_avg["avg_wt"],  srtf_avg["avg_wt"])
        tat_w = best3(rr_avg["avg_tat"], sjf_avg["avg_tat"], srtf_avg["avg_tat"])
        rt_w  = best3(rr_avg["avg_rt"],  sjf_avg["avg_rt"],  srtf_avg["avg_rt"])

        lines.append(f"\n  {'Metric':<22} {'RR':>8}  {'SJF':>8}  {'SRTF':>8}  {'Best':>8}")
        lines.append(f"  {'─'*22} {'─'*8}  {'─'*8}  {'─'*8}  {'─'*8}")
        lines.append(f"  {'Avg Waiting Time':<22} {rr_avg['avg_wt']:>8.2f}  "
                     f"{sjf_avg['avg_wt']:>8.2f}  {srtf_avg['avg_wt']:>8.2f}  {wt_w:>8}")
        lines.append(f"  {'Avg Turnaround':<22} {rr_avg['avg_tat']:>8.2f}  "
                     f"{sjf_avg['avg_tat']:>8.2f}  {srtf_avg['avg_tat']:>8.2f}  {tat_w:>8}")
        lines.append(f"  {'Avg Response Time':<22} {rr_avg['avg_rt']:>8.2f}  "
                     f"{sjf_avg['avg_rt']:>8.2f}  {srtf_avg['avg_rt']:>8.2f}  {rt_w:>8}")
        lines.append(f"\n  {'Fairness (Jain)':<22} {rr_fair:>8.4f}  "
                     f"{sjf_fair:>8.4f}  {srtf_fair:>8.4f}")

        rr_fairer   = (rr_fair >= sjf_fair and rr_fair >= srtf_fair)
        srtf_fairer = (srtf_fair >= rr_fair and srtf_fair >= sjf_fair)
    else:
        wt_w  = best2(rr_avg["avg_wt"],  sjf_avg["avg_wt"])
        tat_w = best2(rr_avg["avg_tat"], sjf_avg["avg_tat"])
        rt_w  = best2(rr_avg["avg_rt"],  sjf_avg["avg_rt"])
        lines.append(f"\n  Avg Waiting Time   →  RR: {rr_avg['avg_wt']:.2f}  |  "
                     f"SJF: {sjf_avg['avg_wt']:.2f}   ✓ {wt_w}")
        lines.append(f"  Avg Turnaround     →  RR: {rr_avg['avg_tat']:.2f}  |  "
                     f"SJF: {sjf_avg['avg_tat']:.2f}   ✓ {tat_w}")
        lines.append(f"  Avg Response Time  →  RR: {rr_avg['avg_rt']:.2f}  |  "
                     f"SJF: {sjf_avg['avg_rt']:.2f}   ✓ {rt_w}")
        lines.append(f"\n  Fairness (Jain's):  RR={rr_fair:.4f}  |  SJF={sjf_fair:.4f}")
        rr_fairer   = rr_fair >= sjf_fair
        srtf_fairer = False

    # ── Build per-algorithm maps ─────────────────────────────────────────────
    rr_map  = {p.pid: p for p in rr_procs}
    sjf_map = {p.pid: p for p in sjf_procs}
    srtf_map = {p.pid: p for p in srtf_procs} if three else {}

    long_pid   = max(rr_map, key=lambda pid: rr_map[pid].burst)
    long_burst = rr_map[long_pid].burst
    short_pid  = min(sjf_map, key=lambda pid: sjf_map[pid].burst)

    rr_worst_rt   = max(rr_procs,  key=lambda p: p.response_time)
    sjf_worst_rt  = max(sjf_procs, key=lambda p: p.response_time)

    # ── Context-switch estimate for RR ───────────────────────────────────────
    n = len(rr_procs)
    context_switches = sum(
        math.ceil(p.burst / quantum) - 1 for p in rr_procs if p.burst > quantum
    )

    # ════════════════════════════════════════════════════════════════════════
    # ANALYSIS QUESTIONS
    # ════════════════════════════════════════════════════════════════════════
    lines.append("\n" + "─" * 70)
    lines.append("  🔍  ANALYSIS QUESTIONS")
    lines.append("─" * 70)

    # Q1 – Lower avg WT?
    lines.append(f"\n  Q1. Which algorithm gave lower average waiting time?")
    lines.append(f"      → {wt_w}")
    if "SRTF" in wt_w and three:
        lines.append(f"        SRTF is provably optimal for average waiting time among")
        lines.append(f"        preemptive schedulers — it always minimises total wait")
        lines.append(f"        by running the job closest to completion first.")
    elif "SJF" in wt_w:
        lines.append(f"        SJF always picks the shortest available job, keeping")
        lines.append(f"        cumulative wait low for the majority of processes.")
    elif "RR" in wt_w:
        lines.append(f"        RR's time-slicing distributed waiting evenly, giving a")
        lines.append(f"        lower overall average on this dataset.")

    # Q2 – Lower avg RT?
    lines.append(f"\n  Q2. Which algorithm gave lower average response time?")
    lines.append(f"      → {rt_w}")
    if "RR" in rt_w:
        lines.append(f"        Every process gets its first CPU slice within ≤{quantum} units,")
        lines.append(f"        bounding first-response time tightly — ideal for interactive use.")
    if "SRTF" in rt_w and three:
        lines.append(f"        SRTF preempts long jobs the instant a shorter job arrives,")
        lines.append(f"        giving short processes an extremely fast first response.")

    # Q3 – RR fairer?
    lines.append(f"\n  Q3. Did Round Robin appear fairer across all processes?")
    if rr_fairer:
        lines.append(f"      → YES  (RR Jain index = {rr_fair:.4f})")
        lines.append(f"        No process is starved; every process rotates through the")
        lines.append(f"        ready queue within each cycle of the quantum.")
    elif three and srtf_fairer:
        lines.append(f"      → Not the fairest here.  SRTF has the highest fairness")
        lines.append(f"        index ({srtf_fair:.4f}) on this workload because it continuously")
        lines.append(f"        serves whichever process can finish soonest.")
    else:
        lines.append(f"      → On this dataset SJF was equally or more fair.")

    # Q4 – SJF short-job efficiency?
    lines.append(f"\n  Q4. Did SJF complete short jobs more efficiently?")
    short_burst  = sjf_map[short_pid].burst
    sjf_short_tat = sjf_map[short_pid].turnaround_time
    rr_short_tat  = rr_map[short_pid].turnaround_time
    lines.append(f"      Shortest process: {short_pid} (burst={short_burst})")
    lines.append(f"      TAT → RR={rr_short_tat}  SJF={sjf_short_tat}", )
    if three:
        lines.append(f"            SRTF={srtf_map[short_pid].turnaround_time}")
    if sjf_short_tat <= rr_short_tat:
        lines.append(f"      → YES. SJF scheduled {short_pid} earlier, confirming its")
        lines.append(f"        short-job preference for non-preemptive scheduling.")
    else:
        lines.append(f"      → RR served {short_pid} faster here (small quantum effect).")

    # Q5 – Quantum effect?
    lines.append(f"\n  Q5. How did the chosen quantum (q={quantum}) affect Round Robin?")
    lines.append(f"      With q={quantum} and {n} processes:")
    lines.append(f"      • Max first-response wait ≤ {quantum}×({n}-1) = {quantum*(n-1)} units")
    lines.append(f"      • Estimated mid-run preemptions: ≥{context_switches}")
    if quantum <= 3:
        lines.append(f"      • Small quantum → very responsive but high context-switch overhead.")
    elif quantum <= 8:
        lines.append(f"      • Moderate quantum → balanced responsiveness and overhead.")
    else:
        lines.append(f"      • Large quantum → fewer switches; approaches FCFS behaviour.")

    # Q6 – Recommendation
    lines.append(f"\n  Q6. Which algorithm is recommended for this workload?")
    if three:
        score = {"RR": 0, "SJF": 0, "SRTF": 0}
        for label in [wt_w, tat_w, rt_w]:
            for algo in ["RR", "SJF", "SRTF"]:
                if algo in label:
                    score[algo] += 1
        if rr_fairer:   score["RR"]   += 1
        if srtf_fairer: score["SRTF"] += 1
        best = max(score, key=score.get)
        lines.append(f"      ★ RECOMMENDATION: {best}  "
                     f"(scores — RR:{score['RR']}  SJF:{score['SJF']}  SRTF:{score['SRTF']})")
        if best == "SRTF":
            lines.append(f"        SRTF wins on most efficiency metrics. Use for batch")
            lines.append(f"        workloads where burst times are predictable and")
            lines.append(f"        minimising average wait / turnaround is the priority.")
        elif best == "RR":
            lines.append(f"        RR wins overall. Use for interactive / time-sharing")
            lines.append(f"        environments where fairness and responsiveness matter.")
        else:
            lines.append(f"        SJF wins here. Use for batch workloads with known")
            lines.append(f"        burst times and no starvation concern.")
    else:
        score_rr  = (wt_w=="RR")+(tat_w=="RR")+(rt_w=="RR")+(1 if rr_fairer else 0)
        score_sjf = (wt_w=="SJF")+(tat_w=="SJF")+(rt_w=="SJF")+(0 if rr_fairer else 1)
        if score_rr > score_sjf:
            lines.append(f"      ★ RECOMMENDATION: Round Robin  ({score_rr}/4 vs SJF {score_sjf}/4)")
        elif score_sjf > score_rr:
            lines.append(f"      ★ RECOMMENDATION: SJF  ({score_sjf}/4 vs RR {score_rr}/4)")
        else:
            lines.append(f"      ★ TIE — choose RR for interactive, SJF for batch.")

    # ════════════════════════════════════════════════════════════════════════
    # LONG-PROCESS TREATMENT
    # ════════════════════════════════════════════════════════════════════════
    lines.append("\n" + "─" * 70)
    lines.append("  🐘  LONG-PROCESS TREATMENT ANALYSIS")
    lines.append("─" * 70)
    lines.append(f"\n  Longest job: {long_pid}  (burst = {long_burst} units)")
    rr_lp_wt  = rr_map[long_pid].waiting_time
    rr_lp_rt  = rr_map[long_pid].response_time
    sjf_lp_wt = sjf_map[long_pid].waiting_time
    sjf_lp_rt = sjf_map[long_pid].response_time

    if three:
        srtf_lp_wt = srtf_map[long_pid].waiting_time
        srtf_lp_rt = srtf_map[long_pid].response_time
        lines.append(f"  ┌──────────────┬───────────┬───────────┬───────────┐")
        lines.append(f"  │ Metric       │    RR     │    SJF    │   SRTF    │")
        lines.append(f"  ├──────────────┼───────────┼───────────┼───────────┤")
        lines.append(f"  │ Waiting Time │ {rr_lp_wt:^9} │ {sjf_lp_wt:^9} │ {srtf_lp_wt:^9} │")
        lines.append(f"  │ Response Time│ {rr_lp_rt:^9} │ {sjf_lp_rt:^9} │ {srtf_lp_rt:^9} │")
        lines.append(f"  └──────────────┴───────────┴───────────┴───────────┘")
        if srtf_lp_wt >= sjf_lp_wt:
            lines.append(f"  ✦  SRTF penalises {long_pid} most severely ({srtf_lp_wt} units wait)")
            lines.append(f"     because every shorter arriving process preempts it, making")
            lines.append(f"     starvation risk HIGHEST under SRTF for long jobs.")
        else:
            lines.append(f"  ✦  SRTF gave {long_pid} a lower wait than SJF on this dataset")
            lines.append(f"     because no shorter jobs kept arriving after it started.")
        srtf_worst_rt = max(srtf_procs, key=lambda p: p.response_time)
        lines.append(f"\n  Worst response-time process per algorithm:")
        lines.append(f"    RR   → {rr_worst_rt.pid}  (RT={rr_worst_rt.response_time}, burst={rr_worst_rt.burst})")
        lines.append(f"    SJF  → {sjf_worst_rt.pid}  (RT={sjf_worst_rt.response_time}, burst={sjf_worst_rt.burst})")
        lines.append(f"    SRTF → {srtf_worst_rt.pid}  (RT={srtf_worst_rt.response_time}, burst={srtf_worst_rt.burst})")
    else:
        lines.append(f"  ┌──────────────┬───────────────┬───────────────┐")
        lines.append(f"  │ Metric       │ Round Robin   │      SJF      │")
        lines.append(f"  ├──────────────┼───────────────┼───────────────┤")
        lines.append(f"  │ Waiting Time │ {rr_lp_wt:^13} │ {sjf_lp_wt:^13} │")
        lines.append(f"  │ Response Time│ {rr_lp_rt:^13} │ {sjf_lp_rt:^13} │")
        lines.append(f"  └──────────────┴───────────────┴───────────────┘")
        lines.append(f"\n  Worst response-time process:")
        lines.append(f"    RR  → {rr_worst_rt.pid}  (RT={rr_worst_rt.response_time}, burst={rr_worst_rt.burst})")
        lines.append(f"    SJF → {sjf_worst_rt.pid}  (RT={sjf_worst_rt.response_time}, burst={sjf_worst_rt.burst})")

    # ════════════════════════════════════════════════════════════════════════
    # SRTF-SPECIFIC OBSERVATIONS  (only in 3-algo mode)
    # ════════════════════════════════════════════════════════════════════════
    if three:
        lines.append("\n" + "─" * 70)
        lines.append("  ⚡  SRTF-SPECIFIC OBSERVATIONS")
        lines.append("─" * 70)

        # Count preemptions: SRTF gantt segments > n implies preemptions occurred
        # (we don't have the gantt here, but we can infer from response/start times)
        srtf_opt_wt = "SRTF" in wt_w
        lines.append(f"\n  ✦  SRTF is the preemptive extension of SJF.  It preempts the")
        lines.append(f"     currently running process whenever a newly-arrived process")
        lines.append(f"     has a shorter *remaining* time, enabling CPU reallocation")
        lines.append(f"     mid-execution — something SJF (non-preemptive) cannot do.")
        if srtf_opt_wt:
            lines.append(f"  ✦  SRTF achieved the LOWEST average waiting time ({srtf_avg['avg_wt']:.2f})")
            lines.append(f"     on this dataset, consistent with its theoretical optimality")
            lines.append(f"     for minimising avg WT among all preemptive policies.")
        lines.append(f"  ✦  STARVATION RISK under SRTF is the highest of the three:")
        lines.append(f"     a continuous stream of short jobs can indefinitely block")
        lines.append(f"     longer processes (e.g., {long_pid}, burst={long_burst}).")
        lines.append(f"  ✦  Compared to SJF (non-preemptive): SRTF's Gantt chart shows")
        lines.append(f"     more segments (each preemption creates a new bar) — the")
        lines.append(f"     trade-off is better avg WT at the cost of more context switches.")
        lines.append(f"  ✦  Compared to RR: SRTF has no fixed quantum — the 'slice'")
        lines.append(f"     length is dynamic, determined by when a shorter job arrives.")
        lines.append(f"     This makes SRTF more efficient but less predictable than RR.")

    # ════════════════════════════════════════════════════════════════════════
    # KEY OBSERVATIONS
    # ════════════════════════════════════════════════════════════════════════
    lines.append("\n" + "─" * 70)
    lines.append("  🔍  KEY OBSERVATIONS")
    lines.append("─" * 70)

    if "SJF" in wt_w or "SRTF" in wt_w:
        lines.append("  ✦  SJF / SRTF achieve lower average waiting time by always")
        lines.append("     preferring processes closest to completion.")
    else:
        lines.append("  ✦  RR achieves the lowest average waiting time here.")

    if "RR" in rt_w:
        lines.append(f"  ✦  RR provides the tightest response-time bound (≤{quantum} units per")
        lines.append(f"     rotation), making it the best choice for interactive systems.")

    if rr_fairer:
        lines.append(f"  ✦  RR is the most FAIR algorithm (Jain index {rr_fair:.4f}).")
        lines.append(f"     No process waits indefinitely — starvation is impossible.")
    if three:
        lines.append(f"  ✦  SRTF has the highest starvation risk: long jobs can wait")
        lines.append(f"     arbitrarily long if short jobs keep arriving.")
    lines.append(f"  ✦  SJF (non-preemptive) also risks starvation but once a long")
    lines.append(f"     job starts it runs to completion, limiting the worst case.")
    lines.append(f"  ✦  Quantum = {quantum}: small → more responsive RR; large → approaches FCFS.")

    # ════════════════════════════════════════════════════════════════════════
    # CONCLUSION
    # ════════════════════════════════════════════════════════════════════════
    lines.append("\n" + "─" * 70)
    lines.append("  🏆  CONCLUSION")
    lines.append("─" * 70)

    if three:
        lines.append(f"  • Lowest avg WT:        {wt_w}")
        lines.append(f"  • Lowest avg TAT:       {tat_w}")
        lines.append(f"  • Lowest avg RT:        {rt_w}")
        lines.append(f"  • Most fair (Jain):     {'RR' if rr_fairer else ('SRTF' if srtf_fairer else 'SJF')}")
        lines.append(f"  • Starvation risk:      SRTF > SJF > RR (none)")
        lines.append(f"  • Context-switch cost:  SRTF > RR (q={quantum}) > SJF")
        lines.append(f"\n  When to use each:")
        lines.append(f"    RR   → Interactive / time-sharing OSes; fairness critical.")
        lines.append(f"    SJF  → Batch systems; burst times known; no starvation concern.")
        lines.append(f"    SRTF → Batch systems; preemption allowed; minimise avg WT.")
    else:
        lines.append(f"  • Lower avg WT:         {wt_w}")
        lines.append(f"  • Lower avg TAT:        {tat_w}")
        lines.append(f"  • Lower avg RT:         {rt_w}")
        lines.append(f"  • More balanced (fair): {'RR' if rr_fairer else 'SJF'}")

    lines.append(f"\n  Quantum effect: q={quantum} → max RR first-response ≈{quantum*(n-1)} units,")
    lines.append(f"  ~{context_switches} mid-run preemption(s) estimated for this workload.")
    if quantum <= 3:
        lines.append(f"  Smaller quantum = more responsive RR, higher context-switch overhead.")
    elif quantum >= 10:
        lines.append(f"  Large quantum = RR approaches FCFS; consider reducing for fairness.")
    else:
        lines.append(f"  This quantum strikes a balanced trade-off for this workload.")
    lines.append("═" * 70)

    return "\n".join(lines)


# ─────────────────────────────────────────────
#  SAMPLE TEST DATA
# ─────────────────────────────────────────────

SAMPLE_SETS = {
    "Basic Mixed Workload": [
        ("P1", 0, 10),
        ("P2", 1,  4),
        ("P3", 2,  6),
        ("P4", 3,  2),
        ("P5", 4,  8),
    ],
    "Short-Job-Heavy": [
        ("P1", 0,  2),
        ("P2", 0,  3),
        ("P3", 1,  1),
        ("P4", 2,  2),
        ("P5", 3, 20),
    ],
    "Fairness Case (RR Advantage)": [
        ("P1", 0, 12),
        ("P2", 0, 12),
        ("P3", 0, 12),
        ("P4", 0, 12),
    ],
    "Long-Job Sensitivity": [
        ("P1", 0, 30),
        ("P2", 1,  4),
        ("P3", 2,  6),
        ("P4", 5,  2),
    ],
    "SRTF Preemption Showcase": [
        # P1 starts running at t=0 (burst=8).  P2 arrives at t=1 with burst=4
        # — shorter remaining than P1 (7), so P1 is preempted immediately.
        # This dataset makes SRTF preemption unmistakable in the Gantt chart.
        ("P1", 0,  8),
        ("P2", 1,  4),
        ("P3", 2,  9),
        ("P4", 3,  5),
    ],
}


# ─────────────────────────────────────────────
#  GUI APPLICATION
# ─────────────────────────────────────────────

class SchedulerApp(tk.Tk):
    """Main application window."""

    # ── colour tokens ──────────────────────────
    BG         = "#F0F4F8"
    PANEL      = "#FFFFFF"
    ACCENT     = "#2563EB"
    ACCENT2    = "#7C3AED"
    ACCENT3    = "#059669"    # SRTF — teal/emerald
    HEADER     = "#1E293B"
    TEXT       = "#334155"
    SUBTEXT    = "#64748B"
    BORDER     = "#E2E8F0"
    SUCCESS    = "#16A34A"
    WARNING    = "#D97706"
    ERROR      = "#DC2626"
    TAG_RR     = "#DBEAFE"
    TAG_SJF    = "#EDE9FE"

    def __init__(self):
        super().__init__()
        self.title("CPU Scheduling Simulator — RR vs SJF vs SRTF")
        self.configure(bg=self.BG)
        self.state("zoomed")          # Maximise on launch
        self.minsize(1100, 700)

        self.processes: List[Process] = []   # master list
        self._pid_list: List[str] = []       # ordered pids for colour mapping

        self._build_styles()
        self._build_ui()
        self._apply_sample("Basic Mixed Workload")   # pre-load demo data

    # ─── STYLES ────────────────────────────────

    def _build_styles(self):
        self._style = ttk.Style(self)
        self._style.theme_use("clam")

        # Treeview
        self._style.configure("Proc.Treeview",
                               background=self.PANEL,
                               fieldbackground=self.PANEL,
                               foreground=self.TEXT,
                               rowheight=26,
                               font=("Consolas", 10))
        self._style.configure("Proc.Treeview.Heading",
                               background=self.HEADER,
                               foreground="#FFFFFF",
                               font=("Segoe UI", 10, "bold"),
                               relief="flat")
        self._style.map("Proc.Treeview.Heading",
                        background=[("active", self.ACCENT)])
        self._style.map("Proc.Treeview",
                        background=[("selected", self.ACCENT)],
                        foreground=[("selected", "#FFFFFF")])

        # Notebook tabs
        self._style.configure("TNotebook", background=self.BG, borderwidth=0)
        self._style.configure("TNotebook.Tab",
                               background=self.BORDER,
                               foreground=self.TEXT,
                               padding=(14, 6),
                               font=("Segoe UI", 10))
        self._style.map("TNotebook.Tab",
                        background=[("selected", self.ACCENT)],
                        foreground=[("selected", "#FFFFFF")])

    # ─── MAIN LAYOUT ───────────────────────────

    def _build_ui(self):
        # ── Top banner ─────────────────────────
        banner = tk.Frame(self, bg=self.HEADER, height=56)
        banner.pack(fill="x")
        banner.pack_propagate(False)

        tk.Label(banner,
                 text="⚙  CPU Scheduling Simulator",
                 bg=self.HEADER, fg="#FFFFFF",
                 font=("Segoe UI", 17, "bold")).pack(side="left", padx=24, pady=12)

        tk.Label(banner,
                 text="Round Robin  vs  SJF  vs  SRTF (Preemptive SJF)",
                 bg=self.HEADER, fg="#94A3B8",
                 font=("Segoe UI", 11)).pack(side="left", padx=4, pady=12)

        # ── Main body: left panel + right notebook ─
        body = tk.Frame(self, bg=self.BG)
        body.pack(fill="both", expand=True, padx=0, pady=0)

        self._build_left_panel(body)
        self._build_right_panel(body)

    # ─── LEFT INPUT PANEL ──────────────────────

    def _build_left_panel(self, parent):
        left = tk.Frame(parent, bg=self.PANEL, width=310,
                        bd=0, relief="flat",
                        highlightbackground=self.BORDER,
                        highlightthickness=1)
        left.pack(side="left", fill="y", padx=0, pady=0)
        left.pack_propagate(False)

        # ── Section header ─
        self._section_label(left, "➕  Add Process")

        form = tk.Frame(left, bg=self.PANEL, padx=16, pady=4)
        form.pack(fill="x")

        self._pid_var     = tk.StringVar()
        self._arrival_var = tk.StringVar()
        self._burst_var   = tk.StringVar()
        self._quantum_var = tk.StringVar(value="3")

        fields = [
            ("Process ID",    self._pid_var),
            ("Arrival Time",  self._arrival_var),
            ("Burst Time",    self._burst_var),
        ]
        for label, var in fields:
            self._field(form, label, var)

        # Quantum field (special background)
        qf = tk.Frame(form, bg=self.PANEL)
        qf.pack(fill="x", pady=(8, 2))
        tk.Label(qf, text="Time Quantum (RR)", bg=self.PANEL,
                 fg=self.SUBTEXT, font=("Segoe UI", 9)).pack(anchor="w")
        tk.Entry(qf, textvariable=self._quantum_var,
                 font=("Consolas", 11), bd=1, relief="solid",
                 bg="#EFF6FF", fg=self.ACCENT,
                 insertbackground=self.ACCENT,
                 highlightthickness=0).pack(fill="x", ipady=5)

        # Buttons
        btn_frame = tk.Frame(left, bg=self.PANEL, padx=16, pady=8)
        btn_frame.pack(fill="x")

        self._btn(btn_frame, "Add Process", self._add_process,
                  self.ACCENT, "#FFFFFF").pack(fill="x", pady=(0, 6))

        self._btn(btn_frame, "▶  Run Simulation", self._run_simulation,
                  self.SUCCESS, "#FFFFFF").pack(fill="x", pady=(0, 6))

        self._btn(btn_frame, "🗑  Clear All", self._clear_all,
                  "#EF4444", "#FFFFFF").pack(fill="x")

        # ── Sample data loader ─
        self._section_label(left, "📋  Load Sample Dataset")

        sf = tk.Frame(left, bg=self.PANEL, padx=16, pady=4)
        sf.pack(fill="x")

        for name in SAMPLE_SETS:
            short = name.split("(")[0].strip()
            self._btn(sf, short,
                      lambda n=name: self._apply_sample(n),
                      "#F8FAFC", self.TEXT,
                      bd=1, relief="solid",
                      activebackground=self.BORDER).pack(fill="x", pady=2)

        # Scenario E — Validation demo (Gap 2 requirement)
        # Loads an invalid input into the form fields and triggers validation
        # so students can see the error-handling behaviour in action.
        self._btn(sf, "⚠  Scenario E: Validation Demo",
                  self._run_validation_demo,
                  "#FEF3C7", "#92400E",
                  bd=1, relief="solid",
                  activebackground="#FDE68A").pack(fill="x", pady=2)

        # ── Process table ─
        self._section_label(left, "📄  Process Queue")

        tv_frame = tk.Frame(left, bg=self.PANEL, padx=8, pady=4)
        tv_frame.pack(fill="both", expand=True)

        cols = ("pid", "arrival", "burst")
        self._proc_tv = ttk.Treeview(tv_frame, columns=cols,
                                      show="headings", style="Proc.Treeview",
                                      height=10)
        for col, hdr, w in [("pid","PID",60),("arrival","Arrive",60),("burst","Burst",60)]:
            self._proc_tv.heading(col, text=hdr)
            self._proc_tv.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(tv_frame, orient="vertical",
                             command=self._proc_tv.yview)
        self._proc_tv.configure(yscrollcommand=vsb.set)
        self._proc_tv.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Delete selected process
        del_btn = tk.Frame(left, bg=self.PANEL, padx=16, pady=4)
        del_btn.pack(fill="x")
        self._btn(del_btn, "Remove Selected",
                  self._remove_selected,
                  "#F1F5F9", self.ERROR,
                  bd=1, relief="solid").pack(fill="x")

    # ─── RIGHT RESULTS PANEL ───────────────────

    def _build_right_panel(self, parent):
        right = tk.Frame(parent, bg=self.BG)
        right.pack(side="left", fill="both", expand=True, padx=0, pady=0)

        self._notebook = ttk.Notebook(right)
        self._notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # ── Tabs ──
        self._tab_rr   = self._make_tab("🔵  Round Robin")
        self._tab_sjf  = self._make_tab("🟣  SJF")
        self._tab_srtf = self._make_tab("🟢  SRTF")
        self._tab_cmp  = self._make_tab("📊  Comparison")

        self._build_algo_tab(self._tab_rr,   "rr")
        self._build_algo_tab(self._tab_sjf,  "sjf")
        self._build_algo_tab(self._tab_srtf, "srtf")
        self._build_comparison_tab(self._tab_cmp)

    def _make_tab(self, label: str) -> tk.Frame:
        frame = tk.Frame(self._notebook, bg=self.BG)
        self._notebook.add(frame, text=label)
        return frame

    def _build_algo_tab(self, parent: tk.Frame, algo: str):
        """Build Gantt + results table section for one algorithm."""
        # Store refs so we can update later
        store = {}

        # ── Gantt section ─
        # Choose accent colour per algorithm
        if algo == "rr":
            gantt_fg = self.ACCENT
        elif algo == "sjf":
            gantt_fg = self.ACCENT2
        else:                       # srtf
            gantt_fg = self.ACCENT3

        gantt_frame = tk.LabelFrame(parent,
                                    text="  Gantt Chart  ",
                                    bg=self.PANEL,
                                    fg=gantt_fg,
                                    font=("Segoe UI", 10, "bold"),
                                    bd=1, relief="solid",
                                    labelanchor="nw")
        gantt_frame.pack(fill="x", padx=10, pady=(10, 4))

        h_scroll = tk.Scrollbar(gantt_frame, orient="horizontal")
        canvas = tk.Canvas(gantt_frame, bg=self.PANEL,
                           height=140, bd=0,
                           xscrollcommand=h_scroll.set,
                           highlightthickness=0)
        canvas.configure(width=800)
        h_scroll.configure(command=canvas.xview)
        canvas.pack(fill="x", expand=True)
        h_scroll.pack(fill="x")
        store["canvas"] = canvas

        # ── Metrics table ─
        tbl_frame = tk.LabelFrame(parent,
                                  text="  Process Metrics  ",
                                  bg=self.PANEL,
                                  fg=self.TEXT,
                                  font=("Segoe UI", 10, "bold"),
                                  bd=1, relief="solid",
                                  labelanchor="nw")
        tbl_frame.pack(fill="both", expand=True, padx=10, pady=(4, 6))

        cols = ("pid", "arrival", "burst", "wt", "tat", "rt")
        hdrs = ("PID", "Arrival", "Burst", "Wait Time", "Turnaround", "Response")
        tv = ttk.Treeview(tbl_frame, columns=cols, show="headings",
                          style="Proc.Treeview", height=8)
        for col, hdr in zip(cols, hdrs):
            tv.heading(col, text=hdr)
            tv.column(col, width=100, anchor="center")

        vsb = ttk.Scrollbar(tbl_frame, orient="vertical", command=tv.yview)
        tv.configure(yscrollcommand=vsb.set)
        tv.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        store["tv"] = tv

        # ── Ready Queue View (Round Robin only) ─────────────────────────────
        # Shows each scheduling decision: which process ran, what was waiting.
        # Required interface section: "Ready Queue View for Round Robin".
        if algo == "rr":
            rq_frame = tk.LabelFrame(parent,
                                     text="  Ready Queue Trace (per scheduling decision)  ",
                                     bg=self.PANEL,
                                     fg=self.ACCENT,
                                     font=("Segoe UI", 10, "bold"),
                                     bd=1, relief="solid",
                                     labelanchor="nw")
            rq_frame.pack(fill="x", padx=10, pady=(4, 2))

            rq_cols = ("time", "running", "queue")
            rq_hdrs = ("Time", "Running", "Ready Queue  (front → back)")
            rq_tv = ttk.Treeview(rq_frame, columns=rq_cols, show="headings",
                                  style="Proc.Treeview", height=5)
            rq_tv.heading("time",    text="Time")
            rq_tv.heading("running", text="Running")
            rq_tv.heading("queue",   text="Ready Queue  (front → back)")
            rq_tv.column("time",    width=60,  anchor="center")
            rq_tv.column("running", width=80,  anchor="center")
            rq_tv.column("queue",   width=400, anchor="w")

            rq_vsb = ttk.Scrollbar(rq_frame, orient="vertical", command=rq_tv.yview)
            rq_tv.configure(yscrollcommand=rq_vsb.set)
            rq_tv.pack(side="left", fill="x", expand=True)
            rq_vsb.pack(side="right", fill="y")
            store["rq_tv"] = rq_tv

        # ── Averages bar ─
        avg_bar = tk.Frame(parent, bg=self.PANEL,
                           highlightbackground=self.BORDER,
                           highlightthickness=1)
        avg_bar.pack(fill="x", padx=10, pady=(0, 6))

        store["avg_wt"]  = tk.StringVar(value="—")
        store["avg_tat"] = tk.StringVar(value="—")
        store["avg_rt"]  = tk.StringVar(value="—")

        for lbl, var, col in [
            ("Avg Wait Time",   store["avg_wt"],  self.ACCENT),
            ("Avg Turnaround",  store["avg_tat"], self.SUCCESS),
            ("Avg Response",    store["avg_rt"],  self.WARNING),
        ]:
            cell = tk.Frame(avg_bar, bg=self.PANEL, padx=20, pady=8)
            cell.pack(side="left", expand=True)
            tk.Label(cell, textvariable=var, bg=self.PANEL,
                     fg=col, font=("Consolas", 15, "bold")).pack()
            tk.Label(cell, text=lbl, bg=self.PANEL,
                     fg=self.SUBTEXT, font=("Segoe UI", 9)).pack()

        if algo == "rr":
            self._rr_store = store
        elif algo == "sjf":
            self._sjf_store = store
        else:
            self._srtf_store = store

    def _build_comparison_tab(self, parent: tk.Frame):
        """Build the comparison & conclusion section."""
        self._cmp_text = tk.Text(parent,
                                  font=("Consolas", 10),
                                  bg=self.PANEL,
                                  fg=self.TEXT,
                                  bd=0,
                                  relief="flat",
                                  wrap="word",
                                  padx=18, pady=14,
                                  state="disabled")
        vsb = ttk.Scrollbar(parent, orient="vertical",
                             command=self._cmp_text.yview)
        self._cmp_text.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._cmp_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Colour tags inside the text widget
        self._cmp_text.tag_configure("header", foreground=self.ACCENT,
                                      font=("Consolas", 11, "bold"))
        self._cmp_text.tag_configure("win",    foreground=self.SUCCESS,
                                      font=("Consolas", 10, "bold"))
        self._cmp_text.tag_configure("normal", foreground=self.TEXT)

    # ─── WIDGET HELPERS ────────────────────────

    def _section_label(self, parent, text: str):
        frm = tk.Frame(parent, bg=self.BORDER, height=1)
        frm.pack(fill="x", pady=(14, 0))
        tk.Label(parent, text=text, bg=self.PANEL,
                 fg=self.HEADER,
                 font=("Segoe UI", 10, "bold"),
                 padx=16, pady=4).pack(fill="x")

    def _field(self, parent, label: str, var: tk.StringVar):
        frm = tk.Frame(parent, bg=self.PANEL, pady=3)
        frm.pack(fill="x")
        tk.Label(frm, text=label, bg=self.PANEL,
                 fg=self.SUBTEXT, font=("Segoe UI", 9)).pack(anchor="w")
        tk.Entry(frm, textvariable=var,
                 font=("Consolas", 11), bd=1, relief="solid",
                 bg="#F8FAFC", fg=self.HEADER,
                 insertbackground=self.ACCENT,
                 highlightthickness=0).pack(fill="x", ipady=5)

    def _btn(self, parent, text: str, cmd, bg: str, fg: str, **kw) -> tk.Button:
        return tk.Button(parent, text=text, command=cmd,
                         bg=bg, fg=fg,
                         font=("Segoe UI", 10, "bold"),
                         relief=kw.pop("relief", "flat"),
                         bd=kw.pop("bd", 0),
                         activebackground=kw.pop("activebackground", "#E2E8F0"),
                         activeforeground=fg,
                         cursor="hand2",
                         padx=6, pady=7,
                         **kw)

    # ─── PROCESS MANAGEMENT ────────────────────

    def _add_process(self):
        existing = [p.pid for p in self.processes]
        try:
            pid, arrival, burst = validate_process_inputs(
                self._pid_var.get(),
                self._arrival_var.get(),
                self._burst_var.get(),
                existing
            )
        except ValidationError as e:
            messagebox.showerror("Input Error", str(e))
            return

        proc = Process(pid, arrival, burst)
        self.processes.append(proc)
        self._pid_list.append(pid)
        self._refresh_proc_table()

        # Clear form fields
        self._pid_var.set("")
        self._arrival_var.set("")
        self._burst_var.set("")

    def _remove_selected(self):
        sel = self._proc_tv.selection()
        if not sel:
            messagebox.showinfo("Remove", "No process selected.")
            return
        for item in sel:
            pid = self._proc_tv.item(item, "values")[0]
            self.processes = [p for p in self.processes if p.pid != pid]
            if pid in self._pid_list:
                self._pid_list.remove(pid)
        self._refresh_proc_table()

    def _clear_all(self):
        self.processes.clear()
        self._pid_list.clear()
        self._refresh_proc_table()
        # Reset displays
        for store in (self._rr_store, self._sjf_store, self._srtf_store):
            store["canvas"].delete("all")
            store["tv"].delete(*store["tv"].get_children())
            store["avg_wt"].set("—")
            store["avg_tat"].set("—")
            store["avg_rt"].set("—")
        # Clear Ready Queue trace (RR only)
        if "rq_tv" in self._rr_store:
            self._rr_store["rq_tv"].delete(*self._rr_store["rq_tv"].get_children())
        self._cmp_text.config(state="normal")
        self._cmp_text.delete("1.0", "end")
        self._cmp_text.config(state="disabled")

    def _refresh_proc_table(self):
        """Redraw the input process treeview."""
        tv = self._proc_tv
        tv.delete(*tv.get_children())
        for p in self.processes:
            tv.insert("", "end", values=(p.pid, p.arrival, p.burst))

    def _apply_sample(self, name: str):
        """Load one of the pre-defined sample datasets."""
        self._clear_all()
        for pid, arr, bst in SAMPLE_SETS[name]:
            self.processes.append(Process(pid, arr, bst))
            self._pid_list.append(pid)
        self._refresh_proc_table()

    def _run_validation_demo(self):
        """
        Scenario E – Validation Case (Gap 2).

        Sequentially demonstrates every category of invalid input by pre-filling
        the form with bad values and calling the validator, displaying each error
        message so students can observe the validation behaviour without having
        to type bad data themselves.
        """
        demos = [
            # (pid, arrival, burst, quantum, description)
            ("",    "0",  "5",  "3",  "Empty Process ID"),
            ("P1",  "-1", "5",  "3",  "Negative Arrival Time"),
            ("P1",  "0",  "0",  "3",  "Zero Burst Time"),
            ("P1",  "0",  "-3", "3",  "Negative Burst Time"),
            ("P1",  "0",  "5",  "0",  "Zero Time Quantum"),
            ("P1",  "0",  "5",  "-2", "Negative Time Quantum"),
            ("P1",  "abc","5",  "3",  "Non-integer Arrival Time"),
            ("P1",  "0",  "xyz","3",  "Non-integer Burst Time"),
        ]
        # If any process already exists with PID "P1" we can also demo duplicate
        existing_pids = [p.pid for p in self.processes]
        if "P1" in existing_pids:
            demos.insert(0, ("P1", "0", "5", "3", "Duplicate Process ID"))

        results = []
        for pid, arr, bst, q, desc in demos:
            # Test process-field validation
            try:
                validate_process_inputs(pid, arr, bst, existing_pids)
                proc_result = "✅  ACCEPTED (no error)"
            except ValidationError as e:
                proc_result = f"❌  {e}"

            # Test quantum validation separately for quantum-specific cases
            q_result = ""
            if proc_result.startswith("✅"):
                try:
                    validate_quantum(q)
                    q_result = ""
                except ValidationError as e:
                    q_result = f"  |  Quantum error: {e}"

            results.append(f"  [{desc}]\n    Input: PID='{pid}' Arrival='{arr}' "
                           f"Burst='{bst}' Quantum='{q}'\n"
                           f"    Result: {proc_result}{q_result}")

        msg = ("Scenario E — Validation Case\n"
               "════════════════════════════════════════\n\n"
               + "\n\n".join(results)
               + "\n\n════════════════════════════════════════\n"
               "All invalid inputs above are correctly REJECTED by the validator.\n"
               "Only well-formed inputs (positive integers, unique IDs,\n"
               "non-negative arrival, quantum > 0) are accepted.")
        messagebox.showinfo("Scenario E — Validation Demo", msg)

    # ─── SIMULATION ────────────────────────────

    def _run_simulation(self):
        if len(self.processes) < 1:
            messagebox.showwarning("No Processes", "Please add at least one process.")
            return

        # Validate quantum
        try:
            quantum = validate_quantum(self._quantum_var.get())
        except ValidationError as e:
            messagebox.showerror("Quantum Error", str(e))
            return

        pid_list = [p.pid for p in self.processes]

        # ── Run algorithms ─
        rr_procs,   rr_gantt,  rr_queue_history = schedule_rr(self.processes, quantum)
        sjf_procs,  sjf_gantt                   = schedule_sjf(self.processes)
        srtf_procs, srtf_gantt                  = schedule_srtf(self.processes)

        rr_avg   = compute_averages(rr_procs)
        sjf_avg  = compute_averages(sjf_procs)
        srtf_avg = compute_averages(srtf_procs)
        rr_fair   = fairness_index(rr_procs)
        sjf_fair  = fairness_index(sjf_procs)
        srtf_fair = fairness_index(srtf_procs)

        # ── Update RR tab ─
        self._update_algo_display(
            self._rr_store, rr_procs, rr_gantt, rr_avg, pid_list,
            f"Round Robin  (Quantum = {quantum})",
            rq_history=rr_queue_history
        )

        # ── Update SJF tab ─
        self._update_algo_display(
            self._sjf_store, sjf_procs, sjf_gantt, sjf_avg, pid_list,
            "Shortest Job First  (Non-Preemptive)"
        )

        # ── Update SRTF tab ─
        self._update_algo_display(
            self._srtf_store, srtf_procs, srtf_gantt, srtf_avg, pid_list,
            "SRTF  (Shortest Remaining Time First — Preemptive SJF)"
        )

        # ── Update comparison tab ─
        report = generate_comparison(
            rr_procs,   rr_avg,   rr_fair,
            sjf_procs,  sjf_avg,  sjf_fair,
            quantum,
            srtf_procs, srtf_avg, srtf_fair
        )
        self._cmp_text.config(state="normal")
        self._cmp_text.delete("1.0", "end")
        self._cmp_text.insert("end", report)
        self._cmp_text.config(state="disabled")

        # Switch to RR tab to show results
        self._notebook.select(0)

    def _update_algo_display(self, store: dict,
                              procs: List[Process],
                              gantt: List[Tuple[str, int, int]],
                              avgs: Dict[str, float],
                              pid_list: List[str],
                              title: str,
                              rq_history: List[Tuple[int, str, List[str]]] = None):
        """Refresh Gantt + table + averages (+ Ready Queue for RR) for one algorithm."""
        # Gantt
        self.update_idletasks()
        draw_gantt(store["canvas"], gantt, pid_list, title)

        # Table
        tv = store["tv"]
        tv.delete(*tv.get_children())
        for p in sorted(procs, key=lambda x: x.pid):
            tv.insert("", "end",
                      values=(p.pid, p.arrival, p.burst,
                               p.waiting_time, p.turnaround_time,
                               p.response_time))

        # Averages
        store["avg_wt"].set(f"{avgs['avg_wt']:.2f}")
        store["avg_tat"].set(f"{avgs['avg_tat']:.2f}")
        store["avg_rt"].set(f"{avgs['avg_rt']:.2f}")

        # ── Ready Queue View (RR only) ──────────────────────────────────────
        # Populated from rq_history: each row is one scheduling-decision
        # snapshot showing what time it was, which process had the CPU, and
        # which processes were lined up behind it in the ready queue.
        if rq_history is not None and "rq_tv" in store:
            rq_tv = store["rq_tv"]
            rq_tv.delete(*rq_tv.get_children())
            for t, running, queued in rq_history:
                queue_str = " → ".join(queued) if queued else "(empty)"
                rq_tv.insert("", "end", values=(f"t={t}", running, queue_str))


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app = SchedulerApp()
    app.mainloop()
