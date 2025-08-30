# Requirements

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
