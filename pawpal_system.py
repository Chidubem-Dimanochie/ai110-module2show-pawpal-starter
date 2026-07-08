"""PawPal+ logic layer.

Backend classes for tracking pet care tasks and generating daily plans.
This module mirrors the UML class diagram; keep both in sync.

Class roles:
    Task      - a single care activity (description, time, frequency, done).
    Pet       - stores a pet's details and its list of tasks.
    Owner     - manages multiple pets and exposes all of their tasks.
    Scheduler - the "brain": retrieves, sorts, and plans tasks across pets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from itertools import combinations, count

# Maps priority labels to a sort weight (higher = more important).
# Keeps sorting well-defined instead of relying on raw string comparison.
PRIORITY_ORDER = {"high": 3, "medium": 2, "low": 1}

# How many days must pass before a recurring task is "due" again.
# "once" is handled separately (due until it has ever been completed).
FREQUENCY_DAYS = {"daily": 1, "weekly": 7}

# Process-wide counter so every Task gets a unique id.
_task_ids = count(1)


def _to_minutes(clock: str) -> int:
    """Convert an ``"HH:MM"`` clock string to minutes past midnight."""
    hours, minutes = clock.split(":")
    return int(hours) * 60 + int(minutes)


@dataclass
class Task:
    """A single pet care task (walk, feeding, meds, etc.)."""

    title: str
    duration_minutes: int
    priority: str
    frequency: str = "daily"
    done: bool = False
    # Optional fixed time of day as "HH:MM". Only timed tasks can conflict.
    start_time: str | None = None
    # ISO date ("YYYY-MM-DD") this task was last completed; kept for history.
    last_done: str | None = None
    # ISO date this occurrence is due. None means "due now / no fixed date".
    # Auto-set on the next occurrence spawned when a recurring task is finished.
    due_date: str | None = None
    # Unique identity so two tasks with identical fields are still distinct.
    # Used by remove_task/edit_task to target the right task.
    id: int = field(default_factory=lambda: next(_task_ids))

    def mark_done(self, on: date | None = None) -> None:
        """Mark this task as completed, recording the date for recurrence."""
        self.done = True
        if on is not None:
            self.last_done = on.isoformat()

    def edit(self, title: str | None = None, duration_minutes: int | None = None,
             priority: str | None = None, frequency: str | None = None,
             done: bool | None = None, start_time: str | None = None) -> None:
        """Update one or more fields of this task; ``None`` leaves a field as-is."""
        if title is not None:
            self.title = title
        if duration_minutes is not None:
            self.duration_minutes = duration_minutes
        if priority is not None:
            self.priority = priority
        if frequency is not None:
            self.frequency = frequency
        if done is not None:
            self.done = done
        if start_time is not None:
            self.start_time = start_time

    # --- Time-of-day helpers (used for conflict detection) ---

    def start_minutes(self) -> int | None:
        """Start time as minutes past midnight, or None if the task is untimed."""
        return None if self.start_time is None else _to_minutes(self.start_time)

    def end_minutes(self) -> int | None:
        """End time as minutes past midnight, or None if the task is untimed."""
        start = self.start_minutes()
        return None if start is None else start + self.duration_minutes

    def overlaps(self, other: "Task") -> bool:
        """True if this task's time window overlaps ``other``'s.

        Untimed tasks (no ``start_time``) can never conflict. Uses the standard
        half-open interval test: [a_start, a_end) intersects [b_start, b_end).
        """
        a_start, b_start = self.start_minutes(), other.start_minutes()
        if a_start is None or b_start is None:
            return False
        return a_start < other.end_minutes() and b_start < self.end_minutes()

    # --- Recurrence ---

    def is_due(self, today: date) -> bool:
        """Whether this occurrence needs doing on ``today``.

        Each Task instance is a single occurrence: a completed one is never due
        again (its successor, spawned by :meth:`next_occurrence`, carries the
        future ``due_date``). An unfinished task with no ``due_date`` is due now;
        otherwise it becomes due once ``today`` reaches its ``due_date``.
        """
        if self.done:
            return False
        if self.due_date is None:
            return True
        return date.fromisoformat(self.due_date) <= today

    def next_occurrence(self, completed_on: date) -> "Task | None":
        """Return a fresh Task for the next occurrence, or None if it doesn't recur.

        Daily tasks come due ``completed_on + 1 day``, weekly ones ``+ 7 days``
        (via :data:`FREQUENCY_DAYS` and ``timedelta``). One-off tasks return None.
        The new task copies the recurring details but starts not-done, with a
        fresh id and its computed ``due_date``.
        """
        gap = FREQUENCY_DAYS.get(self.frequency)
        if gap is None:  # "once" or an unrecognized frequency: no successor
            return None
        next_due = completed_on + timedelta(days=gap)
        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            start_time=self.start_time,
            due_date=next_due.isoformat(),
        )


@dataclass
class Pet:
    """A pet owned by an Owner, with its own list of care tasks."""

    name: str
    species: str
    breed: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        self.tasks.append(task)

    def remove_task(self, task_id: int) -> None:
        """Remove the task with the given id from this pet."""
        self.tasks = [t for t in self.tasks if t.id != task_id]

    def edit_task(self, task_id: int, **changes) -> None:
        """Edit fields of the task with the given id.

        Extra keyword arguments are forwarded to ``Task.edit`` (e.g.
        ``pet.edit_task(3, priority="low", duration_minutes=15)``).
        """
        task = self.get_task(task_id)
        if task is not None:
            task.edit(**changes)

    def get_task(self, task_id: int) -> Task | None:
        """Return the task with the given id, or None if not found."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def complete_task(self, task_id: int, on: date) -> Task | None:
        """Mark a task complete and auto-schedule its next occurrence.

        Marks the task done (recording the date), then, if it recurs daily or
        weekly, spawns a fresh Task for the next due date and adds it to this
        pet. Returns the newly created occurrence, or None for one-off tasks
        (or an unknown ``task_id``).
        """
        task = self.get_task(task_id)
        if task is None:
            return None
        task.mark_done(on=on)
        upcoming = task.next_occurrence(on)
        if upcoming is not None:
            self.add_task(upcoming)
        return upcoming

    def pending_tasks(self) -> list[Task]:
        """Tasks not yet marked done."""
        return [t for t in self.tasks if not t.done]

    def completed_tasks(self) -> list[Task]:
        """Tasks already marked done."""
        return [t for t in self.tasks if t.done]


@dataclass
class Owner:
    """The pet owner, who owns one or more pets and has limited time."""

    name: str
    minutes_available: int
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner."""
        if pet in self.pets:
            self.pets.remove(pet)

    def all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets.

        This is the single entry point the Scheduler uses to read task data,
        so it never has to reach into ``owner.pets[i].tasks`` itself.
        """
        tasks: list[Task] = []
        for pet in self.pets:
            tasks.extend(pet.tasks)
        return tasks

    def filter_tasks(self, pet_name: str | None = None, done: bool | None = None,
                     priority: str | None = None) -> list[Task]:
        """Return tasks matching any combination of filters.

        Each argument left as ``None`` is ignored, so
        ``owner.filter_tasks(pet_name="Mochi", done=False)`` yields Mochi's
        outstanding tasks. This gives the UI one flexible entry point instead
        of hand-writing a new loop for every view.
        """
        result: list[Task] = []
        for pet in self.pets:
            if pet_name is not None and pet.name != pet_name:
                continue
            for task in pet.tasks:
                if done is not None and task.done != done:
                    continue
                if priority is not None and task.priority != priority:
                    continue
                result.append(task)
        return result

    def due_tasks(self, today: date) -> list[Task]:
        """Every task that is actually due on ``today`` (honors recurrence)."""
        return [t for t in self.all_tasks() if t.is_due(today)]

    def view_plan(self, pet: Pet) -> "Scheduler":
        """Build and return a daily plan for a single pet.

        Uses this owner's ``minutes_available`` as the time budget.
        """
        scheduler = Scheduler(time_budget=self.minutes_available, pet=pet)
        scheduler.generate_plan(pet.tasks)
        return scheduler


@dataclass
class Scheduler:
    """The planning "brain": retrieves, organizes, and plans tasks.

    ``planned_tasks`` holds the tasks that fit within ``time_budget``;
    ``skipped_tasks`` holds tasks that still need doing but didn't fit, so
    the UI can explain *why* the plan looks the way it does. ``conflicts``
    holds pairs of planned tasks whose fixed times overlap. Already-completed
    tasks are excluded from planning entirely.
    """

    time_budget: int
    pet: Pet | None = None
    planned_tasks: list[Task] = field(default_factory=list)
    skipped_tasks: list[Task] = field(default_factory=list)
    conflicts: list[tuple[Task, Task]] = field(default_factory=list)

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by priority (high first).

        Ties are broken by shorter duration first, so more high-value tasks
        can fit inside the same time budget.
        """
        return sorted(
            tasks,
            key=lambda t: (-PRIORITY_ORDER.get(t.priority, 0), t.duration_minutes),
        )

    def sort_by_priority_then_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by priority first, then by time of day.

        This is the schedule's presentation order: the most important tasks
        come first (high -> medium -> low via :data:`PRIORITY_ORDER`), and within
        a single priority level tasks run in chronological order of their
        ``start_time``. Untimed tasks sort to the end of their priority band
        (``float("inf")``) instead of raising when ``None`` meets a number.
        """
        return sorted(
            tasks,
            key=lambda t: (
                -PRIORITY_ORDER.get(t.priority, 0),
                t.start_minutes() if t.start_time else float("inf"),
            ),
        )

    def sort_by_duration(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by time cost (shortest first).

        Doing the quick tasks first is a simple way to clear the most items
        off the list when the owner is short on time.
        """
        return sorted(tasks, key=lambda t: t.duration_minutes)

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks in chronological order of their ``start_time``.

        A lambda ``key`` does the work. Zero-padded ``"HH:MM"`` strings already
        sort correctly as plain text ("08:00" < "09:05" < "10:00"), but we sort
        on ``start_minutes()`` so untimed tasks (``start_time is None``) go to
        the end instead of raising a TypeError when compared against a string.
        """
        return sorted(
            tasks,
            key=lambda t: t.start_minutes() if t.start_time else float("inf"),
        )

    def detect_conflicts(self, tasks: list[Task] | None = None) -> list[tuple[Task, Task]]:
        """Find pairs of *timed* tasks whose windows overlap.

        Defaults to the current ``planned_tasks``. Considers only tasks with a
        ``start_time`` and checks every unordered pair with
        :meth:`Task.overlaps`, so the overlap rule lives in exactly one place.
        Tasks are sorted by start time first so the reported pairs come out in
        chronological order. This is O(n^2) in the number of timed tasks, which
        is fine for the handful a pet owner schedules in a day.
        """
        source = self.planned_tasks if tasks is None else tasks
        timed = sorted(
            (t for t in source if t.start_time is not None),
            key=lambda t: t.start_minutes(),
        )

        self.conflicts = [(a, b) for a, b in combinations(timed, 2) if a.overlaps(b)]
        return self.conflicts

    def conflict_warnings(self, owner: Owner | None = None) -> list[str]:
        """Return a plain-text warning for each scheduling conflict.

        Lightweight by design: it never raises: it just reports. Each
        overlapping pair among the planned tasks becomes one human-readable
        string. If an ``owner`` is passed, the message says whether the clash
        is within a single pet or across two different pets; without it, the
        warning still lists the two tasks and their times.
        """
        # Map task id -> pet name so we can label same-pet vs. cross-pet clashes.
        pet_of: dict[int, str] = {}
        if owner is not None:
            for pet in owner.pets:
                for task in pet.tasks:
                    pet_of[task.id] = pet.name

        warnings: list[str] = []
        for earlier, later in self.detect_conflicts():
            who = ""
            name_a, name_b = pet_of.get(earlier.id), pet_of.get(later.id)
            if name_a and name_b:
                who = f" for {name_a}" if name_a == name_b else f" ({name_a} vs {name_b})"
            warnings.append(
                f"WARNING: time conflict{who}: '{earlier.title}' at "
                f"{earlier.start_time} overlaps '{later.title}' at {later.start_time}."
            )
        return warnings

    def generate_plan(self, tasks: list[Task]) -> "Scheduler":
        """Fill in the plan from ``tasks``, respecting the time budget.

        Skips tasks that are already done. *Selects* tasks by priority (with
        shorter duration breaking ties, so the most high-value tasks fit the
        budget), greedily adding until the budget runs out; tasks that don't fit
        go to ``skipped_tasks``. The kept tasks are then *presented* in
        priority-then-time order via :meth:`sort_by_priority_then_time`, so the
        plan reads most-important-first and chronologically within each level.
        Finally flags any time-of-day conflicts among the planned tasks. Mutates
        and returns ``self``.
        """
        self.planned_tasks = []
        self.skipped_tasks = []

        pending = [t for t in tasks if not t.done]
        remaining = self.time_budget

        for task in self.sort_by_priority(pending):
            if task.duration_minutes <= remaining:
                self.planned_tasks.append(task)
                remaining -= task.duration_minutes
            else:
                self.skipped_tasks.append(task)

        # Present the chosen tasks priority-first, then chronologically.
        self.planned_tasks = self.sort_by_priority_then_time(self.planned_tasks)

        self.detect_conflicts()
        return self

    def plan_for_owner(self, owner: Owner, today: date | None = None) -> "Scheduler":
        """Build a plan across all of an owner's pets.

        Uses the owner's ``minutes_available`` as the budget. When ``today`` is
        given, only tasks that are actually due (per their recurrence) are
        considered; otherwise every task is fair game.
        """
        self.time_budget = owner.minutes_available
        tasks = owner.due_tasks(today) if today is not None else owner.all_tasks()
        return self.generate_plan(tasks)

    def explain(self) -> str:
        """Return a human-readable summary of the plan and its reasoning."""
        who = f" for {self.pet.name}" if self.pet else ""
        lines = [f"Daily plan{who} ({self.time_budget} min available):"]

        if self.planned_tasks:
            for task in self.planned_tasks:
                when = f"{task.start_time} " if task.start_time else ""
                lines.append(
                    f"  - {when}{task.title} ({task.duration_minutes} min) "
                    f"[priority: {task.priority}]"
                )
        else:
            lines.append("  (nothing scheduled)")

        if self.skipped_tasks:
            lines.append("Skipped (not enough time):")
            for task in self.skipped_tasks:
                lines.append(
                    f"  - {task.title} ({task.duration_minutes} min) "
                    f"[priority: {task.priority}]"
                )

        if self.conflicts:
            lines.append("Time conflicts (overlapping tasks):")
            for earlier, later in self.conflicts:
                lines.append(
                    f"  ! {earlier.title} ({earlier.start_time}) overlaps "
                    f"{later.title} ({later.start_time})"
                )

        return "\n".join(lines)
