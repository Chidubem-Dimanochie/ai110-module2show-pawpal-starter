"""Tests for the PawPal+ logic layer.

Run with:
    pytest
"""

from datetime import date, timedelta

from pawpal_system import Owner, Pet, Task, Scheduler


def test_task_completion_changes_status():
    """Calling mark_done() flips a task's status from not-done to done."""
    task = Task("Morning walk", duration_minutes=30, priority="high")

    # A new task should start as not done.
    assert task.done is False

    task.mark_done()

    # After marking done, its status should be True.
    assert task.done is True


def test_adding_task_increases_pet_task_count():
    """Adding a task to a Pet increases that pet's task count by one."""
    pet = Pet("Biscuit", species="dog", breed="Golden Retriever")

    # A new pet starts with no tasks.
    assert len(pet.tasks) == 0

    pet.add_task(Task("Feeding", duration_minutes=10, priority="high"))

    # The task list should now hold exactly one task.
    assert len(pet.tasks) == 1


def test_sort_by_duration_orders_shortest_first():
    """sort_by_duration returns tasks ordered by ascending time cost."""
    scheduler = Scheduler(time_budget=60)
    tasks = [
        Task("Walk", 30, "high"),
        Task("Feed", 10, "high"),
        Task("Play", 15, "medium"),
    ]

    ordered = [t.title for t in scheduler.sort_by_duration(tasks)]

    assert ordered == ["Feed", "Play", "Walk"]


def test_filter_tasks_by_pet_and_status():
    """filter_tasks narrows results by pet name and done status."""
    owner = Owner("Jordan", minutes_available=60)
    mochi = Pet("Mochi", "cat", "Tabby")
    biscuit = Pet("Biscuit", "dog", "Golden Retriever")
    owner.add_pet(mochi)
    owner.add_pet(biscuit)

    litter = Task("Litter box", 8, "high")
    play = Task("Play", 15, "medium")
    mochi.add_task(litter)
    mochi.add_task(play)
    biscuit.add_task(Task("Walk", 30, "high"))
    litter.mark_done()

    pending_mochi = owner.filter_tasks(pet_name="Mochi", done=False)

    assert [t.title for t in pending_mochi] == ["Play"]


def test_completing_daily_task_spawns_next_occurrence():
    """Completing a daily task marks it done and adds a copy due tomorrow."""
    today = date(2026, 7, 8)
    pet = Pet("Biscuit", "dog", "Golden Retriever")
    pet.add_task(Task("Feeding", 10, "high", frequency="daily"))
    original = pet.tasks[0]

    upcoming = pet.complete_task(original.id, on=today)

    # Original is now done; exactly one fresh occurrence was created.
    assert original.done is True
    assert len(pet.tasks) == 2
    assert upcoming.done is False
    assert upcoming.due_date == (today + timedelta(days=1)).isoformat()
    # Distinct instance, not the same object with a flipped flag.
    assert upcoming.id != original.id


def test_weekly_next_occurrence_is_seven_days_out():
    """A weekly task's successor is due in 7 days and not due today."""
    today = date(2026, 7, 8)
    task = Task("Grooming", 25, "low", frequency="weekly")

    upcoming = task.next_occurrence(today)

    assert upcoming.due_date == (today + timedelta(days=7)).isoformat()
    assert upcoming.is_due(today) is False                     # due next week
    assert upcoming.is_due(today + timedelta(days=7)) is True  # due when it arrives


def test_once_task_has_no_next_occurrence():
    """One-off tasks do not regenerate."""
    task = Task("Vet appointment", 60, "high", frequency="once")

    assert task.next_occurrence(date(2026, 7, 8)) is None


def test_detect_conflicts_flags_overlapping_times():
    """Two tasks whose time windows overlap are reported as a conflict."""
    scheduler = Scheduler(time_budget=120)
    walk = Task("Walk", 30, "high", start_time="08:00")
    feed = Task("Feed", 10, "high", start_time="08:00")
    later = Task("Play", 15, "medium", start_time="10:00")

    conflicts = scheduler.detect_conflicts([walk, feed, later])

    # Only the two 08:00 tasks overlap; the 10:00 task is clear.
    assert len(conflicts) == 1
    titles = {conflicts[0][0].title, conflicts[0][1].title}
    assert titles == {"Walk", "Feed"}


def test_conflict_warnings_label_same_pet_and_cross_pet():
    """conflict_warnings returns readable strings noting which pet(s) clash."""
    owner = Owner("Jordan", minutes_available=120)
    biscuit = Pet("Biscuit", "dog", "Golden Retriever")
    mochi = Pet("Mochi", "cat", "Tabby")
    owner.add_pet(biscuit)
    owner.add_pet(mochi)

    biscuit.add_task(Task("Feeding", 10, "high", start_time="08:00"))
    biscuit.add_task(Task("Morning meds", 5, "high", start_time="08:00"))
    mochi.add_task(Task("Vet call", 5, "high", start_time="08:00"))

    scheduler = Scheduler(time_budget=owner.minutes_available)
    scheduler.plan_for_owner(owner)
    warnings = scheduler.conflict_warnings(owner)

    # Three all-08:00 tasks -> three overlapping pairs, all reported as strings.
    assert len(warnings) == 3
    assert all(isinstance(w, str) for w in warnings)
    joined = " ".join(warnings)
    assert "for Biscuit" in joined            # same-pet clash labeled
    assert "Biscuit vs Mochi" in joined or "Mochi vs Biscuit" in joined  # cross-pet
