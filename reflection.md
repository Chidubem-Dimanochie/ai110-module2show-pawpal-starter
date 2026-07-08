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

During Phase 3, I expanded the scheduler with additional functionality. I added different sorting options, including sorting by time and duration, as well as flexible task filtering by pet, status, and priority. I also added time-based scheduling with conflict detection, allowing the system to identify overlapping tasks.

I implemented recurring tasks by using task frequency to generate future occurrences after completion. Daily and weekly tasks now create new due dates automatically, while one-time tasks do not repeat. These changes made the scheduler more practical by improving organization, handling real scheduling scenarios, and supporting long-term task management.


---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler considers factors like available time, task priority, completion status, scheduled times, and recurring tasks. I prioritized these constraints because they directly affect what tasks can realistically be completed in a day and help create a useful schedule for the owner.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

One tradeoff is that the scheduler reports time conflicts instead of automatically rescheduling tasks. This keeps the system simple and transparent by allowing the owner to decide how to handle conflicts rather than moving tasks without permission.
---

## 3. AI Collaboration

**a. How you used AI**
I used my AI coding assistant throughout every phase of the project. It helped brainstorm the class design, assisted with implementing and connecting features, and generated tests while suggesting edge cases I hadn't considered.

The most helpful prompts were specific and based on my actual project files. Asking the AI to explain its code before I used it also helped me understand the implementation instead of simply copying it.


**b. Judgment and verification**
I verified the AI's output by running the code, not just reading it. I made sure all tests passed with `pytest`, ran the application end-to-end, and checked that the behavior matched the intended design.

One suggestion I chose not to follow was optimizing `detect_conflicts` with a more complex algorithm. Since the app only handles a small number of daily tasks, I kept the simpler implementation because it was easier to read, test, and maintain.

**c. AI Strategy**

**Which AI coding assistant features were most effective for building your scheduler?**

The most helpful features were attaching project files so the AI understood my actual codebase, making coordinated edits across multiple files to keep everything consistent, and generating tests with useful edge cases I might have overlooked.

**One AI suggestion I rejected or modified to keep the design clean.**

The AI suggested automatically rescheduling conflicting tasks, but I changed it to only report conflicts. This kept the `Scheduler` focused on detecting issues instead of making scheduling decisions for the user.

**How separate chat sessions for different phases helped me stay organized.**

I used separate chat sessions for design, implementation, testing, UI, and documentation. This kept each conversation focused, made it easier to revisit earlier decisions, and prevented different parts of the project from getting mixed together.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I tested the app's core features, including sorting, filtering, conflict detection, and recurring task behavior (daily, weekly, and one-time tasks). These tests were important because they verified the main functionality and helped catch bugs whenever changes were made.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I am fairly confident that the scheduler works correctly, around 4/5. The core features are well-tested, with all tests passing and coverage for important cases like sorting, budgeting, conflicts, and recurring tasks. I also verified the program by running it end-to-end and comparing the results with the expected behavior.

I would still improve input validation and clarify some edge cases, such as late-completed recurring tasks, invalid times or durations, and tasks that cross midnight. These are not confirmed bugs, but areas where the behavior could be better defined.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I was most satisfied with how the four classes remained organized as the system grew. Each class had a clear responsibility, which made adding features like sorting, conflict detection, and recurring tasks easier without rewriting existing code. Having 29 passing tests also gave me confidence that the different parts of the system worked together correctly.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

 I would add stronger input validation and define more edge cases, such as how late-completed recurring tasks should behave. I would also make the scheduling and display logic follow one consistent priority and time-based ordering rule to make the system easier to understand.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

My biggest takeaway is that good class design makes future changes much easier. I also learned that AI works best as a collaborator that helps explore ideas and find issues, but its suggestions still need to be tested and verified before being added.
