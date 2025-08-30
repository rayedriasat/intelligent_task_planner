# Epic 3: Productivity Suite & Integrations

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