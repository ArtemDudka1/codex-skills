# Codex Arena Implementation Plan

Approved architecture: DESIGN.md. Implementation proceeds inline in this session.

**Goal:** reusable local Python CLI for evidence-based audit and branch improvement.
**Architecture:** SQLite job ledger, independent Codex subprocess adapter, controlled Git worktrees, deterministic tournament, external verification gates.
**Tech stack:** Python 3.11+, standard library, Git, installed Codex CLI.

## Constraints

Never edit the target checkout or merge/push. All model output is untrusted and validated. Durable artifacts precede ledger completion. Missing usage pauses dispatch. No live model runs during tool development. Model ID is explicit, reasoning is stage-specific. Unknown checks never count as passing. Real usage and quota availability are not inferred from subscription observations.

## Task 1: executable contract and persistence

Files: tests/test_arena.py, codex_arena/state.py, codex_arena/process.py.

- [x] Write tests for interrupted output recovery, exclusive locking, malformed output, missing usage and budget pauses; run them and observe missing implementation failures.
- [x] Implement transactional ledger, artifact hashes, validated responses and process termination.
- [x] Run targeted tests before proceeding.

## Task 2: repository and checks

Files: codex_arena/git.py, codex_arena/checks.py, tests/test_arena.py.

- [x] Exercise temporary Git repositories; assert original branch/HEAD/files stay unchanged.
- [x] Implement base snapshots, candidate commits, check logs and mandatory gates.
- [x] Verify timeout, changed candidate, weakened checks and baseline failure cases.

## Task 3: tournament and CLI

Files: codex_arena/engine.py, codex_arena/prompts.py, codex_arena/cli.py, pyproject.toml.

- [x] Run full 32-participant fake tournament with audit→run and resume; assert call accounting and winner branch.
- [x] Implement scheduling, role-specific schemas, all-findings registry, attacks, defenses, deterministic judge arithmetic and final independent review.
- [x] Verify ties, both candidates invalid, final audit failure, budget cutoff and idempotent completion.

## Task 4: delivery

Files: README.md, examples/*.toml, docs/DESIGN.md.

- [x] Document installation, model selection, universal and AI Factory profiles, recovery and limitations.
- [x] Verify CLI help, install in a temporary environment, all automated tests and compile checks.
- [x] Perform source review and remedy actionable findings; report exact verification and untested live integration.

This plan follows the approved design; commands and test cases are implemented in the named files so they remain executable rather than duplicated in this document.
