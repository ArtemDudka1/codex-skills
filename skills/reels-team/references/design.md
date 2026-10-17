# Reels production team — proposed specification

Status: Approved design. Instruction package implemented; end-to-end media production remains untested.
Version: 0.1 — 2026-10-17
Documentation language: English. User-facing conversation: Russian.

## Purpose

Produce Instagram Reels through specialist agents, shared production artifacts, and independent review. Deliver a playable export, editable source, and evidence of verification. Publication remains a user action.

English documentation is a user preference; exact token savings depend on the model, tokenizer, and text. Video language is specified separately in each brief.

## Operating approach

Recommended: one coordinator delegates bounded tasks to specialists sharing a project folder. Run independent research and preparation concurrently; sequence dependent work. A single assistant switching roles is a cheaper alternative but offers less independent review. Separate manually managed chats offer direct user access to each role but require more handoff work.

AGENTS.md will contain shared operating rules, not create or launch agents. Separate role instructions will define responsibilities. A runtime capable of delegation and media tools is required. This document does not establish that such a runtime is configured.

## Roles and deliverables

| Role | Responsibility | Required handoff |
| --- | --- | --- |
| Coordinator | Own brief, dependencies, versioning, routing and acceptance | Brief, task board, artifact manifest, release summary |
| Designer | Find references, explain relevant techniques, define typography, color, composition and motion | Reference URLs with observations, style guide, scene treatments |
| Scriptwriter | One central idea, hook, explanation, evidence, payoff and relevant CTA | Narration, on-screen copy, scene IDs and factual sources |
| Editor | Implement scenes in code, transitions, captions and export | Editable source, scene timeline, rendered candidate |
| Sound director | Select an available voice, direct delivery, place music and SFX, mix | Actual voice audio, word/phrase timing, cue sheet, stems and mix |
| Reviewer | Independently inspect the exact rendered candidate | Criterion results, timestamped defects, evidence and verdict |

The reviewer does not silently fix the candidate or weaken criteria. The coordinator cannot override a failed gate or describe an unverified candidate as accepted.

## Production sequence

1. Coordinator records audience, central idea, intended action, duration budget, media language, resources and constraints.
2. Designer and scriptwriter develop compatible treatments; source research may run concurrently.
3. Coordinator freezes the script, scene plan and acceptance profile before production.
4. Sound director produces actual narration and timing. Editor may build visual components beforehand but locks scene timing against real narration.
5. Editor and sound director exchange timeline and cue revisions using stable scene IDs.
6. Render an immutable candidate with a unique version and file checksum.
7. Reviewer runs technical checks and watches/listens to the entire export, including transitions, at normal speed. Inspect suspect frames and listen to isolated audio where needed.
8. Coordinator routes each defect to its owner. After changes, create a new candidate and repeat review of the whole export plus focused regression checks.
9. Accepted delivery includes video, source, supporting assets and review report. User reviews and publishes.

Allow at most three automatic repair rounds after initial review. If unresolved, mark NEEDS_USER_DECISION and report remaining defects and alternatives. Never relax thresholds automatically.

## Acceptance rules

All numeric thresholds below are initial internal production policies, not Instagram requirements or scientifically established retention laws. They are deliberately explicit so agents can apply them consistently. Freeze them per Reel before rendering. Change future defaults using observed results and user decisions, not to make a failed candidate pass.

Time is evaluated using integer frame timestamps; duration limits are rounded conservatively to the available frame grid. Values exactly at a limit pass; values beyond it fail. Audio measurements state tool, method and precision. No criterion may be marked PASS without evidence. Unavailable checks are UNVERIFIED and block acceptance.

### Picture and technical integrity

| ID | Gate | Evidence |
| --- | --- | --- |
| V01 | Default export 1080 × 1920, progressive, constant 30 fps; alternate profile must be frozen in the brief | Probe of delivered file |
| V02 | Entire file decodes; required assets load; no unintended black, blank, frozen, missing or corrupt frames | Decode check, anomaly scan and full playback |
| V03 | No unintended overlaps, clipping, truncated glyphs, placeholder content, watermarks or layout jumps | Full playback and frame inspection |
| V04 | Critical copy stays within x=90…900 and y=240…1500 at 1080 × 1920; this is a conservative house safe region, not an official platform guarantee | Frame/layout inspection; phone UI preview still required |
| V05 | Default essential text size at least 48 px; captions at least 52 px; smaller text requires redesign or a pre-approved brief profile | Source inspection plus rendered phone-size view |
| V06 | No unintended repeated flashes; prohibit sequences with three or more substantial flashes in any one-second window | Timeline inspection and playback; this is not a medical safety certification |

### Pacing and attention proxies

A meaningful visual event changes the information or directs attention to the current explanation: reveal a relevant object, highlight a specific detail, demonstrate an action, update a diagram or change the shot. Decorative drift, a looping background, tiny zooms and routine caption-word changes do not reset the meaningful-event clock.

| ID | Gate | Evidence |
| --- | --- | --- |
| P01 | First meaningful visual appears by 0.5 s; concrete subject or promise is understandable by 2.0 s | First two seconds and script review |
| P02 | During explanatory narration, gap between meaningful visual events is at most 3.0 s | Actual rendered event log, including scene boundaries |
| P03 | Reading/demo holds may extend to 6.0 s only when declared before production, with a specific reading or observation task; longer holds require a different pre-approved profile | Scene plan plus rendered segment |
| P04 | No essential visual is available for less than 0.8 s; a reading requirement can require longer | Timeline and frame review |
| P05 | One primary visual focus at a time; no simultaneous new diagram, unrelated headline and new reading task | Reviewer identifies the intended focal point for every scene |
| P06 | Each narration claim has a matching visual or explicitly designated speaker/text treatment; decorative footage cannot serve as evidence | Claim-to-scene map |
| P07 | Payoff answers the opening promise; no irrelevant ending or unexplained abrupt cutoff | Full script and export review |

Do not manufacture cuts to satisfy P02. If pacing and comprehension conflict, simplify the script or redesign the visual explanation. An approved P03 hold is evaluated under its declared limit rather than simultaneously failing P02.

These tests detect risks to attention; they do not measure gaze, comprehension or actual retention. No predicted retention percentage may be reported as a measured result.

### Captions and reading

| ID | Gate | Evidence |
| --- | --- | --- |
| C01 | Caption wording matches approved narration, including names, numbers and negation; punctuation may differ without changing meaning | Transcript comparison and listening |
| C02 | Phrase captions: at most two lines, 32 characters per line, and 17 visible characters per second including spaces; display at least 1.0 s | Caption timing report |
| C03 | Phrase caption onset within ±100 ms of phrase onset; offset from final spoken word between −100 ms and +300 ms; no overlap into an unrelated phrase | Actual audio alignment plus spot checks |
| C04 | Essential non-caption copy receives at least max(1.0 s, word count / 3) fully readable time; entrance/exit animation does not count | Rendered visibility intervals |
| C05 | Small-preview reading check at 360 × 640, without zoom, passes; text/background contrast target at least 4.5:1 across the moving background | Preview and contrast inspection |

Default format is phrase captions. Word-highlight animation may sit inside a persistent phrase; isolated rapidly replaced word captions require a separately approved profile. If caption speed fails, rewrite/re-record or extend timing rather than dropping important words.

### Audio and synchronization

| ID | Gate | Evidence |
| --- | --- | --- |
| A01 | Delivery target −16 LUFS integrated, accepted range −17 to −15 LUFS; true peak at most −1 dBTP | Measure the final encoded export; these are house targets |
| A02 | No audible distortion, pops, truncated syllables, accidental silence, clicks or harsh edit boundaries | Full listening pass, headphones and phone speaker |
| A03 | Voice is intelligible throughout on a phone speaker; music and SFX never mask a word | Actual phone check or explicit UNVERIFIED status |
| A04 | Intended synchronized SFX/visual onsets differ by at most two frames; voice-linked demonstration beats by at most three frames | Cue sheet compared with export |
| A05 | During narration, continuous background bed is initially mixed at least 12 dB below voice RMS over the same speech-active windows; this measurement does not replace A03 | Stem measurements and listening |
| A06 | Voice pronunciation, emotional delivery and pauses fit approved copy; no unapproved voice substitution | Voice asset manifest and listening |

No lip-sync claim is applicable unless a speaking face exists; then define and freeze a specific lip-sync profile before production. Beat synchronization is required only for designated cues; reading and semantic timing take priority over a global musical grid.

## Reviewer protocol and defect record

Verdicts: PASS, FAIL, UNVERIFIED, or NOT_APPLICABLE with reason. Overall acceptance requires every applicable gate to PASS. Editorial gates are still mandatory but require an explicit written judgment, not fabricated measurements.

Each defect records candidate checksum, criterion ID, scene ID, start/end timestamp, expected limit, observed result, evidence, responsible role and requested correction. Example: P02; scene S04; 00:12.400–00:16.800; event gap 4.400 s > 3.000 s; editor must reveal the relevant example during the explanation. Mere addition of decorative motion does not resolve it.

Inspect every scene boundary frame by frame where appropriate. Always watch the full final export with sound. Source-code inspection, contact sheets and successful rendering alone cannot substitute for playback. If the environment cannot inspect audio/video adequately, report that limitation and block acceptance.

## Shared artifacts planned for implementation

- AGENTS.md: common rules, workflow and authority boundaries.
- roles/: English instructions for coordinator, designer, scriptwriter, editor, sound director and reviewer.
- quality/criteria.md: frozen criteria with version history.
- reels/<reel-id>/: brief, references, script, scene plan, source, assets, narration, cue sheet and renders.
- reels/<reel-id>/reviews/: candidate manifest, measurements, timestamped issues and acceptance report.

Tasks use explicit inputs, output paths, dependencies and completion conditions. Agents own separate files; coordinator resolves shared timeline changes. Handoffs include unresolved assumptions. Research links must be real and inspected; generated demo footage must be identified as such.

## Permissions and resources

Use available tools and licensed/user-supplied assets. Record provenance. Paid voice or asset generation requires an existing user-authorized budget. Do not create accounts, purchase services, clone a voice or publish without appropriate explicit authorization. Missing tools or credentials are reported, not simulated as successful media work.

## Improvement after publication

User-supplied analytics may inform subsequent versions. Compare available retention, watch time, saves and shares at equal post age; missing values remain missing. Choose one or two changes per iteration. Never infer a universal timing rule from a single Reel.

## Sources and interpretation

- BBC Research white paper WHP306: https://downloads.bbc.co.uk/rd/pubs/whp/whp-pdf-files/WHP306.pdf — research context on subtitle reading and presentation; not a source for an Instagram retention guarantee or our exact house thresholds. The historical BBC subtitle-guidelines URL returned 404 during research and is not relied on.
- Remotion audio transitions: https://www.remotion.dev/docs/transitions/audio-transitions — implementation reference for audio around transitions, not a loudness standard.

All exact limits in this draft are chosen production defaults. They require calibration on actual sample exports before being treated as a proven workflow.
