# PawPal+ Project Reflection

## 1. System Design

**Core user actions**

These are the three core actions a user should be able to perform in PawPal+:

1. **Set a priority on each task.** Every care task the user adds has a level of importance (for example: high, medium, low). This priority system lets the scheduler decide which tasks matter most when time is limited, so the essentials get done first.

2. **Create accounts for different pets.** The user can add multiple accounts for various pets, each with its own species and breed. This keeps each pet's care separate and lets the owner manage several animals from one app.

3. **Track what's done and what's left.** The user can see which tasks have been completed and which still need to be done, so it's always clear what remains for the day.

**a. Initial design**

My initial UML design has four classes:

- **Owner** — holds the user's info (name, minutes available per day) and their list of pets. Responsible for adding/removing pets and requesting a plan.
- **Pet** — holds a pet's info (name, species, breed) and its list of tasks. Responsible for adding, removing, and editing its own tasks.
- **Task** — represents a single care task (title, duration, priority, done status). Responsible for marking itself done and editing its details.
- **Schedule** — takes a pet's tasks and the owner's time budget and builds the daily plan. Responsible for sorting tasks by priority and generating the schedule.

An Owner owns many Pets, a Pet has many Tasks, and the Schedule uses those Tasks to produce the plan.

**b. Design changes**

Yes. After reviewing my skeleton, I made four changes so the classes would actually support the behavior I wanted:

1. **Gave `Task` a unique `id`.** Because `Task` is a dataclass, two tasks with the same title, duration, and priority counted as equal. That meant removing or editing a task could hit the wrong one when a pet had look-alike tasks. Each task now gets a unique id from a counter, and `remove_task`/`edit_task` take a `task_id` instead of a whole `Task` object so they always target the right one.

2. **Settled how `Schedule.generate_plan` works.** Originally it was unclear whether the plan was built in the constructor, by mutating the object, or by returning a new one. I standardized on: `generate_plan` fills in the schedule and returns `self`. This keeps one clear pattern instead of two competing ones.

3. **Added `skipped_tasks` to `Schedule`.** The old design only stored the tasks that made it into the plan, so when a task got dropped for lack of time it just disappeared. Since a core goal is explaining *why* the plan looks the way it does, I now keep the left-out tasks so the UI can show what was skipped and why.

4. **Made `done` actually matter.** `Task.done` existed but nothing used it. `generate_plan` now skips tasks that are already done before scheduling, which supports the "track what's done vs. what's left" action.

I also added a `PRIORITY_ORDER` mapping so priority sorting is well-defined instead of relying on raw string comparison, and gave `Schedule` an optional reference to its `Pet` so a plan knows which pet it belongs to (useful for labeled output like "Daily plan for Biscuit").

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
