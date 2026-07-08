import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# Persist the Owner across reruns instead of recreating it each time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", minutes_available=60)

owner = st.session_state.owner

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# --- Owner settings ---
st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)
owner.minutes_available = st.number_input(
    "Minutes available today", min_value=0, max_value=1440, value=owner.minutes_available
)

st.divider()

# --- Add a pet ---
st.subheader("Add a Pet")
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
    st.info("No pets yet. Add one above.")

st.divider()

# --- Add a task to a pet ---
if owner.pets:
    st.subheader("Add a Task")
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

    if st.button("Add task"):
        selected_pet.add_task(
            Task(title=task_title, duration_minutes=int(duration), priority=priority)
        )
        st.success(f"Added '{task_title}' to {selected_pet.name}.")

    # Show each pet's current tasks (read straight from the Owner's data).
    for pet in owner.pets:
        st.markdown(f"**{pet.name}** ({pet.species}, {pet.breed})")
        if pet.tasks:
            st.table(
                [
                    {
                        "title": t.title,
                        "duration_minutes": t.duration_minutes,
                        "priority": t.priority,
                        "done": t.done,
                    }
                    for t in pet.tasks
                ]
            )
        else:
            st.caption("No tasks yet.")

st.divider()

# --- Build the schedule ---
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if not owner.all_tasks():
        st.warning("Add at least one task first.")
    else:
        scheduler = Scheduler(time_budget=owner.minutes_available)
        scheduler.plan_for_owner(owner)

        st.markdown(f"### Today's Schedule for {owner.name}")
        st.caption(f"{owner.minutes_available} minutes available")

        if scheduler.planned_tasks:
            for t in scheduler.planned_tasks:
                st.write(f"✅ {t.title} ({t.duration_minutes} min) — priority: {t.priority}")
        else:
            st.write("Nothing fit in the available time.")

        if scheduler.skipped_tasks:
            st.markdown("**Skipped (not enough time):**")
            for t in scheduler.skipped_tasks:
                st.write(f"⏳ {t.title} ({t.duration_minutes} min) — priority: {t.priority}")
