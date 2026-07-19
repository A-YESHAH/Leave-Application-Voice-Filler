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
