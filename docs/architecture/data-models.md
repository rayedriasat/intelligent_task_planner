# Data Models

The following data models will be implemented using the Django ORM.

### User (Provided by Django & Allauth)

*   **Purpose:** Manages user authentication, sessions, and core profile information.
*   **Relationships:** A `User` has a one-to-many relationship with `Task`, `TimeBlock`, and `PomodoroSession`.

### Task

*   **Purpose:** To store all information related to a single task that a user needs to complete.
*   **Key Attributes:** `user`, `title`, `description`, `deadline`, `priority`, `estimated_hours`, `min_block_size`, `status`, `start_time`, `end_time`, `is_locked`, `actual_hours`.
*   **Relationships:** Belongs to one `User` and can have many `PomodoroSession`s.

### TimeBlock

*   **Purpose:** Stores the blocks of time a user has marked as available for tasks to be scheduled into.
*   **Key Attributes:** `user`, `start_time`, `end_time`, `is_recurring`, `day_of_week`.
*   **Relationships:** Belongs to one `User`.

### PomodoroSession

*   **Purpose:** Logs a completed 25-minute Pomodoro focus session against a specific task.
*   **Key Attributes:** `task`, `start_time`, `end_time`.
*   **Relationships:** Belongs to one `Task`.
