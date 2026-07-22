import streamlit as st
from pathlib import Path
import tempfile
import uuid
from datetime import date

from src.stt.transcribe import transcribe
from src.extraction.extract import extract
from src.dialogue.clarify import get_next_question, apply_answer
from src.generation.generate import generate

st.set_page_config(page_title="Voice-Based Form Filler", page_icon="🎙️")
st.title("🎙️ Voice-Based Form Filler")
st.caption("Speak naturally in English/Urdu — get a formal document.")

if "recorder_key" not in st.session_state:
    st.session_state.recorder_key = 0
if "form" not in st.session_state:
    st.session_state.form = None
if "transcript" not in st.session_state:
    st.session_state.transcript = None
if "needs_type_selection" not in st.session_state:
    st.session_state.needs_type_selection = False
if "no_intent" not in st.session_state:
    st.session_state.no_intent = False

DOC_TYPE_LABELS = {
    "leave_application_office": "Office leave application",
    "leave_application_university": "University/school leave application",
    "complaint_letter": "Complaint letter",
}

st.subheader("1. Provide your voice note")
tab_record, tab_upload = st.tabs(["🎙️ Record", "📁 Upload"])

audio_path = None

with tab_record:
    current_key = f"recorder_{st.session_state.recorder_key}"
    recorded = st.audio_input("Record your request", key=current_key)
    if recorded:
        tmp = Path(tempfile.gettempdir()) / f"recorded_{uuid.uuid4().hex}.wav"
        tmp.write_bytes(recorded.getvalue())
        audio_path = tmp

    if st.button("🔄 Record again"):
        old_key = f"recorder_{st.session_state.recorder_key}"
        if old_key in st.session_state:
            del st.session_state[old_key]
        st.session_state.recorder_key += 1
        st.session_state.form = None
        st.session_state.transcript = None
        st.session_state.needs_type_selection = False
        st.session_state.no_intent = False
        st.rerun()

with tab_upload:
    uploaded = st.file_uploader("Upload a voice recording", type=["wav", "mp3", "m4a", "mp4", "webm", "ogg"])
    if uploaded:
        tmp = Path(tempfile.gettempdir()) / f"upload_{uuid.uuid4().hex}_{uploaded.name}"
        tmp.write_bytes(uploaded.getvalue())
        audio_path = tmp

if (audio_path and st.session_state.form is None
        and not st.session_state.needs_type_selection and not st.session_state.no_intent):
    st.audio(str(audio_path))

    st.subheader("2. Transcript")
    with st.spinner("Transcribing..."):
        transcript = transcribe(audio_path)
    st.write(transcript)
    st.session_state.transcript = transcript

    st.subheader("3. Extracted fields")
    with st.spinner("Classifying and extracting..."):
        try:
            form = extract(transcript, today=date.today().isoformat())
            st.session_state.form = form
        except ValueError as e:
            msg = str(e)
            if msg.startswith("NO_DOCUMENT_INTENT"):
                st.session_state.no_intent = True
            elif msg.startswith("UNKNOWN_DOCUMENT_TYPE"):
                st.session_state.needs_type_selection = True
            else:
                st.error(msg)
            st.session_state.form = None

if st.session_state.no_intent:
    st.error(
        "I couldn't find a request for any document in that recording. "
        "Try describing what you need — e.g. 'I need 3 days leave...' or "
        "'I want to file a complaint about...'"
    )

if st.session_state.needs_type_selection:
    st.warning("I couldn't tell what kind of document you need. Please choose one:")
    choice_label = st.selectbox("Document type", list(DOC_TYPE_LABELS.values()))
    if st.button("Continue with this type"):
        chosen_type = [k for k, v in DOC_TYPE_LABELS.items() if v == choice_label][0]
        with st.spinner("Extracting with selected document type..."):
            try:
                form = extract(st.session_state.transcript, today=date.today().isoformat(),
                                forced_doc_type=chosen_type)
                st.session_state.form = form
                st.session_state.needs_type_selection = False
                st.rerun()
            except ValueError as e:
                st.error(str(e))

if st.session_state.form is not None:
    form = st.session_state.form
    st.json(form.model_dump())

    st.subheader("4. Fill in missing details")
    next_q = get_next_question(form)

    if next_q:
        field, question = next_q
        with st.form(key=f"clarify_{field}"):
            answer = st.text_input(question)
            submitted = st.form_submit_button("Submit")
            if submitted and answer.strip():
                apply_answer(form, field, answer)
                st.session_state.form = form
                st.rerun()
    else:
        st.success("All required fields present — ready to generate.")
        st.subheader("5. Document")
        if st.button("Generate document"):
            out_path = Path(tempfile.gettempdir()) / f"document_{uuid.uuid4().hex}.docx"
            try:
                generate(form, out_path)
                with open(out_path, "rb") as f:
                    st.download_button(
                        "Download .docx",
                        data=f.read(),
                        file_name="document.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
            except ValueError as e:
                st.error(str(e))
elif not audio_path:
    st.info("Record or upload a voice note to get started.")