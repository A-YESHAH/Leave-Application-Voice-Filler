import json
import ollama

CLASSIFY_MODEL = "llama3.2"

NO_REQUEST_MARKERS = [
    "mera naam", "meri naam", "میرا نام", "میرے نام",
    "my name is", "i am making this", "test recording",
    "aaj tareekh", "tareekh hai", "آج تاریخ",
]

REQUEST_MARKERS = [
    "chahiye", "chutti", "chuti", "leave", "application likhni",
    "complaint likhni", "i need", "i want", "please grant",
    "لکھ دو", "لکھنی", "لکھ دیں", "لکھنا", "likh do", "likhwa",
    "likhni hai", "likhna hai", "application", "ایپلکیشن", "ایپلیکیشن",
    "چھٹی", "چاہیے", "درخواست",
    "complain", "complaint", "کمپلینٹ", "کمپلین", "شکایت",
]

UNIVERSITY_MARKERS = [
    "semester", "سمسٹر", "class", "کلاس", "roll number", "رول نمبر",
    "student", "طالب علم", "بی ایس سی ایس", "بی ای سی ایس",
    "university", "یونیورسٹی", "یونیویسٹی", "head of department",
    "ہیڈ اف ڈپارٹمنٹ", "professor", "پروفیسر",
]

WORKPLACE_MARKERS = [
    "manager", "منیجر", "مینجر", "company", "کمپنی", "employee",
    "ایمپلائی", "designation", "ڈیزگنیشن", "office", "آفس",
]

COMPLAINT_MARKERS = ["complain", "complaint", "کمپلینٹ", "کمپلین", "شکایت"]

CLASSIFIER_PROMPT = """You classify voice transcripts into a document type for a formal-letter
generation system used in Pakistan. Transcripts may be in English, Roman Urdu, or Urdu script,
and may mix languages/scripts within one sentence.

Return ONLY a JSON object: {{"document_type": "<one of the types below>"}}

Types:
- leave_application_office
- leave_application_university
- complaint_letter
- unknown (a leave/complaint request IS present, but which specific type is unclear)
- no_intent (there is NO request for any document at all — greetings, self-introductions,
  date statements, test recordings, unrelated speech)

Rules:
- Base your decision on document intent (what kind of letter is needed), not exact wording
  or script. The SAME rules apply whether the transcript is in English, Roman Urdu, or Urdu
  script (اردو رسم الخط) — do not let the script change your classification logic.
- A transcript merely mentioning a date, a number, or a name is NOT automatically a leave
  request or complaint. There must be a clear intent to request leave, file a complaint, etc.
  If there is no such intent at all, return "no_intent".
- MANDATORY CHECK before choosing any document type: does the transcript contain an explicit
  VERB OF REQUEST — words/phrases like "chahiye"/"چاہیے" (want/need), "chutti"/"چھٹی" (leave)
  combined with a request, "application likhni hai"/"ایپلیکیشن لکھنی ہے" (need to write an
  application), "complaint likhni hai"/"کمپلینٹ لکھنی ہے" (need to file a complaint),
  "I need", "I want", "please grant"? If NO such request verb or phrase is present anywhere
  in the transcript, in ANY script, you MUST return "no_intent". Stating a name or a date is
  NOT a request verb.
- Mentions of "class"/"کلاس", "semester"/"سمسٹر", "roll number"/"رول نمبر", "student"/"طالب علم",
  or a subject/professor context strongly indicate leave_application_university, NOT
  leave_application_office — even if "chutti"/"چھٹی" or "leave" appears, check WHO the request
  is addressed to (a teacher/school vs a workplace manager) before choosing office.
- If a bare leave request exists but has NO workplace context (manager, company, employee ID,
  designation) AND NO school context (class, semester, roll number, student), return "unknown".

Worked examples (each shown in both Roman Urdu and Urdu script — apply the SAME logic to both):

Transcript: "Sir ko application likhni hai, kal main class attend nahi kar sakta, bukhar hai. Main BSCS 7th semester ka student hoon, roll number 21-CS-045."
-> {{"document_type": "leave_application_university"}}

Transcript: "سر کو اپلیکیشن لکھنی ہے، کل میں کلاس اٹینڈ نہیں کر سکتا، بخار ہے۔ میں بی ایس سی ایس سیونتھ سمسٹر کا طالب علم ہوں، رول نمبر 21-CS-045۔"
-> {{"document_type": "leave_application_university"}}
(Same content as above, in Urdu script — student/class/semester/roll number -> university.)

Transcript: "Mujhe Monday se teen din ki chutti chahiye, meri sister ki shaadi hai. Manager ka naam Ahmed Khan hai."
-> {{"document_type": "leave_application_office"}}

Transcript: "مجھے پیر سے تین دن کی چھٹی چاہیے، میری بہن کی شادی ہے۔ منیجر کا نام احمد خان ہے۔"
-> {{"document_type": "leave_application_office"}}
(Same content as above, in Urdu script — manager/workplace context -> office.)

Transcript: "K-Electric ko complaint likhni hai, hamare area mein loadshedding ho rahi hai."
-> {{"document_type": "complaint_letter"}}

Transcript: "کے الیکٹرک کو کمپلینٹ لکھنی ہے، ہمارے علاقے میں لوڈشیڈنگ ہو رہی ہے۔"
-> {{"document_type": "complaint_letter"}}
(Same content as above, in Urdu script — complaint about a utility provider.)

Transcript: "Hello, today is 15th of June, Wednesday."
-> {{"document_type": "no_intent"}}

Transcript: "ہیلو، آج 15 جون بدھ ہے۔"
-> {{"document_type": "no_intent"}}
(Just a date statement in Urdu script — no request verb present.)

Transcript: "Good morning, I am Ayesha Niazi and I am making this project to test."
-> {{"document_type": "no_intent"}}

Transcript: "صبح بخیر، میرا نام عائشہ نیازی ہے اور میں یہ پروجیکٹ ٹیسٹ کر رہی ہوں۔"
-> {{"document_type": "no_intent"}}
(Same self-introduction pattern in Urdu script — no request verb present.)

Transcript: "muje parson se do din ki chuti chahye i am not well."
-> {{"document_type": "unknown"}}

Transcript: "مجھے پرسوں سے دو دن کی چھٹی چاہیے، میری طبیعت ٹھیک نہیں ہے۔"
-> {{"document_type": "unknown"}}
(Same bare leave request in Urdu script, no workplace or school context — type unclear.)

TODAY'S DATE is not needed for classification — focus only on WHAT KIND of document is being
requested, if any, regardless of script.

Transcript: {transcript}
"""


def classify(transcript: str, model: str = CLASSIFY_MODEL) -> str:
    text_lower = transcript.lower()
    word_count = len(transcript.split())

    has_request_marker = any(m in text_lower for m in REQUEST_MARKERS)
    has_no_request_marker = any(m in text_lower for m in NO_REQUEST_MARKERS)

    if not has_request_marker:
        return "no_intent"

    if has_no_request_marker and not has_request_marker:
        return "no_intent"

    has_university_marker = any(m in text_lower for m in UNIVERSITY_MARKERS)
    has_workplace_marker = any(m in text_lower for m in WORKPLACE_MARKERS)
    has_complaint_marker = any(m in text_lower for m in COMPLAINT_MARKERS)

    if has_university_marker and not has_workplace_marker:
        return "leave_application_university"

    if has_complaint_marker:
        return "complaint_letter"

    if (word_count <= 12 and not has_university_marker
            and not has_workplace_marker and not has_complaint_marker):
        return "unknown"

    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": CLASSIFIER_PROMPT.format(transcript=transcript)}],
        format="json",
        options={"temperature": 0},
    )
    raw = response["message"]["content"]
    try:
        data = json.loads(raw)
        doc_type = data.get("document_type", "no_intent")
    except json.JSONDecodeError:
        doc_type = "no_intent"

    valid_types = {"leave_application_office", "leave_application_university",
                   "complaint_letter", "unknown", "no_intent"}
    return doc_type if doc_type in valid_types else "no_intent"


if __name__ == "__main__":
    import sys
    text = sys.argv[1] if len(sys.argv) > 1 else "Mujhe 3 din ki chutti chahiye"
    print(classify(text))