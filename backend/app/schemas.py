from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    plan: str
    email: str
    full_name: str


class ProfileUpdate(BaseModel):
    headline: str = ""
    location: str = ""
    visa_status: str = ""
    linkedin: str = ""
    github: str = ""
    phone: str = ""
    certification: str = ""
    summary: str = ""
    skills: list[str] | dict[str, list[str]] = []
    projects: list[dict] = []
    languages: dict[str, str] = {}
    role_targets: list[str] = []
    relocation_targets: list[str] = []
    stack_highlight: str = ""


class CheckoutRequest(BaseModel):
    plan: str = Field(pattern="^(pro|premium)$")


class ShortlistUpdate(BaseModel):
    email_draft: str = ""
    to_email: str = ""
    job_url: str = ""
    outreach_status: str = ""


class ApplicationCreate(BaseModel):
    company: str
    role: str = ""
    job_url: str = ""
    source: str = "Manual"
    status: str = "Applied"
    applied_date: str = ""
    follow_up_date: str = ""
    notes: str = ""