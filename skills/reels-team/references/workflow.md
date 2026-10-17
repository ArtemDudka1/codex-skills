# Production workflow

## States

BRIEF → TREATMENT → SCRIPT_LOCK → NARRATION → ASSEMBLY → REVIEW → ACCEPTED.
REVIEW failure → REPAIR → new candidate → REVIEW. Missing resources → BLOCKED with an actionable explanation. Exhausted repair budget → NEEDS_USER_DECISION. ACCEPTED requires every applicable gate to pass against the same candidate checksum.

## Coordination

Create production.md from the template. Ask only for critical missing information, such as the topic; infer reversible preferences from the request and document them. Do not reuse an old video's style or voice as confirmed preference without inspecting the artifact or receiving user direction. Default media profile: Russian content, 1080×1920, 30 fps; choose duration to fit one idea and record it before scripting.

Designer and writer may explore concurrently. Reconcile style with the actual script, then freeze the brief, script, scene plan and a complete copy of quality/criteria.md as acceptance-profile.md. Record profile version and checksum. Any pre-production exception needs an explicit reason and user decision; the reviewer cannot introduce exceptions after seeing failures.

Sound director creates real narration and phrase timings. Editor can prepare components concurrently but must derive final duration from real audio. Maintain stable scene IDs and one coordinator-owned timeline. Sound director proposes cues; coordinator serializes timing changes. Source edits invalidate existing renders.

## Task contract

Every assignment includes role, production ID, task ID, exact input paths, allowed output paths, dependencies, expected deliverables, applicable gates and budget. Worker handoff includes created/changed paths, evidence, unresolved assumptions and READY or BLOCKED status. Report only concise rationale, not private chain-of-thought. English handoffs go to coordinator; Russian chat goes to user.

## Review

Candidate directory: renders/v001/, v002/, etc. Never overwrite reviewed output. Record source revision or source checksum manifest, media checksum, duration, fps, profile checksum, asset manifest and render command. The frozen profile is authoritative even if package defaults later change. Reviewer receives the exact export and frozen profile, not just source code or an editor's success claim.

Review technical integrity, every scene and transition, text reading time, meaningful visual events and full audio/video playback. Maintain a result for every criterion ID. NOT_APPLICABLE requires a concrete reason; a missing capability is UNVERIFIED. Store measurements separately from editorial judgments. Phone listening unavailable means A03 remains UNVERIFIED until a real phone check is supplied.

Each defect uses the review template. Route script/claim problems to writer, style/composition problems to designer, timing/layout problems to editor, and mix/pronunciation problems to sound director. Coordinator resolves cross-role dependencies. After repairs, re-render and recheck all gates, not only the cited interval. Keep the original issues linked to their resolution and replacement candidate.

After three repair rounds, stop and report remaining failures in Russian. Do not accept a lower-quality file or loop indefinitely. Final report links media, source and review report and distinguishes automatic checks, actual listening/playback and any user-dependent checks.

## Post-publication

Only analyze real user-supplied or authorized analytics. Actual retention and gaze cannot be measured from an export. Compare at equal publication age; preserve missing data. Apply one or two documented hypotheses to the next Reel.
