# Epic 2: Full Scheduling & Task Management

**Goal:** First, to deliver a complete, standalone task management system with list and Kanban views. Second, to enhance this system with a powerful, interactive scheduling engine and calendar view.

### Story 2.1: Full Task Management UI

**As a** student, **I want** a main dashboard where I can view, create, edit, and delete all of my tasks, **so that** I have full control over my academic workload in one place.
**Acceptance Criteria:**
1. The dashboard displays a list of all the user's tasks.
2. The "Create Task" form is now integrated and includes all `Task` model fields.
3. Users can edit and delete existing tasks.

### Story 2.2: Kanban Board & Progress Tracking

**As a** student, **I want** a Kanban board to visually track my progress and update task statuses, **so that** I can easily manage my workflow.
**Acceptance Criteria:**
1. A Kanban board view is created with "To Do", "In Progress", and "Completed" columns.
2. All of the user's tasks are displayed as cards in the appropriate column.
3. Dragging cards between columns updates the task's `status` in the database (FR9).
4. When a task is moved to "Completed", the system logs the completion time (FR8).

### Story 2.3: Advanced Scheduling Engine (Backend Logic)

**As a** system, **I want** a robust backend function that can take a list of tasks and availability, and return a fully optimized schedule, **so that** the core scheduling intelligence is built and testable.
**Acceptance Criteria:**
1. The `calculate_schedule` function is enhanced to handle a full list of tasks.
2. It correctly implements **prioritization** (by deadline/priority), **overload detection**, and **intelligent task splitting** (respecting `min_block_size`).
3. The function returns two lists: `scheduled_tasks` and `unscheduled_tasks`.
4. A comprehensive suite of unit tests is created to validate all engine logic. **This story involves no UI changes.**

### Story 2.4: Interactive Calendar & Engine Integration

**As a** student, **I want** to see my fully optimized schedule on an interactive calendar, **so that** I can visualize my week and make manual adjustments.
**Acceptance Criteria:**
1. An interactive calendar view is created.
2. When the page loads, it calls the `calculate_schedule` function and displays the `scheduled_tasks` on the calendar.
3. Users can drag-and-drop and resize tasks, and these changes are saved (FR5).
4. A "lock" option is available on manually moved tasks (FR6).

### Story 2.5: "Re-optimize Week" & Unscheduled Tray

**As a** student, **I want** to be able to re-optimize my week and see any tasks that couldn't fit, **so that** my schedule stays up-to-date and no work is forgotten.
**Acceptance Criteria:**
1. A prominent "Re-optimize Week" button triggers the `calculate_schedule` function on all unlocked tasks (FR12).
2. A persistent "Unscheduled Tasks Tray" is added to the UI (FR13).
3. The `unscheduled_tasks` returned by the engine are displayed in this tray.

### Story 2.6: "Sacrifice Mode" for Urgent Interruptions

**As a** student, **I want** a simple way to add an urgent task to a full schedule, **so that** I can handle unexpected high-priority work.
**Acceptance Criteria:**
1. The interactive "Sacrifice Mode" (FR4) is implemented.
2. When a user adds an urgent task with no free time, this mode is triggered.
3. Dragging the new task over existing events on the calendar "bumps" those events into the Unscheduled Tasks Tray and schedules the new one.
