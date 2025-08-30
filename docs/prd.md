# Intelligent Task Planner Project Product Requirements Document (PRD)

## Goals and Background Context

### Goals

*   Deliver a functional, responsive web application that meets all defined MVP requirements within the 4-week timeline.
*   Reduce student stress and planning overhead by providing an automated, intelligent scheduling solution.
*   Ensure the application is intuitive and valuable, targeting a System Usability Scale (SUS) score above 80.
*   Meet all non-functional requirements for performance (≤ 2s schedule generation), reliability (99% uptime), and scalability (up to 500 concurrent users).

### Background Context

The Intelligent Task Planner project aims to solve the common problem of inefficient and stressful manual planning faced by university students. By creating a specialized web application, we will provide a tool that moves beyond simple to-do lists into the realm of automated time management. The system will process a student's tasks, deadlines, and available time to generate an optimized weekly schedule.

This PRD defines the requirements for an MVP inspired by the simplicity of tools like TickTick but tailored for academic needs. The core of the MVP is a robust, rule-based scheduling engine, with a progressive enhancement path to include optional AI-driven suggestions via the OpenRouter API.

### Change Log

| Date | Version | Description | Author |
| :--- | :--- | :--- | :--- |
| 2025-08-02 | 1.0 | Initial PRD draft created from Project Brief. | John (PM) |
| 2025-08-05 | 1.1 | Updated Branding section to reference `front-end-spec.md` as the single source of truth for UI. Corrected dependency management reference. | Winston (Architect) |

## Requirements

### Functional

1.  **FR1: User Account:** Users can register, login, logout, reset password, and update their profile (e.g., notification preferences). Must support email verification.
2.  **FR2: Task Management:** The system will support full CRUD operations for tasks with fields: title, description, type, deadline, priority, estimated hours, tags, recurrence, and an optional `min_block_size` to guide the scheduling engine.
3.  **FR3: Time-Block Input:** Users can input weekly recurring or ad-hoc free time slots.
4.  **FR4: Auto-Schedule:** The core scheduling engine must perform:
    *   **Feasibility Check (Overload):** Before scheduling, check if total required time exceeds available time and prompt the user for a resolution strategy ("Compress Schedule" or "Prioritize & Schedule").
    *   **Intelligent Task Splitting (Fragmentation):** Respect the `min_block_size` on tasks, only placing them in slots of adequate size.
    *   **Conflict Resolution (Interruptions):** When an urgent task is added with no free time, initiate an interactive "Sacrifice Mode" for the user to resolve the conflict.
5.  **FR5: Manual Edit:** Users can drag-and-drop to move, resize, or split tasks. These manual placements are treated as direct overrides.
6.  **FR6: Event Locking:** When a user manually places or edits an event, they must have the option to "lock" it, making it a fixed appointment.
7.  **FR7: Notifications:** The system will send time-based reminders (e.g., 24h and 1h before tasks) via browser push or email.
8.  **FR8: Progress Tracking:** Users can mark tasks as in-progress or completed, and the system logs actual vs. estimated time for analytics.
9.  **FR9: Kanban Board View:** The application must provide a Kanban board view ("To Do", "In Progress", "Completed") where users can drag-and-drop tasks to update their status.
10. **FR10: Pomodoro Timer:** An integrated timer for 25-5 minute focus cycles within tasks, with session tracking.
11. **FR11: "Quick-Start" Onboarding:** The first-time user experience must be a single prompt ("What's your most urgent task?") to schedule one task immediately.
12. **FR12: Adaptive Re-optimization:** The UI must feature a prominent "Re-optimize Week" button that re-runs the scheduler on all uncompleted and unlocked tasks.
13. **FR13: Unscheduled Tasks Tray:** A persistent, clearly visible area (e.g., a collapsible sidebar) to hold all tasks that could not be placed or were bumped.
14. **FR14: AI Scheduling Enhancement (Optional):** The application will integrate with the OpenRouter API to provide an optional, AI-powered scheduling suggestion. This feature must be a progressive enhancement and the system must remain fully functional if the API is unavailable.

### Non Functional

1.  **NFR1: Performance:** Schedule generation must be ≤ 2 seconds; page loads must be ≤ 1 second on standard hardware.
2.  **NFR2: Usability:** The UI must be intuitive and responsive (mobile/desktop) with a clean design aesthetic similar to TickTick and include accessibility features (e.g., keyboard navigation).
3.  **NFR3: Security:** The system must provide user authentication, data encryption, and privacy (e.g., GDPR compliance) with secure API endpoints.
4.  **NFR4: Scalability:** The system must support up to 500 concurrent users with a database optimized for multi-user access.
5.  **NFR5: Reliability:** The application must maintain 99% uptime and handle edge cases like time overlaps with graceful errors.
6.  **NFR6: Compatibility:** The application must work on major modern browsers (Chrome, Firefox) and be responsive for various device sizes.
7.  **NFR7: Maintainability:** The codebase must follow Django best practices, and UV will be used for dependency management.
8.  **NFR8: External API Resilience:** The integration with the OpenRouter API (FR14) must timeout after 8 seconds. In the event of a timeout or any API error, the system must fail gracefully, clearly inform the user that AI suggestions are currently unavailable, and ensure all core scheduling functionalities remain unaffected.

## User Interface Design Goals

### Overall UX Vision

The user experience will be clean, intuitive, and efficient, drawing inspiration from the simplicity of modern productivity tools like TickTick. The primary goal is to minimize cognitive load for the user by providing a clear, visually organized schedule that is easy to understand at a glance. The interface should feel empowering, transforming the complex task of academic planning into a manageable and even engaging process.

### Key Interaction Paradigms

*   **Drag-and-Drop:** Core to the user experience will be the ability to manually adjust the schedule by dragging, resizing, and splitting task blocks directly on the calendar view.
*   **Visual Status Management:** A Kanban board will provide a clear, tactile way for users to update task status.
*   **Interactive Conflict Resolution:** The "Sacrifice Mode" will be a highly visual, interactive overlay that allows users to resolve scheduling conflicts by physically dragging a new task over existing ones.

### Core Screens and Views

*   **Landing Page:** A professional, welcoming page that clearly communicates the application's value proposition.
*   **Dashboard / Kanban View:** The main user hub, displaying tasks in "To Do", "In Progress", and "Completed" columns.
*   **Weekly Calendar View:** A visual representation of the generated schedule, showing time-blocked tasks for the week.
*   **Pomodoro Timer View:** A dedicated, focused interface for the Pomodoro sessions.

### Accessibility: WCAG AA

The application will adhere to Web Content Accessibility Guidelines (WCAG) 2.1 Level AA as a target, ensuring it is usable by students with disabilities, with a focus on keyboard navigation and screen reader compatibility.

### Branding

The visual identity will follow a modern, clean aesthetic called "Focused Calm," featuring both light and dark themes. The design will utilize soft colors, rounded corners, and a refined glass morphism effect for key cards and modals, with a vibrant yet professional color palette.

**Implementation & Aesthetic Reference**
*   **Primary Reference:** The **`front-end-spec.md`** document is now the definitive source of truth for the application's aesthetic.
*   **Tech Stack Adherence:** The implementation **must** adhere to the project's official tech stack (Django Templates, TailwindCSS, HTMX, AlpineJS).
*   **Design Rules:** Developers must implement the design tokens (colors, typography, spacing, etc.) as defined in the `front-end-spec.md` and configure them within the `tailwind.config.js` file to achieve a UI that is visually and experientially identical to the new design direction.

### Target Device and Platforms: Web Responsive

The application will be a single responsive web application, providing a seamless and consistent experience on both desktop and mobile browsers.

## Technical Assumptions

### Repository Structure: Monorepo

*   **Decision:** The project will be developed within a single repository (monorepo).
*   **Rationale:** This simplifies development workflows, dependency management (via UV), and ensures that frontend templates and backend logic are tightly synchronized, which is crucial for the HTMX-driven architecture.

### Service Architecture: Monolith

*   **Decision:** The application will be built as a single, cohesive Django monolith.
*   **Rationale:** Given the 4-week timeline and the interconnected nature of the features (task management, scheduling, display), a monolithic architecture provides the fastest path to a functional MVP, reducing the complexity of deployment and inter-service communication.

### Testing Requirements: Unit + Integration

*   **Decision:** The testing strategy will prioritize unit tests for business logic and integration tests for user workflows.
*   **Rationale:** The core scheduling engine's logic (FR4) is the highest technical risk and must be covered by extensive unit tests. Integration tests will then verify that the full flow—from task creation to schedule display—functions as expected. End-to-end testing is out of scope for the MVP to conserve time.

### Additional Technical Assumptions and Requests

*   **Primary Tech Stack:** The project will strictly adhere to the specified stack: Django 5, Python 3.13.1, TailwindCSS, HTMX, and AlpineJS.
    *   **Rationale:** This "lean" stack is chosen explicitly to maximize simplicity, reduce JavaScript overhead, and align with the rapid development goals. No other frameworks are to be introduced.
*   **Database:** MySQL will be the relational database, managed via the built-in Django ORM.
    *   **Rationale:** Chosen for its reliability and strong compatibility with Django and PythonAnywhere.
*   **Authentication:** Django Allauth is the designated package for handling user authentication.
    *   **Rationale:** It is a well-supported, comprehensive solution that handles email verification and social auth (Google) out of the box, saving significant development time.
*   **Deployment:** The exclusive deployment target for the MVP is PythonAnywhere's free tier.
    *   **Rationale:** This is a hard project constraint. The architecture and resource usage must be designed to fit within its limitations.
*   **External AI API:** The system will integrate with a free AI model from OpenRouter as a **non-critical, progressive enhancement**.
    *   **Rationale:** This feature must be architected to fail gracefully. The user experience must be complete and functional *without* the AI integration.

## Epic List

*   **Epic 1: Foundation & First Scheduled Task:** Establish the project foundation, user accounts, and implement the "Quick-Start" onboarding flow to schedule a single task onto a basic calendar view.
*   **Epic 2: Full Scheduling & Task Management:** Expand on the foundation by implementing full task CRUD, the advanced scheduling engine (overload, splitting, conflict resolution), manual calendar editing, and the Kanban view.
*   **Epic 3: Productivity Suite & Integrations:** Layer on the advanced productivity tools, including the Pomodoro timer, notifications, progress tracking, and the optional OpenRouter AI scheduling enhancement.

## Epic 1: Foundation & First Scheduled Task

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

## Epic 2: Full Scheduling & Task Management

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

## Epic 3: Productivity Suite & Integrations

**Goal:** To enhance the core scheduling application with advanced productivity tools (notifications, Pomodoro timer) and to integrate the optional OpenRouter AI scheduling suggestions as a progressive enhancement.

### Story 3.1: Task Notifications

**As a** student, **I want** to receive timely reminders for my scheduled tasks, **so that** I don't miss important deadlines or study blocks.
**Acceptance Criteria:**
1. Users can set their notification preferences in their profile.
2. A recurring backend task (Django-Q2) sends notifications for upcoming tasks.
3. Both browser push and email notifications are supported.

### Story 3.2: Pomodoro Timer UI

**As a** student, **I want** an interface to run Pomodoro focus sessions for my tasks, **so that** I can improve my focus.
**Acceptance Criteria:**
1. A Pomodoro timer view is created, matching the mockups.
2. The UI includes controls to start, pause, and reset the timer.
3. The timer correctly cycles through 25-minute focus and 5-minute break periods.
4. The UI allows a user to select an "In Progress" task to associate with the session.

### Story 3.3: Pomodoro Session Tracking (Backend)

**As a** system, **I want** to save the results of completed Pomodoro sessions, **so that** this data can be used for future analytics.
**Acceptance Criteria:**
1. An API endpoint is created to log a completed Pomodoro session.
2. When a focus session is completed, the frontend calls this endpoint with the task ID.
3. The backend saves the session data, linking it to the task.

### Story 3.4: OpenRouter AI Integration Service (Backend)

**As a** developer, **I want** a testable backend service that can call the OpenRouter API with a user's data and handle the response, **so that** the external integration is built and validated in isolation.
**Acceptance Criteria:**
1. A Python function is created that takes a list of tasks and time blocks.
2. The function correctly formats and sends the data to the OpenRouter API.
3. The service correctly parses a successful response from the AI.
4. The service adheres to NFR8, gracefully handling API errors and timeouts.
5. A suite of unit tests is created to mock the API call and validate both success and failure scenarios. **This story involves no UI changes.**

### Story 3.5: Display AI Scheduling Suggestion (UI)

**As a** student, **I want** the option to see an AI-powered schedule suggestion, **so that** I can explore an alternative, potentially more optimized plan.
**Acceptance Criteria:**
1. A "Get AI Suggestion" button is added to the calendar UI.
2. Clicking the button calls the backend service from Story 3.4.
3. The UI displays a loading state and handles success/error responses from the service.
4. On success, the AI schedule is displayed as a preview.
5. The user has clear options to accept or dismiss the AI's suggestion.