"""generate(FormJSON) -> .docx file. Fixed structure, LLM writes only the body paragraph."""
from pathlib import Path
from datetime import date
from docx import Document
from docx.shared import Pt

from src.extraction.schemas import LeaveApplicationForm


def _format_display_date(iso_date: str) -> str:
    """'2026-07-20' -> '20 July 2026'"""
    d = date.fromisoformat(iso_date)
    return d.strftime("%d %B %Y")


def _add_line(doc: Document, text: str, bold: bool = False, size: int = 11):
    """Add a paragraph line, skip entirely if text is falsy (implements optional-field omission)."""
    if not text:
        return
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)


def write_body_paragraph(form: LeaveApplicationForm) -> str:
    """
    Placeholder body-paragraph writer. Replace with an LLM call (Ollama) later —
    kept as a plain function so it's swappable, same pattern as transcribe()/extract().
    """
    start_display = _format_display_date(form.start_date)
    return (
        f"I am writing to respectfully request {form.duration_days} day(s) of "
        f"{form.leave_type} leave starting {start_display}, on account of {form.reason}. "
        f"I will ensure all pending tasks are handed over before my leave begins."
    )


def generate(form: LeaveApplicationForm, output_path: str | Path) -> Path:
    """
    Render a LeaveApplicationForm into a .docx file.
    Raises ValueError if required fields are missing — check form.is_complete() before calling.
    """
    if not form.is_complete():
        raise ValueError(f"Cannot generate — missing required fields: {form.missing_fields}")

    output_path = Path(output_path)
    doc = Document()

    today_display = _format_display_date(date.today().isoformat())
    start_display = _format_display_date(form.start_date)
    duration_display = f"{form.duration_days} day{'s' if form.duration_days != 1 else ''}"

    # Header block — applicant info, optional lines omitted automatically
    _add_line(doc, form.applicant_name, bold=True)
    dept_line = f"{form.applicant_designation}, {form.department}" if form.department else form.applicant_designation
    _add_line(doc, dept_line)
    if form.employee_id:
        _add_line(doc, f"Employee ID: {form.employee_id}")
    _add_line(doc, f"Date: {today_display}")

    doc.add_paragraph()  # spacer

    # Recipient block
    _add_line(doc, f"To: {form.recipient_name}")
    _add_line(doc, form.recipient_designation)
    _add_line(doc, form.company_name)

    doc.add_paragraph()

    # Subject
    leave_type_label = form.leave_type.capitalize() if form.leave_type else ""
    _add_line(doc, f"Subject: Application for {leave_type_label} Leave ({duration_display})", bold=True)

    doc.add_paragraph()
    _add_line(doc, "Respected Sir/Madam,")
    doc.add_paragraph()

    # Body — LLM-written paragraph
    body = write_body_paragraph(form)
    _add_line(doc, body)
    doc.add_paragraph()
    _add_line(doc, "I shall be grateful for your kind approval. I will ensure all pending "
                   "tasks are handed over before my leave begins.")

    doc.add_paragraph()
    _add_line(doc, "Yours sincerely,")
    _add_line(doc, form.applicant_name)
    _add_line(doc, form.applicant_designation)
    if form.contact_number:
        _add_line(doc, f"Contact: {form.contact_number}")

    doc.save(output_path)
    return output_path


if __name__ == "__main__":
    # quick manual test with a fully-filled form
    test_form = LeaveApplicationForm(
        applicant_name="Ayesha Niazi",
        applicant_designation="Software Engineer",
        recipient_name="Ahmed Khan",
        company_name="TechSol Pvt Ltd",
        leave_type="casual",
        start_date="2026-07-20",
        duration_days=3,
        reason="sister's wedding",
    )
    out = generate(test_form, "test_output.docx")
    print(f"Generated: {out}")