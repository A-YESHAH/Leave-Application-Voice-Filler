## Day 1-2 — Environment Setup & Speech-to-Text

**Setup**: venv created, repo initialized, dependencies installed
(faster-whisper, pydantic, streamlit, python-docx). Built transcribe(audio) -> text
using faster-whisper locally (device=cpu, compute_type=int8)

**Issue encountered**: "small" model transcribed dates and general
speech correctly, but got the applicant's name wrong. Switched to
"medium" for better name/entity accuracy. Medium initially crashed with
mkl_malloc: failed to allocate memory (insufficient RAM on CPU-only
machine) — resolved by closing other memory-heavy applications before
running.

**Result**: transcribed 5 English test recordings successfully with
"medium". Transcripts preserved key facts (dates, names, reasons)
accurately, including the applicant's name that "small" had missed.

**Decision**: use "medium" as the working model size for Week 1-2
despite higher RAM cost, since name accuracy matters for the
applicant_name field. Revisit the full accuracy/cost/latency tradeoff
properly in Week 3 (R1) across small/medium/large-v3 on the real
code-switched corpus. Keep transcribe(audio) -> text behind a swappable
interface so this decision can change later without touching downstream
code.

## Day 3-4 — Extraction testing findings

- Typed text: 4/4 correct, missing_fields logic working correctly.
- Audio: 2/3 correct. Two failures:
  1. Model hallucinated a start_date on a transcript with no leave
     content at all — prompt's "don't guess" rule wasn't sufficient.
     Fixed by adding explicit "no leave request -> all fields null" rule.
  2. Whisper mis-detected Urdu speech as Hindi (language=hi), transcribed
     in Devanagari script instead of Roman/mixed text. This then caused
     the extraction LLM to mistranslate "designation" as "back pain" —
     garbled script confusing the LLM layer. Early signal for R1: Urdu
     needs language pinning or model upgrade, not just prompt fixes.

## Day 6-7 — Streamlit App, v0.1

Wired transcribe() -> extract() -> generate() into a Streamlit app.
Record (st.audio_input, re-recordable via session_state key rotation)
or upload tabs -> transcript display -> extracted JSON display ->
download button, shown only when form.is_complete(). Missing-field
case shows a plain-text warning; interactive clarification loop is
Week 2 scope.

**Result**: [fill in — did the full pipeline produce a correct .docx
end to end? any issues with the recorder, transcription, or generated
document formatting?]

**Status**: v0.1 tagged — first true end-to-end demo working.

## Week 2, Day 1-2 — Multi-type classification + extraction

**Setup**: added LeaveApplicationUniversityForm and ComplaintLetterForm
schemas, a classify() step (Ollama, JSON mode) that routes transcripts
to one of 3 types or "unknown", and per-type extraction prompts
(EXTRACTION_PROMPTS dict) replacing the single-form prompt from Week 1.

**Result — typed text**: 3/4 classifier accuracy. Office, university,
and complaint cases all classified and extracted correctly on first
try (university correctly resolved "kal" -> tomorrow; complaint
correctly derived complaint_subject as a formal phrase). The negative
case ("Hello, today is 15th of June") was misclassified as office_leave
instead of unknown — classifier prompt currently has no negative
few-shot example, only a prose description of "unknown". Same
hallucination pattern as the Day 3-4 extraction bug, now surfacing at
the classification stage instead.

**Result — real audio**: Reason-field contamination regressed on
clip 3 (Urdu) — designation info leaked into the reason field again.
Root cause: refactoring prompts.py into per-type prompts dropped the
negative few-shot example that fixed this in Day 3-4; only 2 of the
original 7 examples were carried over to OFFICE_LEAVE_EXAMPLES.
Also recurring: applicant_designation and duration_days stayed null
despite being clearly spoken ("AI Intern", "teen din") — same Urdu
numeral/multi-fact extraction unreliability as before.

**Decision**: add a negative few-shot example to the classifier
prompt (mirroring the fix that worked for the extractor). Restore the
dropped negative examples to OFFICE_LEAVE_EXAMPLES rather than assuming
2 examples are sufficient — prompt refactors need regression checks
against previously-fixed bugs, not just new-feature tests. Flag
Urdu-numeral + multi-fact extraction reliability as a standing R3/R6
open issue, to be addressed properly during the dedicated normalization
pass later in Week 2.

Adding worked contrastive examples (university vs office, explicit
disambiguation rule on student/class/semester/roll-number signals)
fixed the classifier regression: 4/4 typed accuracy, 5/5 consistent
on the previously-flip-flopping university case, no regressions on
office/complaint/unknown categories.

**New finding (R2)**: clip 3's reason field consistently extracts as
"sister's illness" across multiple runs/prompt versions, when the
Urdu transcript clearly says "میری امی بیمار ہیں" (mother, not
sister, is sick — امی = mother). This persisted through the
classifier fix, confirming it's an extraction-stage translation
error, not a classification issue. Root cause is likely the model's
Urdu kinship-term vocabulary being weaker for less-common-in-English-
training-data words like "ami" vs more familiar ones. This is a
genuine model-limitation finding, not something to chase with more
prompt patches — worth reporting directly in the R2 evaluation
writeup as a specific failure category (Urdu kinship/relationship
term translation accuracy) rather than treating as a bug to eliminate.

All green — 7/7, 7/7, 5/5 on the normalization tests, and the bug is confirmed fixed: the university case now correctly holds duration_days: 1 (no bogus overwrite from the roll number), classifier stays 4/4, and everything else remains stable/correct.
NOTES.md — final confirmation entry for Day 5:
markdown## Week 2, Day 5 — Normalization fix confirmed

Regex fix (require digit to be adjacent to a duration-unit word)
resolved the roll-number/duration collision bug. Re-ran full test
suite: normalize.py 7/7 number cases, 7/7 date cases, 5/5 cross-check
cases (including the specific roll-number regression case). Full
pipeline re-test on university case confirms duration_days correctly
stays at 1 (previously corrupted to 21 by the roll number "21-CS-045").
No regressions elsewhere — classifier still 4/4, office/complaint
extraction unaffected.

Added Urdu kinship-term glossary (ami/abbu/behen/bhai/etc.) to all
three extraction prompts. Retested clip 3: reason now correctly
extracts as "mother's illness" (previously "sister's illness") —
امی correctly translated. Full regression suite still clean: 4/4
classifier accuracy, all other fields across office/university/
complaint types unaffected.

Day 5 complete: date/number normalization layer built and validated
(R3), wired into extract.py as a deterministic safety net over LLM
extraction for duration_days.

## Week 2, Day 6-7 — Retry mechanism verified (confirmed working)

Ran test_retry_mechanism.py with a mocked first-call failure (invalid
JSON) followed by a valid response. Result: exactly 2 calls made (1
failure + 1 successful retry), form recovered correctly and complete.
Confirms the retry-on-invalid-output loop (R6) genuinely recovers from
real failures, not just passing because it was never triggered.

Week 2 fully closed out: multi-type classification (Day 1-2),
clarification loop (Day 3-4), date/number normalization (Day 5),
retry-on-invalid-output + graceful error handling (Day 6-7), all
tested and confirmed. Tagged v0.2.
