# Verification — Codex Arena 0.1.0

Date: 2026-10-16. Platform: macOS, Python 3.13.2.

- Automated tests: **34 passed**, 73.139 seconds. Full output: TEST-RESULTS.txt.
- Full 32-participant tournament: 197 completed model jobs using the fake executable at the Codex boundary. Real Git repositories/worktrees, SQLite, check subprocesses, branch commits and patch export are exercised.
- Original main/HEAD/source remain unchanged. Resume of a completed run makes no additional model calls.
- Recovery: saved answer with interrupted ledger, interrupted editor with recovery branch, crash after commit, PID birth guard, unknown usage reconciliation, bounded retry and stale evidence rejection.
- Gates: mandatory-check failure, both candidates ineligible, protected verification config, final blocker, malformed responses and malformed recovered judges.
- Process timeout/cancellation, budget wave reservation, cross-review finding retention and exported patch applicability checked.
- Python modules compile successfully.
- Wheel built, installed in a temporary isolated environment, entry point/help/version/doctor verified outside source directory. Every packaged Python module was compared byte-for-byte to source.
- Local Codex CLI capability check passed: codex-cli 0.162.0-alpha.17.2.
- No live model call, access-to-model check, subscription budget measurement, real 5-hour interruption, AI Factory run or deployment was performed.
- First-version limitations are listed explicitly in README.md and DESIGN.md. Passing these tests does not certify absence of all bugs.
