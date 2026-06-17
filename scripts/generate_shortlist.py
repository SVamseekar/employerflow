#!/usr/bin/env python3
"""Admin utility: generate shortlist for a user by email (no HTTP)."""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.config import get_settings
from app.database import SessionLocal
from app.models import Employer, PlanTier, ShortlistItem, User, UserProfile
from app.services.email_generator import generate_email, guess_to_email
from app.services.scoring import score_all

settings = get_settings()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("email")
    args = parser.parse_args()

    db = SessionLocal()
    user = db.query(User).filter(User.email == args.email.lower()).first()
    if not user:
        print(f"User not found: {args.email}")
        sys.exit(1)
    if user.plan == PlanTier.free:
        print(f"User {user.email} is on free plan — grant pro/premium first.")
        sys.exit(1)

    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile or profile.skills_json in ("", "[]"):
        print("Profile missing or has no skills.")
        sys.exit(1)

    limit = settings.premium_shortlist_limit if user.plan == PlanTier.premium else settings.pro_shortlist_limit
    employers = db.query(Employer).all()
    scored = score_all(employers, profile, min_score=20, limit=limit)

    db.query(ShortlistItem).filter(ShortlistItem.user_id == user.id).delete()
    items = []
    for item in scored:
        emp = item["employer"]
        items.append(ShortlistItem(
            user_id=user.id,
            employer_id=emp.id,
            score=item["score"],
            match_notes=item["match_notes"],
            email_draft=generate_email(user, profile, emp),
            to_email=guess_to_email(emp.company, emp.website),
            job_url=emp.careers_url,
        ))
    db.bulk_save_objects(items)
    db.commit()
    print(f"Generated {len(scored)} shortlist items for {user.email} ({user.plan.value})")
    db.close()


if __name__ == "__main__":
    main()