"""Tests for the PawPal+ logic layer.

Run with:
    pytest
"""

from pawpal_system import Pet, Task


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
