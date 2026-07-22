from typing import Optional, Literal
from pydantic import BaseModel, Field


class BaseForm(BaseModel):
    document_type: str
    missing_fields: list[str] = Field(default_factory=list)

    def _required_fields(self) -> list[str]:
        raise NotImplementedError

    def compute_missing(self) -> list[str]:
        missing = [f for f in self._required_fields() if getattr(self, f) in (None, "", [])]
        self.missing_fields = missing
        return missing

    def is_complete(self) -> bool:
        return len(self.compute_missing()) == 0


class LeaveApplicationOfficeForm(BaseForm):
    document_type: str = Field(default="leave_application_office")

    applicant_name: Optional[str] = None
    applicant_designation: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_designation: Optional[str] = None
    company_name: Optional[str] = None
    leave_type: Optional[Literal["casual", "sick", "annual"]] = None
    start_date: Optional[str] = None
    duration_days: Optional[int] = None
    reason: Optional[str] = None

    department: Optional[str] = None
    employee_id: Optional[str] = None
    contact_number: Optional[str] = None

    def _required_fields(self) -> list[str]:
        return ["applicant_name", "applicant_designation", "recipient_name",
                "recipient_designation", "company_name", "leave_type",
                "start_date", "duration_days", "reason"]


class LeaveApplicationUniversityForm(BaseForm):
    document_type: str = Field(default="leave_application_university")

    student_name: Optional[str] = None
    roll_number: Optional[str] = None
    program: Optional[str] = None
    institution_name: Optional[str] = None
    start_date: Optional[str] = None
    duration_days: Optional[int] = None
    reason: Optional[str] = None
    recipient_designation: Optional[str] = None
    recipient_salutation: Optional[str] = None
    semester: Optional[str] = None
    department: Optional[str] = None

    def _required_fields(self) -> list[str]:
        return ["student_name", "roll_number", "program", "institution_name",
                "start_date", "duration_days", "reason",
                "recipient_designation", "recipient_salutation",
                "semester", "department"]


class ComplaintLetterForm(BaseForm):
    document_type: str = Field(default="complaint_letter")

    complainant_name: Optional[str] = None
    address: Optional[str] = None
    contact_number: Optional[str] = None
    organization_name: Optional[str] = None
    complaint_subject: Optional[str] = None
    issue_description: Optional[str] = None
    recipient_designation: Optional[str] = None

    reference_number: Optional[str] = None
    organization_address: Optional[str] = None
    issue_start: Optional[str] = None

    def _required_fields(self) -> list[str]:
        return ["complainant_name", "address", "contact_number", "organization_name",
                "complaint_subject", "issue_description", "recipient_designation"]


DOCUMENT_SCHEMAS = {
    "leave_application_office": LeaveApplicationOfficeForm,
    "leave_application_university": LeaveApplicationUniversityForm,
    "complaint_letter": ComplaintLetterForm,
}