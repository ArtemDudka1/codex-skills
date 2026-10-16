---
name: codex-arena
description: Run a resumable multi-agent tournament for deep audit and improvement of a local Git project using Codex CLI. Use when the user asks for Codex Arena, a tournament of auditors, or comprehensive project polishing with isolated candidate branches and objective checks.
---

# Codex Arena

Use the bundled CLI to audit and improve the user's current project. This skill is
self-contained: `codex_arena/`, `bin/codex-arena`, `examples/`, and the detailed
[README](README.md) are next to this file. Resolve paths from this skill's actual
location; do not assume the project under audit is the skill directory.

## User intent and scope

- A request to run Arena/audit/improve authorizes that requested operation. Explain
  the scale briefly and proceed when target, task and checks are known; do not ask
  for the same authorization again. Questions about installation or usage do not
  authorize a real tournament.
- Keep the task within the user's brief. Audit and refinement can improve a working
  prototype; a major product redesign needs a concrete brief/reference first.
- Preserve visual direction and distinguish mocked flows from connected integrations.
  For AI Factory, adapt [examples/ai-factory-task.md](examples/ai-factory-task.md).
- Do not push, publish, deploy or merge the tournament winner unless separately
  requested. Keep original checkout and main unchanged.

## Prepare and run

1. Identify the intended project path, read its AGENTS.md/README and inspect Git
   status. Use the current project's actual checkout, not a guessed directory.
   If it is not a Git repository or has unsaved changes, explain the concrete issue;
   do not stash, commit user edits or turn synced reference folders into a repository.
2. Read the bundled README for flags, state/recovery and limitations. Check for a
   compatible saved run with `status` before starting another one. Multiple runs
   require their explicit ID. Do not use `--new` to evade an interrupted run.
3. Prepare a standalone task and TOML verification profile outside the target
   checkout. Adapt the bundled examples to actual project commands; absent tests,
   lint or typecheck are missing coverage, never passing checks. UI projects need
   real browser-flow checks beyond syntax/build. Protected paths must include custom
   verification scripts/configuration. Honor project-specific source restrictions.
4. Set the intended CLI model ID explicitly. Use the configured CLI model or the
   user's chosen model; do not silently substitute. `doctor` checks flags, not model
   access. If authentication/model access fails, preserve state and report it.
5. Invoke via `python3 "<skill-root>/bin/codex-arena" COMMAND "<project>" ...`.
   Run `doctor` and `plan` first. Default: 32 participants, two concurrent processes;
   a full run has 197 model jobs before retries, not 32 simultaneous agents. Explain
   that it consumes Codex usage. Token thresholds are planning limits, not a verified
   subscription allowance or guaranteed hard cap.
6. For audit-only use `audit`; for audit plus implementation use `run`, with
   `--agents 32 --config "<profile>" --task-file "<task>"` on the first invocation.
   A compatible existing audit can be continued with `run` without repeating it.
   Use `resume` after interruption and retain the state directory and all worktrees.
7. Keep the long-running process supervised and report meaningful stage changes.
   If an API/terminal tool returns a process/session ID, keep following that process;
   do not mistake dispatch for completion or start a second orchestrator.

## Recovery and delivery

A normal `resume` recovers valid saved answers. Never synthesize a judge verdict or
silently mark failed/unknown usage as zero. `--retry-interrupted` explicitly spends
another attempt; interrupted editor changes are first kept on recovery branches.
Read the README before using it. Reconcile unknown usage only from confirmed data.

Report `ready`, `paused` or `needs-review` honestly. Deliver branch/SHA, diff,
external check evidence, raw findings versus independently reviewed fixes,
unresolved blockers, usage and state location. Both failed candidates or a final
blocker stop v0.1 for manual review; there is no automatic final repair loop.
Do not call a branch ready merely because an agent says its tests passed.
