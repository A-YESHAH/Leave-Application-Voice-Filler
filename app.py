import streamlit as st
from pathlib import Path
import tempfile
import uuid
from datetime import date

from src.stt.transcribe import transcribe
from src.extraction.extract import extract
from src.generation.generate import generate

st.set_page_config(page_title="Voice-Based Form Filler", page_icon="🎙️")
st.title("🎙️ Voice-Based Form Filler")
st.caption("Speak naturally in English/Urdu — get a formal leave application.")

if "recorder_key" not in st.session_state:
    st.session_state.recorder_key = 0

st.subheader("1. Provide your voice note")
tab_record, tab_upload = st.tabs(["🎙️ Record", "📁 Upload"])

audio_path = None

with tab_record:
    current_key = f"recorder_{st.session_state.recorder_key}"
    recorded = st.audio_input("Record your request", key=current_key)

    if recorded:
        # unique filename per recording — avoids stale/locked file reuse
        tmp = Path(tempfile.gettempdir()) / f"recorded_{uuid.uuid4().hex}.wav"
        tmp.write_bytes(recorded.getvalue())
        audio_path = tmp

    if st.button("🔄 Record again"):
        # explicitly drop the old widget's value from session_state
        old_key = f"recorder_{st.session_state.recorder_key}"
        if old_key in st.session_state:
            del st.session_state[old_key]
        st.session_state.recorder_key += 1
        st.rerun()

with tab_upload:
    uploaded = st.file_uploader("Upload a voice recording", type=["wav", "mp3", "m4a", "mp4", "webm", "ogg"])
    if uploaded:
        tmp = Path(tempfile.gettempdir()) / f"upload_{uuid.uuid4().hex}_{uploaded.name}"
        tmp.write_bytes(uploaded.getvalue())
        audio_path = tmp

if audio_path:
    st.audio(str(audio_path))

    st.subheader("2. Transcript")
    with st.spinner("Transcribing..."):
        transcript = transcribe(audio_path)
    st.write(transcript)

    st.subheader("3. Extracted fields")
    with st.spinner("Extracting structured data..."):
        form = extract(transcript, today=date.today().isoformat())
    st.json(form.model_dump())

    st.subheader("4. Document")
    if form.is_complete():
        st.success("All required fields present — ready to generate.")
        if st.button("Generate document"):
            out_path = Path(tempfile.gettempdir()) / f"leave_application_{uuid.uuid4().hex}.docx"
            generate(form, out_path)
            with open(out_path, "rb") as f:
                st.download_button(
                    "Download .docx",
                    data=f.read(),
                    file_name="leave_application.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
    else:
        st.warning(
            f"Missing required fields: {', '.join(form.missing_fields)}. "
            "Follow-up questions for these are coming in Week 2 — for now, "
            "try a clip that mentions all of: applicant name, designation, "
            "recipient name, company name, leave type, start date, duration, reason."
        )
else:
    st.info("Record or upload a voice note to get started.")