import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PlanTier(str, enum.Enum):
    free = "free"
    pro = "pro"
    premium = "premium"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255), default="")
    plan: Mapped[PlanTier] = mapped_column(Enum(PlanTier), default=PlanTier.free)
    plan_granted: Mapped[bool] = mapped_column(Boolean, default=False)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    profile: Mapped["UserProfile | None"] = relationship(back_populates="user", uselist=False)
    shortlist_items: Mapped[list["ShortlistItem"]] = relationship(back_populates="user")
    applications: Mapped[list["Application"]] = relationship(back_populates="user")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    headline: Mapped[str] = mapped_column(String(500), default="")
    location: Mapped[str] = mapped_column(String(255), default="")
    visa_status: Mapped[str] = mapped_column(String(255), default="")
    linkedin: Mapped[str] = mapped_column(String(255), default="")
    github: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    certification: Mapped[str] = mapped_column(String(500), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    skills_json: Mapped[str] = mapped_column(Text, default="[]")
    projects_json: Mapped[str] = mapped_column(Text, default="[]")
    languages_json: Mapped[str] = mapped_column(Text, default="{}")
    role_targets_json: Mapped[str] = mapped_column(Text, default="[]")
    relocation_targets_json: Mapped[str] = mapped_column(Text, default="[]")
    stack_highlight: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped["User"] = relationship(back_populates="profile")


class Employer(Base):
    __tablename__ = "employers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company: Mapped[str] = mapped_column(String(255), index=True)
    website: Mapped[str] = mapped_column(Text, default="Unknown")
    careers_url: Mapped[str] = mapped_column(Text, default="")
    country: Mapped[str] = mapped_column(Text, default="")
    city: Mapped[str] = mapped_column(Text, default="")
    sector: Mapped[str] = mapped_column(Text, default="")
    subsector: Mapped[str] = mapped_column(Text, default="")
    company_stage: Mapped[str] = mapped_column(String(100), default="")
    company_scale: Mapped[str] = mapped_column(String(100), default="")
    employer_category: Mapped[str] = mapped_column(String(100), default="")
    remote: Mapped[str] = mapped_column(String(50), default="")
    visa_sponsorship: Mapped[str] = mapped_column(String(50), default="")
    eor: Mapped[str] = mapped_column(String(50), default="")
    hiring_geography: Mapped[str] = mapped_column(Text, default="")
    target_roles: Mapped[str] = mapped_column(Text, default="")
    tech_stack: Mapped[str] = mapped_column(Text, default="")
    region_eligibility: Mapped[str] = mapped_column(Text, default="")
    language_requirement: Mapped[str] = mapped_column(Text, default="")
    hiring_confidence: Mapped[str] = mapped_column(String(50), default="")
    reason_match: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(Text, default="")
    visa_sponsor_register: Mapped[str] = mapped_column(Text, default="")


class ShortlistItem(Base):
    __tablename__ = "shortlist_items"
    __table_args__ = (UniqueConstraint("user_id", "employer_id", name="uq_user_employer"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    employer_id: Mapped[int] = mapped_column(ForeignKey("employers.id"), index=True)
    score: Mapped[int] = mapped_column(Integer, default=0)
    match_notes: Mapped[str] = mapped_column(Text, default="")
    email_draft: Mapped[str] = mapped_column(Text, default="")
    to_email: Mapped[str] = mapped_column(String(255), default="")
    job_url: Mapped[str] = mapped_column(String(500), default="")
    outreach_status: Mapped[str] = mapped_column(String(50), default="Unsent")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="shortlist_items")
    employer: Mapped["Employer"] = relationship()


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    company: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(255), default="")
    job_url: Mapped[str] = mapped_column(String(500), default="")
    source: Mapped[str] = mapped_column(String(100), default="Manual")
    status: Mapped[str] = mapped_column(String(50), default="Applied")
    applied_date: Mapped[str] = mapped_column(String(20), default="")
    follow_up_date: Mapped[str] = mapped_column(String(20), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="applications")