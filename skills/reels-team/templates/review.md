# Candidate review

Template only. No gates are pre-marked PASS.

## Identity

Record production ID, candidate version/path/SHA-256, frozen profile checksum, reviewer and review time.

## Evidence

Record commands/tools, outputs, normal-speed full playback/listening, frame checks, phone preview and phone-speaker check. Label unperformed checks explicitly.

## Gate results

Create one row for EVERY criterion in the frozen acceptance profile.

| Criterion ID | PASS / FAIL / UNVERIFIED / NOT_APPLICABLE | Observation | Evidence path and timestamp | Reason for non-applicability |
| --- | --- | --- | --- | --- |

## Defects

| Defect ID | Criterion | Scene | Start/end | Expected | Observed | Evidence | Owner | Requested correction | Resolution candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Verdict

ACCEPTED only if all applicable gates PASS. Otherwise REPAIR_REQUIRED, BLOCKED or NEEDS_USER_DECISION. Record repair round, remaining failures, review limits and concise rationale. A missing measurement is UNVERIFIED, never NOT_APPLICABLE.
