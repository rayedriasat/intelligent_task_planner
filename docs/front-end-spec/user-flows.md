# User Flows

### Flow: First-Time User Onboarding & Scheduling

*   **User Goal:** To sign up and see their most urgent task scheduled on a calendar with the absolute minimum number of steps.
*   **Entry Points:** Clicking "Get Started" or "Start Planning" from the landing page.
*   **Success Criteria:** The user has an account and can see their single most important task scheduled, confirming the app's core value proposition within seconds of signing up.

**Flow Diagram:**
```mermaid
graph TD
    A[User on Landing Page] --> B(Clicks 'Get Started');
    B --> C[Registration Page];
    C -- Fills Form --> D(Submits Registration);
    D -- Success --> E["Quick-Start" Modal Overlay];
    subgraph "Immediate Onboarding"
      E -- Contains single prompt --> F["What's your most urgent task?<br/>(Title, Deadline, Est. Hours)"];
    end
    F -- User Clicks 'Schedule Task' --> G{System};
    G -- Uses Default Availability --> H[Schedules Task];
    H --> I[Redirect to Dashboard];
    I --> J[Show Calendar View with Task Placed];
    J --> K["Display Call-to-Action:<br/>'Add your availability to build a full schedule!'"];
```
