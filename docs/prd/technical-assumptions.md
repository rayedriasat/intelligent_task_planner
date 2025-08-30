# Technical Assumptions

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
