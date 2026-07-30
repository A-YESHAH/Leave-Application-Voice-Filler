import streamlit as st
from pathlib import Path
import tempfile
import uuid
from datetime import date

from src.stt.transcribe import transcribe
from src.extraction.extract import extract
from src.dialogue.clarify import get_next_question, apply_answer, needs_confirmation, apply_confirmation
from src.dialogue.edit_command import apply_edit_command
from src.generation.generate import generate
from src.generation.preview import render_preview
from src.generation.pdf_export import docx_to_pdf

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
if "generic_error" not in st.session_state:
    st.session_state.generic_error = None
if "confirmed_fields" not in st.session_state:
    st.session_state.confirmed_fields = set()

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
        st.session_state.generic_error = None
        st.session_state.confirmed_fields = set()
        st.rerun()

with tab_upload:
    uploaded = st.file_uploader("Upload a voice recording", type=["wav", "mp3", "m4a", "mp4", "webm", "ogg"])
    if uploaded:
        tmp = Path(tempfile.gettempdir()) / f"upload_{uuid.uuid4().hex}_{uploaded.name}"
        tmp.write_bytes(uploaded.getvalue())
        audio_path = tmp

if (audio_path and st.session_state.form is None
        and not st.session_state.needs_type_selection and not st.session_state.no_intent
        and not st.session_state.generic_error):
    st.audio(str(audio_path))

    progress = st.progress(0, text="Starting...")

    progress.progress(20, text="Transcribing audio...")
    transcript = transcribe(audio_path)
    st.session_state.transcript = transcript

    progress.progress(60, text="Classifying and extracting fields...")
    try:
        form = extract(transcript, today=date.today().isoformat())
        st.session_state.form = form
        progress.progress(100, text="Done")
        progress.empty()
    except ValueError as e:
        progress.empty()
        msg = str(e)
        if msg.startswith("NO_DOCUMENT_INTENT"):
            st.session_state.no_intent = True
        elif msg.startswith("UNKNOWN_DOCUMENT_TYPE"):
            st.session_state.needs_type_selection = True
        else:
            st.session_state.generic_error = msg
        st.session_state.form = None

    st.subheader("2. Transcript")
    st.write(transcript)

if st.session_state.no_intent:
    st.error(
        "🎤 I couldn't find a request for any document in that recording.\n\n"
        "Try describing what you need — e.g. *'I need 3 days leave...'* or "
        "*'I want to file a complaint about...'*"
    )
    if st.button("Try again"):
        st.session_state.no_intent = False
        st.session_state.transcript = None
        st.rerun()

if st.session_state.generic_error:
    st.error(f"⚠️ Something went wrong: {st.session_state.generic_error}")
    if st.button("Try again", key="generic_retry"):
        st.session_state.generic_error = None
        st.session_state.transcript = None
        st.rerun()

if st.session_state.needs_type_selection:
    st.warning("🤔 I couldn't tell what kind of document you need. Please choose one:")
    choice_label = st.selectbox("Document type", list(DOC_TYPE_LABELS.values()))
    col1, col2 = st.columns([1, 1])
    with col1:
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
    with col2:
        if st.button("Start over"):
            st.session_state.needs_type_selection = False
            st.session_state.transcript = None
            st.rerun()

if st.session_state.form is not None:
    form = st.session_state.form
    st.json(form.model_dump())

    confirm_needed = needs_confirmation(form, st.session_state.confirmed_fields)

    if confirm_needed:
        field, question = confirm_needed
        st.subheader("4. Please confirm")
        with st.form(key=f"confirm_{field}"):
            st.write(question)
            answer = st.text_input("Your response")
            submitted = st.form_submit_button("Submit")
            if submitted and answer.strip():
                apply_confirmation(form, field, answer, st.session_state.confirmed_fields)
                st.session_state.form = form
                st.rerun()
    else:
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

            st.subheader("5. Preview")
            st.text(render_preview(form))

            with st.form(key="edit_command_form"):
                edit_text = st.text_input("Want to change something? (e.g. 'change the date to Tuesday')")
                edit_submitted = st.form_submit_button("Apply change")
                if edit_submitted and edit_text.strip():
                    with st.spinner("Applying change..."):
                        updated_form, changed = apply_edit_command(
                            form, edit_text, today=date.today().isoformat()
                        )
                        st.session_state.form = updated_form
                        if changed:
                            st.success(f"Updated: {', '.join(changed)}")
                        else:
                            st.warning("Couldn't match that to a field — try being more specific.")
                        st.rerun()

            st.subheader("6. Document")
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
                    try:
                        pdf_path = docx_to_pdf(out_path)
                        with open(pdf_path, "rb") as f:
                            st.download_button(
                                "Download .pdf",
                                data=f.read(),
                                file_name="document.pdf",
                                mime="application/pdf",
                            )
                    except RuntimeError as pdf_err:
                        st.warning(f"PDF export unavailable: {pdf_err}")
                except ValueError as e:
                    st.error(str(e))
elif not audio_path:
    st.info("Record or upload a voice note to get started.")