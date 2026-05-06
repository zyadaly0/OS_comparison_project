# ⚙ CPU Scheduling Simulator — RR vs SJF vs SRTF

A fully interactive Python/Tkinter desktop application that simulates and compares
**three** CPU scheduling algorithms — **Round Robin (RR)**, **Shortest Job First (SJF)**,
and **Shortest Remaining Time First (SRTF)** — side-by-side on the same process dataset.


---

## 📁 Project Structure

```
cpu_scheduler/
├── scheduler.py               ← Main GUI application (all-in-one, 1 547 lines)
├── generate_report.py         ← Standalone PDF report generator
├── cpu_scheduling_report.pdf  ← Pre-generated 15-page academic report
└── README.md                  ← This file
```

---

## 🚀 How to Run

### Prerequisites
- Python 3.8 or higher
- Tkinter (bundled with standard Python on Windows & macOS)


## 🖥 GUI Walkthrough

| Area | Description |
|------|-------------|
| **Left Panel** | Add processes, set quantum, load sample data, manage process queue |
| **Round Robin Tab** 🔵 | Gantt chart + Ready Queue Trace + metrics table + averages |
| **SJF Tab** 🟣 | Gantt chart + per-process metrics table + averages |
| **SRTF Tab** 🟢 | Gantt chart + per-process metrics table + averages |
| **Comparison Tab** 📊 | Full auto-generated 3-algorithm analysis report |

### Adding a Process
1. Fill in **Process ID** (e.g. `P1`), **Arrival Time**, **Burst Time**
2. Click **Add Process**
3. Repeat for all processes
4. Set **Time Quantum** for Round Robin (default = 3)
5. Click **▶ Run Simulation**

### Sample Datasets
Click any preset button on the left panel to instantly load a test scenario:

| Button | Scenario |
|--------|----------|
| Basic Mixed Workload | Scenario A — general comparison dataset |
| Short-Job-Heavy | Scenario B — highlights SJF/SRTF short-job preference |
| Fairness Case (RR Advantage) | Scenario C — equal burst times, RR is perfectly fair |
| Long-Job Sensitivity | Scenario D — one very long job competing with short ones |
| ⚠ Scenario E: Validation Demo | Demonstrates all invalid-input rejection cases |
| SRTF Preemption Showcase | Scenario E (scheduling) — makes SRTF preemption unmistakable |

---

## 🧠 Algorithm Explanations

### Round Robin (RR)
Each process gets a fixed **time quantum** on the CPU before being preempted
and moved to the back of the ready queue. This continues until all processes finish.

- **Arrival times** are respected — processes join the queue only after they arrive.
- **Fair**: no process is ever starved; every process rotates through within each cycle.
- **Context switch overhead** increases as quantum decreases.
- **Ready Queue Trace** panel shows the queue state at every scheduling decision.
- Best for: **time-sharing, interactive systems**.

**Key steps:**
```
1. Sort processes by arrival time
2. Maintain a FIFO ready queue
3. Run front of queue for min(quantum, remaining_burst)
4. After each quantum, admit newly arrived processes, then re-queue if not done
5. Repeat until all complete
```

---

### Shortest Job First (SJF) — Non-Preemptive
When the CPU is free, select the **available** process with the **shortest burst time**.
Once a process starts, it runs to completion — it cannot be interrupted.

- **Optimal** average waiting time among non-preemptive algorithms.
- Can cause **starvation**: long jobs may wait indefinitely if short jobs keep arriving.
- Requires knowing burst times in advance (impractical in pure form).
- Best for: **batch processing** where job lengths are known.

**Key steps:**
```
1. When CPU is free, find all arrived, unfinished processes
2. Select the one with minimum burst time (tie → earliest arrival → smallest PID)
3. Run it to completion
4. Repeat
```

---

### SRTF — Shortest Remaining Time First (Preemptive SJF)
At **every time unit** the scheduler picks the process with the shortest
**remaining** burst time. If a newly arrived process is shorter than the
currently running one, it **preempts** it immediately.

- **Theoretically optimal** — minimises average waiting time among all preemptive policies.
- **Highest starvation risk** — long jobs can be blocked indefinitely by a stream of
  short arrivals.
- Gantt chart is the most fragmented (each preemption creates a new bar).
- Context-switch count is higher than RR or SJF.
- Best for: **batch systems** where minimising average wait is paramount and
  preemption is acceptable.

**Key steps:**
```
1. Advance time one unit at a time
2. Find all arrived, unfinished processes
3. Run the one with the shortest remaining time for exactly 1 unit
   (tie → earliest arrival → smallest PID)
4. On completion, record finish / TAT / WT
5. Merge consecutive 1-unit slices of the same PID into one Gantt block
6. Repeat until all processes finish
```

---

## 📊 Metrics Explained

| Metric | Formula |
|--------|---------|
| **Turnaround Time (TAT)** | Finish Time − Arrival Time |
| **Waiting Time (WT)** | TAT − Burst Time |
| **Response Time (RT)** | First CPU Start − Arrival Time |

**Averages** are the arithmetic mean across all processes.

**Fairness Index** (Jain's): values closer to **1.0** indicate more equal
distribution of CPU time among processes.

```
J = (Σ wᵢ)² / (n × Σ wᵢ²)
```

---

## 🧪 Test Scenarios Included

| Label | Scenario | Purpose |
|-------|----------|---------|
| A | Basic Mixed Workload | General comparison — varied burst times, staggered arrivals |
| B | Short-Job-Heavy | SJF/SRTF short-job preference very visible; starvation risk for P5 |
| C | Fairness Case | Equal burst times — RR distributes perfectly; SJF ≡ FCFS here |
| D | Long-Job Sensitivity | Long P1 vs short jobs — SRTF penalises P1 most severely |
| E | SRTF Preemption Showcase | P1 runs t=0→1, P2 preempts at t=1, preemption is unmistakable |

### Validation Demo (⚠ Scenario E button)
Clicking **⚠ Scenario E: Validation Demo** runs all 8 invalid-input categories
through the validator and shows a popup with every rejection message:

| Invalid Input | Error Shown |
|---------------|-------------|
| Empty Process ID | "Process ID cannot be empty" |
| Duplicate Process ID | "Duplicate Process ID 'P1'" |
| Negative Arrival Time | "Arrival Time cannot be negative" |
| Zero Burst Time | "Burst Time must be greater than zero" |
| Negative Burst Time | "Burst Time must be greater than zero" |
| Zero Quantum | "Time Quantum must be greater than zero" |
| Negative Quantum | "Time Quantum must be greater than zero" |
| Non-integer values | "must be a … integer" |

---

## 📈 Trade-offs: RR vs SJF vs SRTF

```
┌─────────────────────┬──────────────────┬──────────────────────┬──────────────────────┐
│ Property            │ Round Robin      │ SJF (Non-Preemptive) │ SRTF (Preemptive)    │
├─────────────────────┼──────────────────┼──────────────────────┼──────────────────────┤
│ Preemptive?         │ Yes (time-based) │ No                   │ Yes (length-based)   │
│ Avg Waiting Time    │ Moderate         │ Near-optimal         │ Optimal (minimum)    │
│ Avg Response Time   │ Low (≤ quantum)  │ High for long jobs   │ Low for short jobs   │
│ Fairness            │ High             │ Medium               │ Low                  │
│ Starvation Risk     │ None             │ Possible             │ Highest              │
│ Context Switches    │ Many (quantum)   │ Few                  │ Many (arrivals)      │
│ Practicality        │ High             │ Medium               │ Medium               │
│ Best Use Case       │ Interactive / OS │ Batch / known bursts │ Batch / min avg WT   │
└─────────────────────┴──────────────────┴──────────────────────┴──────────────────────┘
```

**Effect of Quantum on RR:**
- **Small quantum** → more responsive, more context switches, higher overhead
- **Large quantum** → approaches FCFS behaviour, less fair

**SRTF vs SJF:**
- SRTF always achieves average waiting time ≤ SJF (verified across all 5 test scenarios)
- SRTF fragments the Gantt chart more — each new arrival may trigger a preemption
- SJF is simpler with no mid-execution interruptions once a job starts

---

## 🏗 Code Architecture

```
scheduler.py  (1 547 lines)
│
├── ── DATA MODEL ──────────────────────────────────────────────────────────────
│   └── Process (dataclass)         pid, arrival, burst + computed metrics
│                                   clone() creates a fresh copy per algorithm run
│
├── ── VALIDATION ──────────────────────────────────────────────────────────────
│   ├── ValidationError             Custom exception class
│   ├── validate_process_inputs()   Checks PID, arrival, burst, duplicates
│   └── validate_quantum()          Checks quantum > 0
│
├── ── SCHEDULING ALGORITHMS ───────────────────────────────────────────────────
│   ├── schedule_rr(procs, q)       Round Robin → (procs, gantt, rq_history)
│   ├── schedule_sjf(procs)         SJF Non-Preemptive → (procs, gantt)
│   └── schedule_srtf(procs)        SRTF Preemptive → (procs, gantt)    ★ NEW
│
├── ── METRICS ─────────────────────────────────────────────────────────────────
│   ├── compute_averages(procs)     Returns avg WT / TAT / RT
│   └── fairness_index(procs)       Jain's Fairness Index
│
├── ── GANTT CHART ─────────────────────────────────────────────────────────────
│   ├── pid_color()                 Stable colour per PID
│   └── draw_gantt()                Cumulative-timeline Canvas renderer
│                                   (idle gaps → grey IDLE blocks, scrollable)
│
├── ── COMPARISON ──────────────────────────────────────────────────────────────
│   └── generate_comparison()       3-algorithm report with 6 Q&A sections,
│                                   long-process table, SRTF observations,
│                                   metric verdict, recommendation         ★ UPDATED
│
├── ── SAMPLE DATA ─────────────────────────────────────────────────────────────
│   └── SAMPLE_SETS (dict)          Scenarios A–E incl. SRTF Showcase      ★ UPDATED
│
└── ── GUI ─────────────────────────────────────────────────────────────────────
    └── SchedulerApp (tk.Tk)
        ├── _build_left_panel()     Input form, sample buttons, process table
        ├── _build_right_panel()    4-tab notebook: RR | SJF | SRTF | Cmp   ★ UPDATED
        ├── _build_algo_tab()       Gantt + Ready Queue (RR) + metrics table ★ UPDATED
        ├── _build_comparison_tab() Scrollable comparison text view
        ├── _run_validation_demo()  Scenario E popup (8 invalid-input cases)
        ├── _add_process()          Validate + append to process list
        ├── _remove_selected()      Delete highlighted row from queue
        ├── _clear_all()            Reset all three algorithm displays        ★ UPDATED
        ├── _run_simulation()       Run RR + SJF + SRTF, refresh all tabs    ★ UPDATED
        └── _update_algo_display()  Refresh Gantt + table + averages + RQ


## 📸 Expected Output Description

### Round Robin Tab 🔵
- Colour-coded Gantt bar chart with cumulative time markers and horizontal scroll
- **Ready Queue Trace table** — `Time | Running | Ready Queue (front→back)` —
  one row per scheduling decision showing exactly who was waiting at each moment
- Per-process metrics: `PID | Arrival | Burst | Wait Time | Turnaround | Response`
- Three highlighted averages: Avg WT / Avg TAT / Avg RT

### SJF Tab 🟣
- Gantt bars are longer and fewer (non-preemptive — each bar = full burst time)
- Shorter jobs appear earlier regardless of arrival order
- Same metrics table and averages layout as RR tab

### SRTF Tab 🟢 ← NEW
- Gantt chart shows more segments than SJF — each split marks a preemption point
- Bars are shorter on average; the most fragmented chart of the three
- Same metrics table and averages layout

### Comparison Tab 📊 (updated for 3 algorithms)
```
══════════════════════════════════════════════════════════════════════════
  📊  COMPARISON & ANALYSIS REPORT
       Round Robin  |  SJF (Non-Preemptive)  |  SRTF (Preemptive SJF)
══════════════════════════════════════════════════════════════════════════

  Metric                       RR       SJF      SRTF      Best
  ─────────────────────────  ──────── ──────── ──────── ────────
  Avg Waiting Time             13.60    10.00     7.20     SRTF
  Avg Turnaround               19.60    16.00    13.20     SRTF
  Avg Response Time             4.40    10.00     3.20     SRTF

  Fairness (Jain):   RR=0.9049   SJF=0.7246   SRTF=0.5082

  🔍  ANALYSIS QUESTIONS
  Q1. Which algorithm gave lower average waiting time?      → SRTF
  Q2. Which algorithm gave lower average response time?     → SRTF
  Q3. Did Round Robin appear fairer?                        → YES (0.9049)
  Q4. Did SJF complete short jobs more efficiently?         → YES
  Q5. How did the chosen quantum affect Round Robin?        → ...
  Q6. Which algorithm is recommended for this workload?     → ...

  🐘  LONG-PROCESS TREATMENT ANALYSIS  (3-column RR | SJF | SRTF table)
  ⚡  SRTF-SPECIFIC OBSERVATIONS        (preemption mechanics, starvation)
  🔍  KEY OBSERVATIONS
  🏆  CONCLUSION                         (per-metric bullet list)
```

---

## 📄 PDF Report Contents

The pre-built `cpu_scheduling_report.pdf` (15 pages) covers:

| # | Section | Content |
|---|---------|---------|
| — | Title Page | Dark navy cover with subtitle and blue accent stripe |
| — | Table of Contents | All 9 sections listed |
| 1 | Introduction | Scheduling motivation, 5 evaluation dimensions |
| 2 | Algorithm Overview | RR, SJF, SRTF — properties, key steps, when to use each |
| 3 | Implementation | Code architecture, validation rules table |
| 4 | Test Datasets | All 5 scenarios (A–E) with process tables |
| 5 | Simulation Results | Per-process tables + 3-algorithm averages comparison |
| 6 | Gantt Chart Analysis | 4 Gantt charts rendered inline with explanations |
| 7 | Comparative Analysis | Performance table, trade-off matrix, quantum effect |
| 8 | Fairness & Starvation | Jain's index table, per-algorithm starvation analysis |
| 9 | Conclusion | Per-metric verdict table, when-to-use guide, final summary |

To regenerate the report after changing datasets or algorithms:
```bash
python generate_report.py
```

---

## 🎓 Learning Objectives

After running this simulator you should understand:

1. How arrival times complicate scheduling decisions for all three algorithms
2. Why RR is preferred for interactive systems (bounded response time, no starvation)
3. Why SJF minimises average waiting time optimally among non-preemptive policies
4. Why SRTF minimises average waiting time optimally among **all** preemptive policies
5. The starvation risk progression: **RR (none) → SJF (possible) → SRTF (highest)**
6. How quantum size affects RR's fairness, response time, and context-switch overhead
7. What SRTF preemption looks like in a Gantt chart vs SJF's uninterrupted bars
8. How to interpret Jain's Fairness Index and what a value near 1.0 means
9. Why no single algorithm is universally best — the right choice depends on workload

---

## 🔬 Verified Test Results (5 scenarios × 3 algorithms = 15 combinations)

| Scenario | RR AvgWT | SJF AvgWT | SRTF AvgWT | SRTF optimal? |
|----------|:--------:|:---------:|:----------:|:-------------:|
| A — Basic Mixed | 13.60 | 10.00 | **7.20** | ✅ |
| B — Short-Heavy | 3.00 | 2.40 | **2.40** | ✅ tie |
| C — Fairness | 31.50 | 18.00 | **18.00** | ✅ tie |
| D — Long-Sensitive | 9.75 | 22.50 | **4.25** | ✅ |
| E — SRTF Showcase | 13.50 | 7.75 | **6.50** | ✅ |

SRTF average waiting time ≤ SJF average waiting time on **every** scenario,
confirming its theoretical optimality for the preemptive case.

All 15 combinations also pass:
- WT ≥ 0 for every process
- TAT ≥ burst time for every process
- RT ≥ 0 for every process
- Gantt timeline is strictly cumulative (no time resets, no backward jumps)
- SRTF Scenario E: P1 runs t=0→1, P2 preempts exactly at t=1 ✅
