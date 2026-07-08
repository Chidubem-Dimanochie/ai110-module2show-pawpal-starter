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


# ---------------------------------------------------------------------------
# Budget-constrained planning (Scheduler.generate_plan)
# ---------------------------------------------------------------------------

def test_task_exactly_equal_to_budget_is_included():
    """A task whose duration equals the remaining budget still fits (<= boundary)."""
    scheduler = Scheduler(time_budget=30)
    scheduler.generate_plan([Task("Walk", 30, "high")])

    assert [t.title for t in scheduler.planned_tasks] == ["Walk"]
    assert scheduler.skipped_tasks == []


def test_task_one_minute_over_budget_is_skipped():
    """A task one minute larger than the budget is skipped, not planned."""
    scheduler = Scheduler(time_budget=29)
    scheduler.generate_plan([Task("Walk", 30, "high")])

    assert scheduler.planned_tasks == []
    assert [t.title for t in scheduler.skipped_tasks] == ["Walk"]


def test_zero_budget_skips_everything():
    """With no time available, every task is skipped and nothing crashes."""
    scheduler = Scheduler(time_budget=0)
    scheduler.generate_plan([Task("Walk", 30, "high"), Task("Feed", 10, "high")])

    assert scheduler.planned_tasks == []
    assert len(scheduler.skipped_tasks) == 2


def test_planning_orders_by_priority_then_shorter_duration():
    """High priority goes first; ties are broken by shorter duration."""
    scheduler = Scheduler(time_budget=1000)
    tasks = [
        Task("Long high", 40, "high"),
        Task("Low", 5, "low"),
        Task("Short high", 10, "high"),
    ]
    scheduler.generate_plan(tasks)

    # Both highs before the low; among highs, the shorter one first.
    assert [t.title for t in scheduler.planned_tasks] == ["Short high", "Long high", "Low"]


def test_done_tasks_are_excluded_from_planning():
    """An already-completed task appears in neither planned nor skipped lists."""
    scheduler = Scheduler(time_budget=1000)
    done = Task("Already fed", 10, "high")
    done.mark_done()
    scheduler.generate_plan([done, Task("Walk", 30, "high")])

    titles = {t.title for t in scheduler.planned_tasks + scheduler.skipped_tasks}
    assert titles == {"Walk"}


# ---------------------------------------------------------------------------
# Conflict-detection boundaries (Task.overlaps / Scheduler.detect_conflicts)
# ---------------------------------------------------------------------------

def test_adjacent_tasks_do_not_conflict():
    """A task ending at 08:30 does not clash with one starting at 08:30 (half-open)."""
    scheduler = Scheduler(time_budget=120)
    first = Task("Walk", 30, "high", start_time="08:00")   # 08:00-08:30
    second = Task("Feed", 10, "high", start_time="08:30")  # 08:30-08:40

    assert scheduler.detect_conflicts([first, second]) == []


def test_untimed_task_never_conflicts():
    """A task with no start_time cannot overlap a timed task."""
    scheduler = Scheduler(time_budget=120)
    timed = Task("Walk", 30, "high", start_time="08:00")
    untimed = Task("Groom", 30, "low")

    assert scheduler.detect_conflicts([timed, untimed]) == []


def test_three_same_time_tasks_yield_three_pairs():
    """Three overlapping tasks produce all three unordered pairs."""
    scheduler = Scheduler(time_budget=120)
    tasks = [
        Task("A", 10, "high", start_time="08:00"),
        Task("B", 10, "high", start_time="08:00"),
        Task("C", 10, "high", start_time="08:00"),
    ]

    assert len(scheduler.detect_conflicts(tasks)) == 3


def test_detect_conflicts_on_empty_list_is_empty():
    """No tasks means no conflicts, no crash."""
    scheduler = Scheduler(time_budget=120)
    assert scheduler.detect_conflicts([]) == []


# ---------------------------------------------------------------------------
# Recurrence / due-date boundaries (Task.is_due, Pet.complete_task)
# ---------------------------------------------------------------------------

def test_is_due_on_exact_due_date():
    """A task is due exactly on its due_date (<= boundary)."""
    today = date(2026, 7, 8)
    task = Task("Feeding", 10, "high", frequency="daily")
    task.due_date = today.isoformat()

    assert task.is_due(today) is True


def test_is_due_day_before_due_date_is_false():
    """A task dated for tomorrow is not yet due today."""
    today = date(2026, 7, 8)
    task = Task("Feeding", 10, "high", frequency="daily")
    task.due_date = (today + timedelta(days=1)).isoformat()

    assert task.is_due(today) is False


def test_complete_unknown_task_id_returns_none():
    """Completing a nonexistent task id returns None and adds nothing."""
    pet = Pet("Biscuit", "dog", "Golden Retriever")
    pet.add_task(Task("Feeding", 10, "high", frequency="daily"))

    result = pet.complete_task(9999, on=date(2026, 7, 8))

    assert result is None
    assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# Empty / degenerate inputs
# ---------------------------------------------------------------------------

def test_pet_with_no_tasks_has_empty_task_views():
    """A pet with no tasks reports empty pending and completed lists."""
    pet = Pet("Ghost", "cat", "Unknown")

    assert pet.pending_tasks() == []
    assert pet.completed_tasks() == []


def test_owner_with_no_pets_plans_empty_without_crashing():
    """An owner with no pets produces an empty plan and no tasks."""
    owner = Owner("Jordan", minutes_available=60)
    scheduler = Scheduler(time_budget=owner.minutes_available)
    scheduler.plan_for_owner(owner)

    assert owner.all_tasks() == []
    assert owner.due_tasks(date(2026, 7, 8)) == []
    assert scheduler.planned_tasks == []


# ---------------------------------------------------------------------------
# Sorting with mixed timed / untimed tasks (Scheduler.sort_by_time)
# ---------------------------------------------------------------------------

def test_sort_by_time_puts_untimed_tasks_last():
    """Timed tasks come out chronologically; untimed tasks sink to the end."""
    scheduler = Scheduler(time_budget=120)
    tasks = [
        Task("Untimed", 10, "low"),
        Task("Late", 10, "high", start_time="18:00"),
        Task("Early", 10, "high", start_time="08:00"),
    ]

    ordered = [t.title for t in scheduler.sort_by_time(tasks)]

    assert ordered == ["Early", "Late", "Untimed"]


# ===========================================================================
# Required categories (explicit, one test per requirement)
# ===========================================================================

def test_sorting_correctness_chronological_order():
    """REQUIRED: Sorting Correctness.

    sort_by_time must return timed tasks in ascending time-of-day order,
    regardless of the order they were added in.
    """
    scheduler = Scheduler(time_budget=120)
    tasks = [
        Task("Evening walk", 30, "high", start_time="18:00"),
        Task("Feeding", 10, "high", start_time="08:00"),
        Task("Midday play", 15, "medium", start_time="12:30"),
    ]

    ordered = [t.start_time for t in scheduler.sort_by_time(tasks)]

    assert ordered == ["08:00", "12:30", "18:00"]


def test_recurrence_daily_complete_creates_next_day_task():
    """REQUIRED: Recurrence Logic.

    Marking a daily task complete must create a new task due the following day.
    """
    today = date(2026, 7, 8)
    pet = Pet("Biscuit", "dog", "Golden Retriever")
    pet.add_task(Task("Feeding", 10, "high", frequency="daily"))
    original = pet.tasks[0]

    upcoming = pet.complete_task(original.id, on=today)

    assert original.done is True                       # old one is finished
    assert len(pet.tasks) == 2                         # a new one was added
    assert upcoming.done is False                      # the new one is not done
    assert upcoming.due_date == "2026-07-09"           # due the following day


def test_priority_then_time_sorting():
    """Enhanced sort: highest priority first, chronological within each level."""
    scheduler = Scheduler(time_budget=1000)
    tasks = [
        Task("Med walk", 20, "medium", start_time="07:00"),  # earliest, but medium
        Task("High late", 10, "high", start_time="09:00"),
        Task("High early", 10, "high", start_time="08:00"),
        Task("Low", 5, "low", start_time="06:00"),
    ]

    ordered = [t.title for t in scheduler.sort_by_priority_then_time(tasks)]

    # Highs (chronological) -> medium -> low, even though Low/Med start earlier.
    assert ordered == ["High early", "High late", "Med walk", "Low"]


def test_generated_plan_is_ordered_priority_then_time():
    """A built plan presents tasks priority-first, then by start time."""
    scheduler = Scheduler(time_budget=1000)
    scheduler.generate_plan([
        Task("Evening meds", 5, "high", start_time="18:00"),
        Task("Morning feed", 10, "high", start_time="08:00"),
        Task("Midday play", 15, "medium", start_time="12:00"),
    ])

    assert [t.title for t in scheduler.planned_tasks] == [
        "Morning feed", "Evening meds", "Midday play"
    ]


def test_conflict_detection_flags_duplicate_times():
    """REQUIRED: Conflict Detection.

    The Scheduler must flag two tasks scheduled at the exact same time.
    """
    scheduler = Scheduler(time_budget=120)
    walk = Task("Walk", 30, "high", start_time="08:00")
    feed = Task("Feed", 10, "high", start_time="08:00")

    conflicts = scheduler.detect_conflicts([walk, feed])

    assert len(conflicts) == 1
    clashing = {conflicts[0][0].title, conflicts[0][1].title}
    assert clashing == {"Walk", "Feed"}
