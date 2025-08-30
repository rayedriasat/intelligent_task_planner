# Epic 1: Foundation & First Scheduled Task

**Goal:** To establish the project's technical foundation, allow a user to create an account, input a task and their availability, and see that single task intelligently scheduled on a calendar.

### Story 1.1: Project Scaffolding & Core Dependencies

**As a** developer, **I want** a clean Django project with all necessary dependencies installed and configured, **so that** I have a stable and correct foundation for all future development.
**Acceptance Criteria:**
1. A new Django project and a core `planner` app are created.
2. All dependencies are installed via UV and the `pyproject.toml` file is configured.
3. Core Django settings are configured.
4. The project runs locally without errors.

### Story 1.2: User Authentication Setup

**As a** student, **I want** to securely register for an account, log in, and log out, **so that** I can access my personal planner.
**Acceptance Criteria:**
1. Django Allauth is fully integrated and configured.
2. URLs for login, logout, and signup are correctly routed.
3. Users can successfully create an account and log in.
4. The authentication pages are styled according to the project's aesthetic.

### Story 1.3: Core Data Models (`Task` & `TimeBlock`)

**As a** system, **I want** database models for Tasks and user Availability, **so that** I have the foundational schema to store all user-generated planning data.
**Acceptance Criteria:**
1. The `Task` model is created in `models.py` with all fields from FR2.
2. A new `TimeBlock` model is created to store user availability.
3. Database migrations are created and successfully applied for both models.
4. Both models are registered in the Django admin site.

### Story 1.4: Task & Availability Input Forms

**As a** user, **I want** simple forms to create a task and define my weekly availability, **so that** I can provide the system with the necessary data for scheduling.
**Acceptance Criteria:**
1. An authenticated user can access a form to create a new `Task` (with title, deadline, estimated hours).
2. An authenticated user can access a separate form to define their weekly `TimeBlock` availability.
3. Submitting these forms successfully saves the data to the database, linked to the current user.
4. These forms are styled according to the project aesthetic and provide clear user feedback on success or failure.

### Story 1.5: V1 Scheduling Engine (Backend Logic & Unit Tests)

**As a** developer, **I want** a testable Python function that can schedule a single task within a user's availability, **so that** the core, high-risk scheduling logic is built and validated independently.
**Acceptance Criteria:**
1. A Python function, e.g., `calculate_schedule(tasks, time_blocks)`, is created.
2. Given a list containing one task and a list of available time blocks, the function returns a new list of scheduled tasks with `start_time` and `end_time` populated.
3. The function correctly places the task in the first available slot that respects the task's deadline and duration.
4. **Crucially, a suite of unit tests is created to validate this function's logic against various scenarios (e.g., no time available, perfect fit, etc.). The story is "done" when the function passes all tests.**
5. This story involves **no UI changes**.

### Story 1.6: Trigger Scheduling & Display Result on Calendar

**As a** user, **I want** to see my task appear on a calendar after I create it, **so that** I get immediate visual confirmation of the automated scheduling.
**Acceptance Criteria:**
1. After a user successfully saves a new `Task` (from Story 1.4), the `calculate_schedule` function (from Story 1.5) is triggered.
2. The `start_time` and `end_time` of the Task object in the database are updated with the results from the function.
3. The user is redirected to a `/dashboard` page that displays a simple, non-interactive weekly calendar.
4. The newly scheduled task is correctly displayed in its calculated time slot on the calendar.
