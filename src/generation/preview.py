"""
Render a plain-text preview of the generated letter.

This reuses the same body paragraph functions as generate.py so the
preview always matches the generated document.
"""

from datetime import date

from src.generation.generate import (
    write_body_paragraph_office,
    write_body_paragraph_university,
    write_body_paragraph_complaint,
)

from src.utils.date_utils import format_date


def render_preview(form) -> str:
    """
    Returns a plain-text preview of the generated document.
    """

    today_display = format_date(date.today().isoformat())
    doc_type = form.document_type

    if doc_type == "leave_application_office":

        duration_display = (
            f"{form.duration_days} day"
            f"{'s' if form.duration_days != 1 else ''}"
        )

        leave_type = (
            form.leave_type.capitalize()
            if form.leave_type
            else "Leave"
        )

        lines = [
            form.applicant_name,
            (
                f"{form.applicant_designation}, {form.department}"
                if form.department
                else form.applicant_designation
            ),
            (
                f"Employee ID: {form.employee_id}"
                if form.employee_id
                else None
            ),
            (
                f"Contact: {form.contact_number}"
                if form.contact_number
                else None
            ),
            f"Date: {today_display}",
            "",
            f"To: {form.recipient_name}",
            form.recipient_designation,
            form.company_name,
            "",
            f"Subject: Application for {leave_type} Leave ({duration_display})",
            "",
            "Respected Sir/Madam,",
            "",
            write_body_paragraph_office(form),
            "",
            "I shall be grateful for your kind approval. Thank you for your consideration.",
            "",
            "Yours sincerely,",
            form.applicant_name,
            form.applicant_designation,
        ]

    elif doc_type == "leave_application_university":

        duration_display = (
            f"{form.duration_days} day"
            f"{'s' if form.duration_days != 1 else ''}"
        )

        salutation = form.recipient_salutation or "Sir/Madam"

        lines = [
            f"Date: {today_display}",
            "",
            f"To: {form.recipient_designation}",
            (
                f"Department of {form.department}"
                if form.department
                else None
            ),
            form.institution_name,
            "",
            f"Subject: Application for Leave ({duration_display})",
            "",
            f"Respected {salutation},",
            "",
            write_body_paragraph_university(form),
            "",
            "Kindly grant me leave for the above-mentioned period. I assure you that I will cover all missed lectures, assignments, and coursework after returning.",
            "",
            "Yours obediently,",
            form.student_name,
            (
                f"{form.program}, Semester {form.semester}"
                if form.semester
                else form.program
            ),
            f"Roll No: {form.roll_number}",
            form.institution_name,
        ]

    elif doc_type == "complaint_letter":

        lines = [
            form.complainant_name,
            form.address,
            (
                f"Contact: {form.contact_number}"
                if form.contact_number
                else None
            ),
            (
                f"Reference No: {form.reference_number}"
                if form.reference_number
                else None
            ),
            f"Date: {today_display}",
            "",
            f"To: {form.recipient_designation}",
            form.organization_name,
            form.organization_address,
            "",
            f"Subject: Complaint Regarding {form.complaint_subject}",
            "",
            "Dear Sir/Madam,",
            "",
            write_body_paragraph_complaint(form),
            "",
            "I would appreciate your prompt attention to this matter and look forward to a suitable resolution at the earliest.",
            "",
            "Yours faithfully,",
            form.complainant_name,
        ]

    else:
        return "Preview not available for this document type."

    cleaned_lines = [
        str(line)
        for line in lines
        if line is not None
    ]

    return "\n".join(cleaned_lines)