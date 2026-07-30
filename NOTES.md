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

## Week 3 — R1: Whisper model size comparison (small vs medium)

Ran both models against all 18 corpus clips, manually scored transcript
quality against expected_gist (facts-preserved judgment, not WER).

**Results**: medium = 18/18 clean transcriptions. small = 10/18 clean,
6/18 usable-but-garbled, 2/18 failed outright (clip_002 lost a spoken
number entirely; clip_018 hallucinated unrelated English fragments and
lost nearly all real content — a genuine breakdown, not just noise).

On English-only input, small and medium performed IDENTICALLY (7/7
clips perfect on both) — small's accuracy gap only appears on Urdu/
code-switched input.

Latency: small averages ~19.8s on English vs medium's ~70.2s (small
~3.5x faster with no quality cost on English). On Urdu, small is
bimodal — mostly fast but with 3 extreme outliers (300-400s) on the
three longest/most complex clips, exactly where it also failed most
badly on accuracy. Medium's Urdu latency stayed consistent (90-207s)
regardless of clip complexity.

**Decision**: ship medium as the default model. The project's core
differentiator is Urdu/code-switching support, and small's failure
mode there (clip_018's near-total hallucination) is a serious
reliability risk for a system generating official documents — an
undetected hallucinated transcript could produce a wrong or nonsensical
formal letter. Small's speed advantage is real but only pays off on
English input, which isn't the harder case this project needs to solve.
This empirically confirms the earlier Day 1-2 decision (switching from
small to medium for name accuracy) at much larger sample size.

**Caveat**: the 3 extreme latency outliers for small (clips 001, 008, 018) need one more confirmation run to rule out a one-off system/
resource issue rather than a genuine model-size effect — worth
re-running just those 3 clips again before citing the latency numbers
definitively in the final report.

Ran extract() against all 18 corpus clips using both small and medium
Whisper transcripts, scored against ground-truth labels.

**Results**: type accuracy small=56% (10/18), medium=67% (12/18).
Field accuracy (on correctly-typed clips only) small=~52%, medium=~63%.
Both far below the ≥95%/≥90% targets — expected at this stage, this
is the real baseline R2 is meant to establish.

**Top failure patterns identified**:

1. Classifier fails identically on 6/18 clips regardless of Whisper
   model size — confirms this is a classification issue, not an STT
   issue. Clip 009 in particular is near-identical in content to the
   existing "university" few-shot example, but fails because the
   example is written in Roman Urdu while real transcribed speech is
   in Urdu script — the script-generalization ceiling documented in
   Week 2, now confirmed at scale.
2. start_date safety net (cross_check_start_date) only checks
   validity, not whether the resolved date is in the future — multiple
   clips got dates in the past relative to the recording date.
3. Model confuses day-of-month mentions ("30 tareekh") with duration
   counts on at least one clip. Also discovered normalize.py's number/
   date word lists are Roman-transliteration only and cannot recognize
   Urdu-script number/day words, making the safety net blind on genuine
   Urdu-script transcripts (the majority of real Urdu STT output).
4. Under heavy transcription noise, the model appears to default to
   entity values from its OWN few-shot examples (e.g. extracted
   "K-Electric" on a Nayatel complaint) rather than returning null —
   a memorization-bias risk distinct from simple omission.
5. Minor name/company spelling noise from STT, lower severity.

## Week 3, Day 5 — R4 clarification policy: confirmed working

Tested the confirm-vs-ask-vs-assume policy on 3 cases:

- Illness-stated -> correctly infers "sick", triggers confirmation
  with correct reasoning shown to user.
- Wedding-stated -> correctly infers "casual", triggers confirmation.
- No reason stated at all -> leave_type stays null, correctly skips
  confirmation (falls through to the normal required-field question
  instead, since there's nothing inferred to confirm).

This directly implements the companion doc's "chutti chahiye is
ambiguous, always confirm" guidance as a genuine policy layer,
distinct from the existing missing-required-field loop. Day 5 (R4)
complete.

## Week 3, Day 6-7 — Final evaluation, v0.3

Final full-corpus run: type accuracy 94% (small) / 100% (medium) —
meets/exceeds the >=95% target on medium. Field accuracy 72% (small)
/ 84% (medium) — approaching but not yet at the >=90% target.

Improvement trajectory across Week 3 (type / field accuracy):

- Baseline: 56%/67% type, ~52%/63% field
- After deterministic classifier pre-filters (university/complaint/
  unknown): 89%/94% type
- After marker-list refinement: 94%/100% type
- After day-of-month resolution, anti-copying rule, vague-reason
  capture, phone-number normalization: 72%/84% field (final)

Top 3 remaining failure patterns (addressed where possible, documented
where not):

1. Occasional field omission on fields stated close together in one
   sentence (department, recipient_designation) — added an explicit
   "scan for ALL fields" prompt rule; partial mitigation, likely a
   residual small-model completeness limitation.
2. Phone/reference number formatting noise — fixed via
   format_phone_number() normalization + digit-only scorer comparison.
   Confirmed working (clip_014's number correctly reformatted).
3. Name/entity phonetic noise (Hassan/Hasan, Bilal/Balal, Fatima
   variants) — determined to be an STT-layer limitation, documented
   as a known limitation tied to R1 findings rather than patched.

New minor finding: semester field occasionally returned as int
instead of str, causing one schema-validation retry (successfully
recovered by the existing retry loop) — added a field_validator to
coerce this automatically going forward.

Week 3 core evaluation phase complete: R1 (Whisper size comparison),
R2 (extraction robustness — iteratively improved through documented,
evidence-driven fixes), R4 (clarification/confirmation policy). This
represents the project's strongest R&D material: a full before/after
accuracy trajectory with root-caused, fixed failure patterns.
