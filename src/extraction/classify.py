import json
import ollama

CLASSIFY_MODEL = "llama3.2"

NO_REQUEST_MARKERS = [
    "mera naam", "meri naam", "میرا نام", "میرے نام",
    "my name is", "i am making this", "test recording",
    "aaj tareekh", "tareekh hai",
]

REQUEST_MARKERS = [
    "chahiye", "chutti", "chuti", "leave", "application likhni",
    "complaint likhni", "i need", "i want", "please grant",
    "لکھ دو", "لکھنی", "لکھ دیں", "لکھنا", "likh do", "likhwa",
    "likhni hai", "likhna hai", "application", "ایپلکیشن", "ایپلیکیشن",
    "چھٹی", "چاہیے", "درخواست",
]

CLASSIFIER_PROMPT = """You classify voice transcripts into a document type for a formal-letter
generation system used in Pakistan. Transcripts may mix Urdu and English.

Return ONLY a JSON object: {{"document_type": "<one of the types below>"}}

Types:
- leave_application_office
- leave_application_university
- complaint_letter
- unknown (a leave/complaint request IS present, but which specific type is unclear)
- no_intent (there is NO request for any document at all — greetings, self-introductions,
  date statements, test recordings, unrelated speech)

Rules:
- Base your decision on document intent (what kind of letter is needed), not exact wording.
- A transcript merely mentioning a date, a number, or a name is NOT automatically a leave
  request or complaint. There must be a clear intent to request leave, file a complaint, etc.
- MANDATORY CHECK before choosing any document type: does the transcript contain an explicit
  VERB OF REQUEST — words/phrases like "chahiye" (want/need), "chutti" (leave) combined with
  a request, "application likhni hai" (need to write an application), "complaint likhni hai"
  (need to file a complaint), "I need", "I want", "please grant" — or their Urdu/English
  equivalents? If NO such request verb or phrase is present anywhere in the transcript, you
  MUST return "no_intent", regardless of what other information (names, dates, numbers) is
  present. Stating a name or a date is NOT a request verb.
- Mentions of "class", "semester", "roll number", "student", or a subject/professor context
  strongly indicate leave_application_university, NOT leave_application_office — even if the
  word "chutti" or "leave" appears, check WHO the request is addressed to (a teacher/school
  vs a workplace manager) before choosing office.
- If a bare leave request exists but has NO workplace context (manager, company, employee ID,
  designation) AND NO school context (class, semester, roll number, student), return "unknown".

Worked examples:

Transcript: "Sir ko application likhni hai, kal main class attend nahi kar sakta, bukhar hai. Main BSCS 7th semester ka student hoon, roll number 21-CS-045."
-> {{"document_type": "leave_application_university"}}
(Student, class, semester, roll number -> university, not office.)

Transcript: "Mujhe Monday se teen din ki chutti chahiye, meri sister ki shaadi hai. Manager ka naam Ahmed Khan hai."
-> {{"document_type": "leave_application_office"}}
(Manager, workplace context -> office, not university.)

Transcript: "K-Electric ko complaint likhni hai, hamare area mein loadshedding ho rahi hai."
-> {{"document_type": "complaint_letter"}}
(Complaint about a utility/service provider.)

Transcript: "Hello, today is 15th of June, Wednesday."
-> {{"document_type": "no_intent"}}
(Just a date statement — no request verb present.)

Transcript: "Good morning, I am Ayesha Niazi and I am making this project to test."
-> {{"document_type": "no_intent"}}
(A self-introduction / test recording — no request verb present.)

Transcript: "muje parson se do din ki chuti chahye i am not well."
-> {{"document_type": "unknown"}}
(A bare leave request with no workplace OR school context — request exists, type unclear.)

Transcript: "میرے نام عیشان یاضی ہے مجھے ایک لیف اپلکیکشن لکھ دو"
-> {{"document_type": "unknown"}}
(A bare request to write "a leave application" with zero context — no dates, no reason,
no workplace or school signal. Request exists, type/details totally unclear.)

TODAY'S DATE is not needed for classification — focus only on WHAT KIND of document is being
requested, if any.

Transcript: {transcript}
"""


def classify(transcript: str, model: str = CLASSIFY_MODEL) -> str:
    text_lower = transcript.lower()
    has_request_marker = any(m in text_lower for m in REQUEST_MARKERS)
    has_no_request_marker = any(m in text_lower for m in NO_REQUEST_MARKERS)

    if has_no_request_marker and not has_request_marker:
        return "no_intent"

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