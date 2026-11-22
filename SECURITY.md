# Security policy

## Reporting a vulnerability

Please report security issues privately via GitHub: **Security → Report a vulnerability** in this repository.
Do not open a public issue. You will get an answer within 7 days.

## Design

- The web UI is only reachable through Home Assistant Ingress; the server accepts connections from the Ingress proxy only (`172.30.32.2`).
- No secrets in the repository. The add-on uses the `SUPERVISOR_TOKEN` provided at runtime.
- All database access is parameterised; all user input is validated and size-limited.
- XML imports reject DTDs and entities (XXE); CSV exports neutralise spreadsheet formulas.
- Strict Content-Security-Policy, no inline scripts, all API text is escaped in the UI.
- Photo folders are mounted read-only; the scanner never follows symlinks out of the configured folders.
- Optional routing (OSRM) sends only the start and end point of a gap; it can be switched off.
- CI runs tests, Ruff, Bandit, pip-audit, CodeQL and Dependabot.

## Privacy

Location history is personal. It is stored only in the add-on's `/data` folder (included in Home Assistant backups).
The repository contains invented sample data only.
