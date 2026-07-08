"""Temporary testing ground for PawPal+ logic.

Run from the command line to verify the scheduling logic works:

    python main.py

Demonstrates the four scheduling improvements:
    1. sort by time (duration)
    2. filter by pet / status
    3. recurring tasks (frequency + is_due)
    4. conflict detection (overlapping start times)
"""

from datetime import date

from pawpal_system import Owner, Pet, Task, Scheduler


def main() -> None:
    today = date.today()

    # 1. Create an owner with a daily time budget.
    owner = Owner(name="Jordan", minutes_available=90)

    # 2. Create two pets and register them with the owner.
    biscuit = Pet(name="Biscuit", species="dog", breed="Golden Retriever")
    mochi = Pet(name="Mochi", species="cat", breed="Tabby")
    owner.add_pet(biscuit)
    owner.add_pet(mochi)

    # 3. Add tasks deliberately OUT OF ORDER (times not chronological) so the
    #    sorting methods have something real to fix. Evening walk is at 18:00
    #    but added first; feeding at 08:00 is added last.
    biscuit.add_task(Task("Evening walk", 30, "high", start_time="18:00"))
    biscuit.add_task(Task("Grooming", 25, "low", frequency="weekly"))
    biscuit.add_task(Task("Feeding", 10, "high", start_time="08:00"))

    mochi.add_task(Task("Play/enrichment", 15, "medium", start_time="09:05"))
    mochi.add_task(Task("Litter box", 8, "high", start_time="09:00"))

    # Two tasks deliberately at the SAME time (08:00) to trigger conflicts:
    #   - "Morning meds" for Biscuit clashes with Biscuit's own "Feeding"  (same pet)
    #   - "Vet call" for Mochi also lands at 08:00                          (different pets)
    biscuit.add_task(Task("Morning meds", 5, "high", start_time="08:00"))
    mochi.add_task(Task("Vet call", 5, "high", start_time="08:00"))

    # --- Recurring tasks: completing one auto-creates the next occurrence ---
    # Litter box is daily; finishing it today should spawn a copy due tomorrow.
    litter = mochi.tasks[1]
    next_litter = mochi.complete_task(litter.id, on=today)
    print(f"Completed '{litter.title}' (daily) on {today}.")
    print(f"  -> next occurrence auto-created, due {next_litter.due_date}\n")

    # Grooming is weekly; finishing it should spawn a copy due 7 days out.
    grooming = biscuit.tasks[1]
    next_grooming = biscuit.complete_task(grooming.id, on=today)
    print(f"Completed '{grooming.title}' (weekly) on {today}.")
    print(f"  -> next occurrence auto-created, due {next_grooming.due_date}\n")

    scheduler = Scheduler(time_budget=owner.minutes_available)

    # --- Sorting: chronological order by start_time ---
    print("Tasks added out of order, now sorted by time:")
    for t in scheduler.sort_by_time(owner.all_tasks()):
        when = t.start_time or "  --"
        print(f"  {when}  {t.title}")

    print("\nSame tasks sorted by duration (shortest first):")
    for t in scheduler.sort_by_duration(owner.all_tasks()):
        print(f"  - {t.title} ({t.duration_minutes} min)")

    # --- Filtering: by pet name and by completion status ---
    print("\nMochi's tasks still to do (done=False):")
    for t in owner.filter_tasks(pet_name="Mochi", done=False):
        print(f"  - {t.title}")

    print("\nEverything already completed (done=True):")
    for t in owner.filter_tasks(done=True):
        print(f"  - {t.title}")

    print("\nAll high-priority tasks:")
    for t in owner.filter_tasks(priority="high"):
        print(f"  - {t.title}")

    # --- Features 3 & 4: recurring filter + conflict detection in the plan ---
    #    Passing `today` drops the not-yet-due weekly grooming automatically.
    scheduler.plan_for_owner(owner, today=today)

    print("\n" + "=" * 40)
    print(f"Today's Schedule for {owner.name}")
    print("=" * 40)
    print(scheduler.explain())

    # --- Conflict detection: lightweight warnings, no crash ---
    warnings = scheduler.conflict_warnings(owner)
    print("\nSchedule check:")
    if warnings:
        for message in warnings:
            print(f"  {message}")
    else:
        print("  No time conflicts found.")


if __name__ == "__main__":
    main()
