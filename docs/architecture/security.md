# Security

*   **Authentication & Authorization:** Handled by `django-allauth`. All sensitive views will be protected and will verify data ownership.
*   **Input Validation:** All user input will be validated via Django Forms to prevent injection attacks. No raw SQL is permitted.
*   **Secrets Management:** `django-environ` will be used to load secrets from environment variables; no secrets in source code.
*   **Django Protections:** CSRF, XSS, and Clickjacking protections will be enabled and enforced.
