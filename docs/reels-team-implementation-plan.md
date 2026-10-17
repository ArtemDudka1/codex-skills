# Reels Team Implementation Plan

**Goal:** Package the approved six-role Reels workflow as a reusable skill.

**Architecture:** Coordinator-led bounded delegation, role-specific English instructions, shared frozen quality profile, immutable review candidates and Russian user communication.

**Tech stack:** Markdown skill package; host-provided subagent and media tools.

## Constraints

Preserve existing repository content and synced project files. Documentation is English; all team chat to the user is Russian. Do not run paid media generation or publish a Reel during setup.

## Tasks

- [x] Create skills/reels-team/SKILL.md and AGENTS.md with explicit invocation, language and authority rules.
- [x] Add six role files, workflow reference, approved design and complete quality profile.
- [x] Add reusable production and review templates without fabricated passing results.
- [x] Validate skill metadata, local links, role coverage and acceptance IDs; review realistic failure cases.
- [ ] Commit only this package and its repository index entry; push to the user-specified repository and verify the remote head.

End-to-end media production is a later invocation and is not part of this setup verification.
