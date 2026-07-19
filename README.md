# Voice-Based Form Filler

Speak naturally in English/Urdu — get a formal leave application document.

## Setup

### 1. Clone and create a virtual environment

```bash
git clone <your-repo-url>
cd voice-form-filler
python -m venv venv
```

Activate it:

```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up Ollama (for extraction)

This project uses a local LLM via [Ollama](https://ollama.com/download) for field extraction — no API key needed.

```bash
ollama pull llama3.2
```

Make sure the Ollama app/service is running in the background before starting the app.

### 4. Speech-to-text

Uses `faster-whisper` locally (no API key needed). The model downloads automatically on first run (~medium model, a few hundred MB) — this may take a minute the first time.

## Running the app

```bash
streamlit run app.py
```

This opens the app in your browser at `http://localhost:8501`.

## How to use

1. **Record** your request using the mic tab, or **upload** an audio file (wav/mp3/m4a/mp4/webm/ogg).
2. The app transcribes your speech and shows the transcript.
3. It extracts structured fields (name, dates, reason, etc.) and shows them as JSON.
4. If all required fields are present, a **Download .docx** button appears with your formatted leave application.
5. If fields are missing, they're listed — currently you need to re-record with the missing details included (interactive follow-up questions are a Week 2 feature).

### Example input

> "Mujhe Monday se teen din ki chutti chahiye, meri sister ki shaadi hai. Manager ka naam Ahmed Khan hai. Company ka naam TechSol hai, casual leave chahiye."

## Project structure

See `NOTES.md` for the running development log (setup decisions, bugs found, R&D findings).

## Status

Week 1 — core pipeline (transcribe → extract → generate) working end-to-end via Streamlit. Currently supports one document type: office leave applications.
