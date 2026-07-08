"""PawPal+ logic layer.

Backend classes for tracking pet care tasks and generating daily plans.
This module mirrors the UML class diagram; keep both in sync.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Task:
    """A single pet care task (walk, feeding, meds, etc.)."""

    title: str
    duration_minutes: int
    priority: str
    done: bool = False

    def mark_done(self) -> None:
        """Mark this task as completed."""
        raise NotImplementedError

    def edit(self, title: str | None = None, duration_minutes: int | None = None,
             priority: str | None = None) -> None:
        """Update one or more fields of this task."""
        raise NotImplementedError


@dataclass
class Pet:
    """A pet owned by an Owner, with its own list of care tasks."""

    name: str
    species: str
    breed: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        raise NotImplementedError

    def remove_task(self, task: Task) -> None:
        """Remove a care task from this pet."""
        raise NotImplementedError

    def edit_task(self, task: Task) -> None:
        """Edit an existing task belonging to this pet."""
        raise NotImplementedError


@dataclass
class Owner:
    """The pet owner, who owns one or more pets and has limited time."""

    name: str
    minutes_available: int
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        raise NotImplementedError

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner."""
        raise NotImplementedError

    def view_plan(self, pet: Pet) -> "Schedule":
        """Generate and return a daily plan for the given pet."""
        raise NotImplementedError


@dataclass
class Schedule:
    """A generated daily plan of tasks that fit within a time budget."""

    time_budget: int
    planned_tasks: list[Task] = field(default_factory=list)

    def generate_plan(self, tasks: list[Task]) -> "Schedule":
        """Build a plan from the given tasks, respecting the time budget."""
        raise NotImplementedError

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by priority (high first)."""
        raise NotImplementedError