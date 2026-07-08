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
from itertools import count

# Maps priority labels to a sort weight (higher = more important).
# Keeps sorting well-defined instead of relying on raw string comparison.
PRIORITY_ORDER = {"high": 3, "medium": 2, "low": 1}

# Process-wide counter so every Task gets a unique id.
_task_ids = count(1)


@dataclass
class Task:
    """A single pet care task (walk, feeding, meds, etc.)."""

    title: str
    duration_minutes: int
    priority: str
    frequency: str = "daily"
    done: bool = False
    # Unique identity so two tasks with identical fields are still distinct.
    # Used by remove_task/edit_task to target the right task.
    id: int = field(default_factory=lambda: next(_task_ids))

    def mark_done(self) -> None:
        """Mark this task as completed."""
        self.done = True

    def edit(self, title: str | None = None, duration_minutes: int | None = None,
             priority: str | None = None, frequency: str | None = None,
             done: bool | None = None) -> None:
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
    the UI can explain *why* the plan looks the way it does. Already-completed
    tasks are excluded from planning entirely.
    """

    time_budget: int
    pet: Pet | None = None
    planned_tasks: list[Task] = field(default_factory=list)
    skipped_tasks: list[Task] = field(default_factory=list)

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by priority (high first).

        Ties are broken by shorter duration first, so more high-value tasks
        can fit inside the same time budget.
        """
        return sorted(
            tasks,
            key=lambda t: (-PRIORITY_ORDER.get(t.priority, 0), t.duration_minutes),
        )

    def generate_plan(self, tasks: list[Task]) -> "Scheduler":
        """Fill in the plan from ``tasks``, respecting the time budget.

        Skips tasks that are already done, sorts the rest by priority, then
        greedily adds tasks until the budget runs out. Tasks that don't fit
        go to ``skipped_tasks``. Mutates and returns ``self``.
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

        return self

    def plan_for_owner(self, owner: Owner) -> "Scheduler":
        """Build a plan across all of an owner's pets.

        Retrieves tasks through ``owner.all_tasks()`` and uses the owner's
        ``minutes_available`` as the budget.
        """
        self.time_budget = owner.minutes_available
        return self.generate_plan(owner.all_tasks())

    def explain(self) -> str:
        """Return a human-readable summary of the plan and its reasoning."""
        who = f" for {self.pet.name}" if self.pet else ""
        lines = [f"Daily plan{who} ({self.time_budget} min available):"]

        if self.planned_tasks:
            for task in self.planned_tasks:
                lines.append(
                    f"  - {task.title} ({task.duration_minutes} min) "
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

        return "\n".join(lines)
