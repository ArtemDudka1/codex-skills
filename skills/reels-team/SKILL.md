---
name: reels-team
description: Produce Instagram Reels with a coordinated designer, scriptwriter, code-based editor, sound director and independent reviewer, including timestamped repair cycles. Use when the user invokes the Reels team or requests this multi-agent production workflow.
---

# Reels team

Read [AGENTS.md](AGENTS.md) first. All chat replies MUST be in Russian. Documentation and agent handoffs are English; internal reasoning may be English without disclosing private reasoning. Reel content defaults to Russian unless the brief says otherwise.

## Start

Act as coordinator using [roles/coordinator.md](roles/coordinator.md). Read [references/workflow.md](references/workflow.md) and the current [quality/criteria.md](quality/criteria.md). Create a production folder in the user's active workspace, outside this skill, from [templates/production.md](templates/production.md). Inspect any existing Reel before creating a new version.

A request to produce a Reel authorizes bounded delegation to these specialist roles using available subagent tools. Use the actual tools exposed by the host; do not invent tool names, APIs or model settings. Keep the coordinator active and schedule specialists in batches according to available concurrency slots. Do not create sidebar chats as a substitute for subagents. If delegation is unavailable, state that in Russian and ask whether the user wants a clearly labeled single-agent fallback; never claim independent review in that mode.

Pass each worker the absolute path to AGENTS.md, its role file, the production folder, exact inputs, allowed output paths and acceptance conditions. Workers return English handoffs to the coordinator; any messages directly visible to the user must be Russian. No need for all six roles to run simultaneously.

## Route work

- Visual research and treatment: [roles/designer.md](roles/designer.md).
- Narration and scene structure: [roles/scriptwriter.md](roles/scriptwriter.md).
- Code-based scenes, timing and render: [roles/editor.md](roles/editor.md).
- Voice, music, effects and mix: [roles/sound-director.md](roles/sound-director.md).
- Exact-export acceptance and regression: [roles/reviewer.md](roles/reviewer.md).

Inspect available media tools and assets before promising delivery. Use existing applicable Remotion/media skills when available; the workflow must remain understandable without them. This package contains instructions and templates, not a renderer, TTS service or background daemon. Do not make paid calls without an authorized budget.

## Finish

Follow the immutable candidate and repair workflow. Deliver a playable file, editable source, review evidence and unresolved limitations. Distinguish configured instructions, document-level checks, mocked checks and actual media production. Never describe an unrendered or unreviewed Reel as finished. Do not publish.
