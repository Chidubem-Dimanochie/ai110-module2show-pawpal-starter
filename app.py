from datetime import date

import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# Persist the Owner across reruns instead of recreating it each time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", minutes_available=60)

owner = st.session_state.owner

st.title("🐾 PawPal+")
st.caption("A pet care planning assistant — plan the day around your time, priorities, and schedule.")

st.divider()

# --- Owner settings ---
st.subheader("👤 Owner")
owner.name = st.text_input("Owner name", value=owner.name)
owner.minutes_available = st.number_input(
    "Minutes available today", min_value=0, max_value=1440, value=owner.minutes_available
)

st.divider()

# --- Add a pet ---
st.subheader("🐕 Add a Pet")
col1, col2, col3 = st.columns(3)
with col1:
    new_pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    new_species = st.selectbox("Species", ["dog", "cat", "other"])
with col3:
    new_breed = st.text_input("Breed", value="Tabby")

if st.button("Add pet"):
    owner.add_pet(Pet(name=new_pet_name, species=new_species, breed=new_breed))
    st.success(f"Added {new_pet_name}.")

if not owner.pets:
    st.info("No pets yet. Add one above to get started.")

st.divider()

# --- Add a task to a pet ---
if owner.pets:
    st.subheader("📝 Add a Task")
    pet_names = [p.name for p in owner.pets]
    selected_name = st.selectbox("For which pet?", pet_names)
    selected_pet = owner.pets[pet_names.index(selected_name)]

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    col4, col5, col6 = st.columns(3)
    with col4:
        frequency = st.selectbox("Repeats", ["once", "daily", "weekly"], index=1)
    with col5:
        # Timed tasks are the only ones that can conflict, so make it optional.
        has_time = st.checkbox("Has a fixed time")
    with col6:
        clock = st.time_input("Start time", value=None, disabled=not has_time)

    if st.button("Add task"):
        start_time = clock.strftime("%H:%M") if (has_time and clock is not None) else None
        selected_pet.add_task(
            Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=priority,
                frequency=frequency,
                start_time=start_time,
            )
        )
        st.success(f"Added '{task_title}' to {selected_pet.name}.")

st.divider()

# --- Browse tasks: filter + sort (surfaces Owner.filter_tasks + Scheduler sorts) ---
if owner.pets:
    st.subheader("🔍 Browse Tasks")

    scheduler = Scheduler(time_budget=owner.minutes_available)

    fcol1, fcol2, fcol3, fcol4 = st.columns(4)
    with fcol1:
        pet_filter = st.selectbox("Pet", ["All"] + [p.name for p in owner.pets])
    with fcol2:
        status_filter = st.selectbox("Status", ["All", "Pending", "Done"])
    with fcol3:
        priority_filter = st.selectbox("Priority", ["All", "high", "medium", "low"])
    with fcol4:
        sort_choice = st.selectbox("Sort by", ["Time of day", "Duration", "Priority"])

    # Translate the UI choices into filter_tasks arguments.
    done_arg = {"All": None, "Pending": False, "Done": True}[status_filter]
    tasks = owner.filter_tasks(
        pet_name=None if pet_filter == "All" else pet_filter,
        done=done_arg,
        priority=None if priority_filter == "All" else priority_filter,
    )

    # Apply the chosen Scheduler sort method.
    sorter = {
        "Time of day": scheduler.sort_by_time,
        "Duration": scheduler.sort_by_duration,
        "Priority": scheduler.sort_by_priority,
    }[sort_choice]
    tasks = sorter(tasks)

    # Build a pet-name lookup so the table can show which pet each task belongs to.
    pet_of = {t.id: p.name for p in owner.pets for t in p.tasks}

    if tasks:
        st.table(
            [
                {
                    "Pet": pet_of.get(t.id, "?"),
                    "Task": t.title,
                    "Time": t.start_time or "—",
                    "Duration": f"{t.duration_minutes} min",
                    "Priority": t.priority,
                    "Repeats": t.frequency,
                    "Done": "✅" if t.done else "⬜",
                }
                for t in tasks
            ]
        )
    else:
        st.caption("No tasks match these filters.")

    # --- Complete a task (surfaces recurrence: completing spawns the next one) ---
    pending = [
        (p, t) for p in owner.pets for t in p.tasks if not t.done
    ]
    if pending:
        st.markdown("**Mark a task complete**")
        labels = [
            f"{p.name}: {t.title}" + (f" @ {t.start_time}" if t.start_time else "")
            for p, t in pending
        ]
        choice = st.selectbox("Completed task", labels, key="complete_choice")
        if st.button("Mark complete"):
            done_pet, done_task = pending[labels.index(choice)]
            upcoming = done_pet.complete_task(done_task.id, on=date.today())
            if upcoming is not None:
                st.success(
                    f"Nice work! '{done_task.title}' is done — "
                    f"next one auto-scheduled for {upcoming.due_date}."
                )
            else:
                st.success(f"'{done_task.title}' marked complete.")

st.divider()

# --- Build the schedule ---
st.subheader("📅 Build Schedule")

if st.button("Generate schedule"):
    if not owner.all_tasks():
        st.warning("Add at least one task first.")
    else:
        scheduler = Scheduler(time_budget=owner.minutes_available)
        scheduler.plan_for_owner(owner, today=date.today())

        st.markdown(f"### Today's Schedule for {owner.name}")
        st.caption(f"{owner.minutes_available} minutes available")

        # Conflict warnings first — most helpful when seen up front, before the
        # owner commits to the plan. One yellow warning per clash, in plain words.
        warnings = scheduler.conflict_warnings(owner)
        if warnings:
            for message in warnings:
                st.warning(f"⚠️ {message}")

        # Planned tasks, priority-first then chronological within each level.
        if scheduler.planned_tasks:
            st.markdown("**Planned for today** (priority first, then time)")
            for t in scheduler.planned_tasks:
                when = f"{t.start_time} · " if t.start_time else ""
                st.success(f"✅ {when}{t.title} ({t.duration_minutes} min) — priority: {t.priority}")
        else:
            st.info("Nothing fit in the available time.")

        # Skipped tasks in a table so it's clear *why* the plan looks the way it does.
        if scheduler.skipped_tasks:
            st.markdown("**⏳ Skipped (not enough time)**")
            st.table(
                [
                    {
                        "Task": t.title,
                        "Duration": f"{t.duration_minutes} min",
                        "Priority": t.priority,
                    }
                    for t in scheduler.skipped_tasks
                ]
            )
