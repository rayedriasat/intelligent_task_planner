# External APIs (Revised)

### OpenRouter API

*   **Purpose:** To provide optional, AI-powered scheduling suggestions.
*   **Integration Notes:** This is a non-critical, progressive enhancement with a strict 8-second timeout and graceful failure handling.

### SMTP Email Service

*   **Purpose:** To send transactional emails for account verification and notifications.
*   **Integration Notes:** Uses Django's built-in SMTP backend and sends all emails asynchronously via Django-Q2.
