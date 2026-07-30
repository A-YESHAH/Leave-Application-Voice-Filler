"""
Render a plain-text preview of the generated letter, without needing
to create an actual .docx file first. Reuses the same body-paragraph
writers as generate.py so the preview matches what actually gets
generated.
"""
from datetime import date

from src.generation.generate import (
    write_body_paragraph_office,
    write_body_paragraph_university,
    write_body_paragraph_complaint,
    _format_display_date,
)


def render_preview(form) -> str:
    """Returns a plain-text approximation of the generated document, for on-screen preview."""
    today_display = _format_display_date(date.today().isoformat())
    doc_type = form.document_type

    if doc_type == "leave_application_office":
        duration_display = f"{form.duration_days} day{'s' if form.duration_days != 1 else ''}"
        leave_type_label = form.leave_type.capitalize() if form.leave_type else ""
        lines = [
            form.applicant_name,
            f"{form.applicant_designation}, {form.department}" if form.department else form.applicant_designation,
            f"Employee ID: {form.employee_id}" if form.employee_id else None,
            f"Date: {today_display}",
            "",
            f"To: {form.recipient_name}",
            form.recipient_designation,
            form.company_name,
            "",
            f"Subject: Application for {leave_type_label} Leave ({duration_display})",
            "",
            "Respected Sir/Madam,",
            "",
            write_body_paragraph_office(form),
            "",
            "I shall be grateful for your kind approval.",
            "",
            "Yours sincerely,",
            form.applicant_name,
            form.applicant_designation,
            f"Contact: {form.contact_number}" if form.contact_number else None,
        ]

    elif doc_type == "leave_application_university":
        duration_display = f"{form.duration_days} day{'s' if form.duration_days != 1 else ''}"
        lines = [
            f"Date: {today_display}",
            "",
            f"To: {form.recipient_designation}",
            f"Department of {form.department}" if form.department else None,
            form.institution_name,
            "",
            f"Subject: Application for Leave — {duration_display}",
            "",
            f"Respected {form.recipient_salutation},",
            "",
            write_body_paragraph_university(form),
            "",
            "Kindly grant me leave for the mentioned period.",
            "",
            "Yours obediently,",
            form.student_name,
            f"{form.program}, Semester {form.semester}" if form.semester else form.program,
            f"Roll No: {form.roll_number}",
        ]

    elif doc_type == "complaint_letter":
        lines = [
            form.complainant_name,
            form.address,
            f"Consumer/Reference No: {form.reference_number}" if form.reference_number else None,
            f"Contact: {form.contact_number}" if form.contact_number else None,
            f"Date: {today_display}",
            "",
            f"To: The {form.recipient_designation}",
            form.organization_name,
            form.organization_address,
            "",
            f"Subject: Complaint Regarding {form.complaint_subject}",
            "",
            "Dear Sir/Madam,",
            "",
            write_body_paragraph_complaint(form),
            "",
            "I request you to kindly look into this matter urgently.",
            "",
            "Yours faithfully,",
            form.complainant_name,
        ]

    else:
        return "Preview not available for this document type."

    return "\n".join(line for line in lines if line)