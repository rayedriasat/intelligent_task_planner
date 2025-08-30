# Coding Standards (Revised)

### Core Standards

*   **Languages & Runtimes:** Python 3.13.1, Django 5.2.4.
*   **Style & Linting:** All Python code **must** be formatted and linted using **`ruff`**.
*   **Test Organization:** Tests **must** be located in the `tests/` directory of the `planner` app.

### Critical Rules

*   **UI Implementation Mandate:** The frontend UI **must** be a faithful implementation of the "Focused Calm" design system defined in `front-end-spec.md`. All styling **must** be achieved by configuring the design tokens in `tailwind.config.js`.
*   **No Direct ORM Calls in Views:** All business logic **must** be handled in the `services/` directory.
*   **Use Asynchronous Tasks for I/O:** Email sending **must** be executed asynchronously using Django-Q2.
*   **Environment Variables:** Secrets **must not** be hardcoded.
*   **Atomic Transactions:** Multi-write database operations **must** be atomic.

### Accessibility Standards

*   **Semantic HTML:** Use appropriate HTML5 elements for their intended purpose.
*   **Form Labeling:** Every form input **must** have an associated `<label>`.
*   **Keyboard Navigability:** All interactive elements **must** be keyboard-accessible.
*   **Focus Indicators:** Do not remove default browser focus indicators without a clear custom alternative.
