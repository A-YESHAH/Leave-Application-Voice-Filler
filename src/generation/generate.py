"""generate(form) -> .docx file. Dispatches to the right template by document_type."""
from pathlib import Path
from datetime import date, datetime
from docx import Document
from docx.shared import Pt

from src.extraction.schemas import (
    LeaveApplicationOfficeForm,
    LeaveApplicationUniversityForm,
    ComplaintLetterForm,
)


def _format_display_date(iso_date: str) -> str:
    """'2026-07-20' -> '20 July 2026'"""
    d = date.fromisoformat(iso_date)
    return d.strftime("%d %B %Y")


def _add_line(doc: Document, text, bold: bool = False, size: int = 11):
    """Add a paragraph line, skip entirely if text is falsy (optional-field omission)."""
    if not text:
        return
    p = doc.add_paragraph()
    run = p.add_run(str(text))
    run.bold = bold
    run.font.size = Pt(size)


def write_body_paragraph_office(form: LeaveApplicationOfficeForm) -> str:
    start_display = _format_display_date(form.start_date)
    return (
        f"I am writing to respectfully request {form.duration_days} day(s) of "
        f"{form.leave_type} leave starting {start_display}, on account of {form.reason}. "
        f"I will ensure all pending tasks are handed over before my leave begins."
    )


def _generate_office(form: LeaveApplicationOfficeForm, output_path: Path) -> Path:
    doc = Document()
    today_display = _format_display_date(date.today().isoformat())
    duration_display = f"{form.duration_days} day{'s' if form.duration_days != 1 else ''}"

    _add_line(doc, form.applicant_name, bold=True)
    dept_line = f"{form.applicant_designation}, {form.department}" if form.department else form.applicant_designation
    _add_line(doc, dept_line)
    if form.employee_id:
        _add_line(doc, f"Employee ID: {form.employee_id}")
    _add_line(doc, f"Date: {today_display}")

    doc.add_paragraph()
    _add_line(doc, f"To: {form.recipient_name}")
    _add_line(doc, form.recipient_designation)
    _add_line(doc, form.company_name)

    doc.add_paragraph()
    leave_type_label = form.leave_type.capitalize() if form.leave_type else ""
    _add_line(doc, f"Subject: Application for {leave_type_label} Leave ({duration_display})", bold=True)

    doc.add_paragraph()
    _add_line(doc, "Respected Sir/Madam,")
    doc.add_paragraph()
    _add_line(doc, write_body_paragraph_office(form))
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


def write_body_paragraph_university(form: LeaveApplicationUniversityForm) -> str:
    start_display = _format_display_date(form.start_date)
    return (
        f"I respectfully submit that due to {form.reason}, I am unable to attend classes "
        f"starting {start_display}. I therefore request leave for {form.duration_days} day(s)."
    )


def _generate_university(form: LeaveApplicationUniversityForm, output_path: Path) -> Path:
    doc = Document()
    today_display = _format_display_date(date.today().isoformat())
    duration_display = f"{form.duration_days} day{'s' if form.duration_days != 1 else ''}"

    _add_line(doc, f"Date: {today_display}")
    doc.add_paragraph()
    _add_line(doc, f"To: {form.recipient_designation}")
    dept_line = f"Department of {form.department}" if form.department else None
    _add_line(doc, dept_line)
    _add_line(doc, form.institution_name)

    doc.add_paragraph()
    _add_line(doc, f"Subject: Application for Leave — {duration_display}", bold=True)

    doc.add_paragraph()
    _add_line(doc, f"Respected {form.recipient_salutation},")
    doc.add_paragraph()
    _add_line(doc, write_body_paragraph_university(form))
    doc.add_paragraph()
    _add_line(doc, "Kindly grant me leave for the mentioned period. I shall cover the "
                   "missed coursework at the earliest.")

    doc.add_paragraph()
    _add_line(doc, "Yours obediently,")
    _add_line(doc, form.student_name)
    program_line = f"{form.program}, Semester {form.semester}" if form.semester else form.program
    _add_line(doc, program_line)
    _add_line(doc, f"Roll No: {form.roll_number}")

    doc.save(output_path)
    return output_path

def write_body_paragraph_complaint(form: ComplaintLetterForm) -> str:
    return (
        f"I wish to bring to your attention that {form.issue_description}. "
        f"This is causing significant difficulty and I request that the matter be "
        f"looked into and resolved at the earliest."
    )


def _generate_complaint(form: ComplaintLetterForm, output_path: Path) -> Path:
    doc = Document()
    today_display = _format_display_date(date.today().isoformat())

    _add_line(doc, form.complainant_name, bold=True)
    _add_line(doc, form.address)
    if form.reference_number:
        _add_line(doc, f"Consumer/Reference No: {form.reference_number}")
    if form.contact_number:
        _add_line(doc, f"Contact: {form.contact_number}")
    _add_line(doc, f"Date: {today_display}")

    doc.add_paragraph()
    _add_line(doc, f"To: The {form.recipient_designation}")
    _add_line(doc, form.organization_name)
    _add_line(doc, form.organization_address)

    doc.add_paragraph()
    _add_line(doc, f"Subject: Complaint Regarding {form.complaint_subject}", bold=True)

    doc.add_paragraph()
    _add_line(doc, "Dear Sir/Madam,")
    doc.add_paragraph()
    _add_line(doc, write_body_paragraph_complaint(form))
    doc.add_paragraph()
    _add_line(doc, "I request you to kindly look into this matter urgently and resolve "
                   "it at the earliest. I look forward to your prompt response.")

    doc.add_paragraph()
    _add_line(doc, "Yours faithfully,")
    _add_line(doc, form.complainant_name)

    doc.save(output_path)
    return output_path


_GENERATORS = {
    "leave_application_office": _generate_office,
    "leave_application_university": _generate_university,
    "complaint_letter": _generate_complaint,
}


def generate(form, output_path: str | Path) -> Path:
    """
    Render a form into a .docx file. Dispatches by form.document_type.
    Raises ValueError if required fields are missing or the type is unsupported.
    """
    if not form.is_complete():
        raise ValueError(f"Cannot generate — missing required fields: {form.missing_fields}")

    generator_fn = _GENERATORS.get(form.document_type)
    if generator_fn is None:
        raise ValueError(f"No generator implemented for document_type: {form.document_type}")

    return generator_fn(form, Path(output_path))


if __name__ == "__main__":
    test_form = LeaveApplicationOfficeForm(
        applicant_name="Ayesha Niazi",
        applicant_designation="Software Engineer",
        recipient_name="Ahmed Khan",
        company_name="TechSol Pvt Ltd",
        leave_type="casual",
        start_date="2026-07-20",
        duration_days=3,
        reason="sister's wedding",
    )
    out = generate(test_form, "test_output_office.docx")
    print(f"Generated: {out}")