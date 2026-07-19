"""Pydantic schemas for structured form extraction. One class per document type."""
from typing import Optional, Literal
from pydantic import BaseModel, Field


class LeaveApplicationForm(BaseModel):
    document_type: str = Field(default="leave_application_office")

    # Required fields
    applicant_name: Optional[str] = Field(default=None, description="Name of the person applying")
    applicant_designation: Optional[str] = Field(default=None, description="e.g. 'Software Engineer'")
    recipient_name: Optional[str] = Field(default=None, description="Who the letter is addressed to")
    company_name: Optional[str] = Field(default=None, description="Employer/organization name")
    leave_type: Optional[Literal["casual", "sick", "annual"]] = Field(
        default=None, description="Type of leave — ask if ambiguous (e.g. 'chutti' alone)"
    )
    start_date: Optional[str] = Field(default=None, description="ISO date YYYY-MM-DD")
    duration_days: Optional[int] = Field(default=None, description="Number of leave days")
    reason: Optional[str] = Field(default=None, description="Formal reason for leave")

    # Optional fields — omit the template line entirely if these are null
    department: Optional[str] = Field(default=None)
    employee_id: Optional[str] = Field(default=None)
    recipient_designation: Optional[str] = Field(default="Manager")
    contact_number: Optional[str] = Field(default=None)

    missing_fields: list[str] = Field(default_factory=list)

    REQUIRED_FIELDS: list[str] = Field(
        default=[
            "applicant_name", "applicant_designation", "recipient_name",
            "company_name", "leave_type", "start_date", "duration_days", "reason",
        ],
        exclude=True,
    )

    def compute_missing(self) -> list[str]:
        missing = [f for f in self.REQUIRED_FIELDS if getattr(self, f) in (None, "", [])]
        self.missing_fields = missing
        return missing

    def is_complete(self) -> bool:
        return len(self.compute_missing()) == 0


DOCUMENT_SCHEMAS = {
    "leave_application_office": LeaveApplicationForm,
}