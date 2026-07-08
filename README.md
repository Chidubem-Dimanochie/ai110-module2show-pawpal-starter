# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Running `python main.py` builds a schedule for an owner with two pets and a
60-minute daily budget. The scheduler pulls tasks across all pets, fits the
highest-priority ones that stay within the budget, and lists the rest under
"Skipped" so it's clear *why* they didn't make the plan:

```
========================================
Today's Schedule for Jordan
========================================
Daily plan (60 min available):
  - Litter box (8 min) [priority: high]
  - Feeding (10 min) [priority: high]
  - Morning walk (30 min) [priority: high]
Skipped (not enough time):
  - Play/enrichment (15 min) [priority: medium]
  - Grooming (25 min) [priority: low]
```

## 🧪 Testing PawPal+

Run the full test suite from the project root:

```bash
python -m pytest
```

### What the tests cover

The 27 tests in `tests/test_pawpal.py` exercise the logic layer in
`pawpal_system.py` across happy paths and edge cases:

- **Sorting correctness** — tasks come back in chronological order by
  `start_time`, shortest-duration first, and untimed tasks sink to the end
  instead of crashing.
- **Recurrence logic** — completing a daily task marks it done and spawns a
  fresh occurrence due the following day; weekly tasks land 7 days out; `once`
  tasks never regenerate; `is_due` boundaries (on/before the due date).
- **Conflict detection** — duplicate/overlapping start times are flagged,
  adjacent non-overlapping tasks are not (half-open intervals), untimed tasks
  never conflict, and three same-time tasks produce three pairs.
- **Budget-constrained planning** — exact-fit and one-over-budget boundaries,
  zero budget, priority + duration tie-breaking, and exclusion of already-done
  tasks.
- **Filtering & degenerate inputs** — filtering by pet/status/priority, plus a
  pet with no tasks and an owner with no pets (no crashes, empty plans).

### Successful test run

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Somdu\OneDrive\Desktop\Coding\CodePath\AI110\ai110-module2show-pawpal-starter
collected 27 items

tests\test_pawpal.py ...........................                         [100%]

============================= 27 passed in 0.02s ==============================
```

### Confidence Level

**★★★★☆ (4 / 5)**

All 27 tests pass, covering every core behavior — sorting, recurrence, conflict
detection, and budget-constrained planning — including boundary cases (exact-fit
budgets, half-open time intervals, on/before due dates) and degenerate inputs
(no pets, no tasks). I'm holding back the fifth star because one behavior remains
unspecified rather than proven: `Task.next_occurrence` dates the next occurrence
from *when the task was completed*, not from its original `due_date`, so a
late-completed recurring task drifts. Once that intended behavior is decided and
pinned with a test, this moves to 5/5.

## 📐 Smarter Scheduling

Beyond the basic "pack by priority" plan, PawPal+ adds four pieces of smarter
scheduling logic. Each row names the exact method that implements it (all in
`pawpal_system.py`).

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_by_duration()`, `Scheduler.sort_by_priority()` | Chronological (by `start_time`), shortest-first (by duration), or highest-priority-first |
| Filtering | `Owner.filter_tasks()`, `Pet.pending_tasks()`, `Pet.completed_tasks()` | Filter by pet name, completion status, and/or priority |
| Conflict handling | `Scheduler.detect_conflicts()`, `Scheduler.conflict_warnings()`, `Task.overlaps()` | Flags overlapping time windows (same or different pets); returns warning strings instead of crashing |
| Recurring tasks | `Task.is_due()`, `Task.next_occurrence()`, `Pet.complete_task()` | Completing a daily/weekly task auto-creates the next occurrence (`today + timedelta`) |

### Sorting behavior

- **`Scheduler.sort_by_time(tasks)`** — orders tasks chronologically by their
  `start_time` (`"HH:MM"`). Untimed tasks (`start_time is None`) sort to the end
  instead of raising an error.
- **`Scheduler.sort_by_duration(tasks)`** — orders by time cost, shortest first.
- **`Scheduler.sort_by_priority(tasks)`** — highest priority first, ties broken by
  shorter duration.

### Filtering behavior

- **`Owner.filter_tasks(pet_name=None, done=None, priority=None)`** — one flexible
  entry point; any argument left `None` is ignored, so
  `owner.filter_tasks(pet_name="Mochi", done=False)` returns Mochi's outstanding
  tasks.
- **`Pet.pending_tasks()` / `Pet.completed_tasks()`** — quick status filters on a
  single pet.

### Conflict detection logic

- **`Task.overlaps(other)`** — half-open interval test on
  `[start, start + duration)`; untimed tasks never conflict.
- **`Scheduler.detect_conflicts(tasks=None)`** — returns every pair of planned
  tasks whose windows overlap (defaults to `planned_tasks`).
- **`Scheduler.conflict_warnings(owner=None)`** — lightweight: turns each conflict
  into a readable warning **string** (never raises), noting whether the clash is
  within one pet (`for Biscuit`) or across two (`Biscuit vs Mochi`).

### Recurring task logic

- **`Task.is_due(today)`** — a done task is never due again; a pending task is due
  once `today` reaches its `due_date`.
- **`Task.next_occurrence(completed_on)`** — factory returning a fresh Task due
  `completed_on + timedelta(days=1)` (daily) or `+7` (weekly); `None` for `"once"`.
- **`Pet.complete_task(task_id, on)`** — marks a task done **and** auto-appends its
  next occurrence, so recurring chores reschedule themselves.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
