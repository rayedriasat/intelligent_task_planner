# Components

The application is structured as a single Django monolith, with logical separation of concerns.

### Backend Components (Business Logic & Data)

1.  **User & Auth Component:** Manages user identity.
2.  **Task Management Component:** Handles core CRUD logic for tasks.
3.  **Scheduling Engine Service:** Contains the decoupled, testable scheduling algorithm.
4.  **Notification Service:** Manages queuing and sending reminders.
5.  **Productivity Suite Component:** Handles Pomodoro session logging.
6.  **OpenRouter AI Service:** Encapsulates the optional external API integration.

### Frontend Components (Views & Templates)

These are implemented as server-rendered Django Templates with HTMX and Alpine.js.

1.  **Main App Shell & Navigation:** The persistent three-column layout (`base.html`).
2.  **Kanban Board View:** Displays tasks by status with drag-and-drop functionality.
3.  **Interactive Calendar View:** Renders the weekly schedule with manual editing.
4.  **Pomodoro Timer View:** The focused timer interface.
5.  **Reusable Template Partials:** Core building blocks (`GlassCard`, `TaskCard`, `Modal`, etc.) styled according to the design system.
