# PawPal+ Project Reflection

## 1. System Design

**Core user actions**

These are the three core actions a user should be able to perform in PawPal+:

1. **Set a priority on each task.** Every care task the user adds has a level of importance (for example: high, medium, low). This priority system lets the scheduler decide which tasks matter most when time is limited, so the essentials get done first.

2. **Create accounts for different pets.** The user can add multiple accounts for various pets, each with its own species and breed. This keeps each pet's care separate and lets the owner manage several animals from one app.

3. **Track what's done and what's left.** The user can see which tasks have been completed and which still need to be done, so it's always clear what remains for the day.

**a. Initial design**

My initial UML design has four classes:

- **Owner** — holds the user's info (name, minutes available per day) and their list of pets. Responsible for adding/removing pets and requesting a plan.
- **Pet** — holds a pet's info (name, species, breed) and its list of tasks. Responsible for adding, removing, and editing its own tasks.
- **Task** — represents a single care task (title, duration, priority, done status). Responsible for marking itself done and editing its details.
- **Schedule** — takes a pet's tasks and the owner's time budget and builds the daily plan. Responsible for sorting tasks by priority and generating the schedule.

An Owner owns many Pets, a Pet has many Tasks, and the Schedule uses those Tasks to produce the plan.

**b. Design changes**

Yes. After reviewing my skeleton, I made four changes so the classes would actually support the behavior I wanted:

1. **Gave `Task` a unique `id`.** Because `Task` is a dataclass, two tasks with the same title, duration, and priority counted as equal. That meant removing or editing a task could hit the wrong one when a pet had look-alike tasks. Each task now gets a unique id from a counter, and `remove_task`/`edit_task` take a `task_id` instead of a whole `Task` object so they always target the right one.

2. **Settled how `Schedule.generate_plan` works.** Originally it was unclear whether the plan was built in the constructor, by mutating the object, or by returning a new one. I standardized on: `generate_plan` fills in the schedule and returns `self`. This keeps one clear pattern instead of two competing ones.

3. **Added `skipped_tasks` to `Schedule`.** The old design only stored the tasks that made it into the plan, so when a task got dropped for lack of time it just disappeared. Since a core goal is explaining *why* the plan looks the way it does, I now keep the left-out tasks so the UI can show what was skipped and why.

4. **Made `done` actually matter.** `Task.done` existed but nothing used it. `generate_plan` now skips tasks that are already done before scheduling, which supports the "track what's done vs. what's left" action.

I also added a `PRIORITY_ORDER` mapping so priority sorting is well-defined instead of relying on raw string comparison, and gave `Schedule` an optional reference to its `Pet` so a plan knows which pet it belongs to (useful for labeled output like "Daily plan for Biscuit").

<!-- AI-ASSISTED NOTES (Phase 3 logic additions) — edit/trim as needed -->
> **Phase 3 additions (AI-assisted, to fold into the write-up above):**
> - **Sorting by time.** Added `Scheduler.sort_by_time()` (chronological by `start_time`) and `Scheduler.sort_by_duration()` (shortest-first) alongside the original `sort_by_priority()`. `sort_by_time` uses a `sorted()` lambda key on `start_minutes()` so untimed tasks fall to the end instead of raising a `TypeError` when `None` is compared to a string.
> - **Filtering.** Added `Owner.filter_tasks(pet_name=, done=, priority=)` as one flexible entry point (any arg left `None` is ignored), plus `Pet.pending_tasks()` / `Pet.completed_tasks()` helpers.
> - **Time-of-day + conflicts.** Gave `Task` an optional `start_time` ("HH:MM") with `start_minutes()`/`end_minutes()`/`overlaps()` helpers, and added `Scheduler.detect_conflicts()` which flags pairs of planned tasks whose windows overlap. It sorts by start time and breaks early once a task starts after the current one ends (avoids blind O(n²) checking). `explain()` now prints conflicts.
> - **Recurring tasks.** The previously-unused `Task.frequency` now drives recurrence. Added `Task.due_date`, reworked `Task.is_due(today)` to a per-occurrence model (a done task is never due again; a pending one is due once `today` reaches its `due_date`), and added `Task.next_occurrence(completed_on)` — a factory that returns a fresh Task due `completed_on + timedelta(days=1)` (daily) or `+7` (weekly), or `None` for `"once"`.
> - **Completion → regeneration.** Added `Pet.complete_task(task_id, on)` which marks a task done *and* auto-appends the next occurrence. This is where completion and `frequency` interact.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

<!-- AI-ASSISTED NOTES — edit/trim as needed -->
> **Constraints now considered (AI-assisted additions):** total time budget (`minutes_available`), task `priority` (via `PRIORITY_ORDER`), whether a task is already `done`, time of day / overlapping `start_time` windows (`detect_conflicts`), and recurrence — only tasks that are actually due today are planned when `plan_for_owner(owner, today=...)` is used.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

<!-- AI-ASSISTED NOTES — edit/trim as needed -->
> **Tradeoffs in the current logic (AI-assisted additions):**
> - The planner still packs greedily by priority/budget and only *reports* time conflicts via `detect_conflicts()` / `conflict_warnings()` — it does not automatically reschedule overlapping tasks. Reasonable because surfacing the conflict lets the owner decide, which is simpler and more transparent than auto-moving tasks.
> - **Lightweight conflict warnings.** `Scheduler.conflict_warnings(owner=None)` returns a list of plain warning *strings* (never raises), one per overlapping pair, labeling whether the clash is within one pet ("for Biscuit") or across two ("Biscuit vs Mochi"). Chose returning messages over throwing so the program keeps running and the UI/terminal can just print the warnings.

<!-- Documented tradeoff (Step 5) — edit as needed -->
> **One tradeoff, explained.** Conflict detection only looks at tasks that have an explicit `start_time`; a task with no fixed time can never trigger a warning, even if the day is over-booked. I chose to detect *overlapping durations* (start → start+duration) rather than only *exact* start-time matches, so a 30-min task starting at 08:00 correctly clashes with one at 08:15. The tradeoff is that untimed tasks are invisible to conflict checking — reasonable here because most flexible chores (grooming, play) genuinely don't have a fixed clock time, and forcing one on them would create false conflicts. A related tradeoff: `detect_conflicts()` compares every timed pair (O(n²)); I kept that for readability since a single day holds only a handful of timed tasks.
> - `Pet.complete_task` leaves the finished instance in the list (marked done) *and* adds the successor, so completed tasks accumulate over time. Tradeoff: preserves history for `filter_tasks(done=True)` at the cost of a growing list.

---

## 3. AI Collaboration

**a. How you used AI**

I used my AI coding assistant across every phase, but for different jobs each time. In the
**design** phase it was a brainstorming partner: I described the four classes and asked it to
poke holes in the responsibilities before I wrote any logic. In the **build** phase it did
multi-step refactoring and feature wiring — for example, connecting the `Scheduler` methods
into `app.py` and keeping the UML source in sync with the final code. In the **testing** phase
it generated the first pass of the pytest suite and brainstormed edge cases I hadn't considered
(exact-fit budgets, adjacent-but-not-overlapping times, empty pet lists).

The most helpful prompts were **specific and file-grounded**: attaching `pawpal_system.py` and
asking a pointed question like *"what are the most important edge cases to test for a scheduler
with sorting and recurring tasks?"* got far better answers than a vague *"write some tests."*
Asking it to *explain* code before I saved it (rather than just accept it) was also key — it
turned the assistant into a tutor instead of a black box.

**b. Judgment and verification**

I verified AI output by **running it**, not just reading it: every generated test had to pass
(`python -m pytest`), and I ran `python main.py` end-to-end to confirm the behavior matched the
description. When the assistant flagged a possible late-completion recurrence bug, I treated it
as a claim to check rather than a fact — I traced `next_occurrence` myself and decided it was an
*unspecified* behavior, not a defect, and left it documented instead of silently "fixing" it.

One moment I did not accept a suggestion as-is: for `detect_conflicts`, the assistant proposed an
early-exit sweep (sort by start time, then break out of the inner loop once a task starts after
the current one ends) to avoid a blind O(n²) scan. I **rejected the optimization** and kept the
plain `combinations()` version, because a single day only ever holds a handful of timed tasks, so
the clever version added branching and off-by-one risk for a speedup nobody would ever notice.
Keeping it simple made the method easier to read and test.

**c. AI Strategy**

*Which AI coding assistant features were most effective for building your scheduler?*

Three features carried the most weight. (1) **File-attached chat / context** — pointing the
assistant at `pawpal_system.py` so its suggestions matched my actual class names and signatures
instead of a generic template. (2) **Agentic multi-file edits** — having it make coordinated
changes across `app.py`, `tests/test_pawpal.py`, the UML `.mmd`, and the README in one pass,
which kept everything consistent. (3) **Test scaffolding + edge-case brainstorming** — it turned
9 starter tests into 27 by surfacing boundary cases (budget exactly equal to a task's duration,
half-open time intervals, a pet with no tasks) that I would likely have missed.

*One AI suggestion I rejected or modified to keep the design clean.*

Beyond the `detect_conflicts` optimization above, the assistant at one point suggested letting the
`Scheduler` automatically **reschedule** conflicting tasks. I modified that down to *reporting*
conflicts only (`conflict_warnings` returns plain strings and never raises). Auto-rescheduling
would have blurred the `Scheduler`'s responsibility — it should detect and explain, not silently
move the owner's tasks around. Keeping "detect vs. decide" separate kept the class focused and the
behavior transparent to the user.

*How separate chat sessions for different phases helped me stay organized.*

I ran a different chat session per phase — design/UML, logic build, testing, UI, and docs. This
kept each conversation's context tight, so the assistant wasn't juggling test details while I was
still deciding class responsibilities. It also mirrored the project's phase structure, which made
it easy to go back and re-read the reasoning behind one phase without scrolling through everything
else, and it stopped the model from conflating concerns across phases (e.g., proposing UI code
while I only wanted to talk about the data model).

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

<!-- AI-ASSISTED NOTES — edit/trim as needed -->
> **Tests added (AI-assisted, in `tests/test_pawpal.py`):** `sort_by_duration` ordering; `filter_tasks` by pet + status; `detect_conflicts` flagging overlapping start times; completing a daily task spawning a next occurrence due tomorrow (`test_completing_daily_task_spawns_next_occurrence`); a weekly successor being due `+7` days and not sooner; and a `"once"` task producing no successor. Suite is currently 8 passing tests.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
