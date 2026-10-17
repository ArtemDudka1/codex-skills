# Acceptance profile v0.1


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

