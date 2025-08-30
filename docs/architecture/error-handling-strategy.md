# Error Handling Strategy

*   **Model:** Standard Python exceptions, with custom exceptions for business logic.
*   **User-Facing Errors:** HTMX will be used to deliver targeted, user-friendly error messages into the UI without full page reloads.
*   **Logging:** Django's built-in logging, configured to include user context.
*   **Transactions:** All multi-step database operations will be wrapped in `transaction.atomic()` to ensure data integrity.
