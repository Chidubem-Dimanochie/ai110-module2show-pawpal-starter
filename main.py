"""Temporary testing ground for PawPal+ logic.

Run from the command line to verify the scheduling logic works:

    python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def main() -> None:
    # 1. Create an owner with a daily time budget.
    owner = Owner(name="Jordan", minutes_available=60)

    # 2. Create two pets and register them with the owner.
    biscuit = Pet(name="Biscuit", species="dog", breed="Golden Retriever")
    mochi = Pet(name="Mochi", species="cat", breed="Tabby")
    owner.add_pet(biscuit)
    owner.add_pet(mochi)

    # 3. Add several tasks with different durations and priorities.
    biscuit.add_task(Task("Morning walk", duration_minutes=30, priority="high"))
    biscuit.add_task(Task("Feeding", duration_minutes=10, priority="high"))
    biscuit.add_task(Task("Grooming", duration_minutes=25, priority="low"))

    mochi.add_task(Task("Litter box", duration_minutes=8, priority="high"))
    mochi.add_task(Task("Play/enrichment", duration_minutes=15, priority="medium"))

    # 4. Build and print "Today's Schedule" across all pets.
    scheduler = Scheduler(time_budget=owner.minutes_available)
    scheduler.plan_for_owner(owner)

    print("=" * 40)
    print(f"Today's Schedule for {owner.name}")
    print("=" * 40)
    print(scheduler.explain())


if __name__ == "__main__":
    main()
