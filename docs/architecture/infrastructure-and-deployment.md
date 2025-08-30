# Infrastructure and Deployment

*   **Tool:** Manual configuration via PythonAnywhere Web UI.
*   **Strategy:** Git-based deployment from the `main` branch.
*   **CI/CD:** GitHub Actions will run the `pytest` suite on every push; failing tests block merges.
*   **Environments:** Local Development and Production on PythonAnywhere.
*   **Rollback:** `git revert` followed by a `git pull` on the server.
