#!/usr/bin/env python3
"""Admin utility: grant a plan to a user without Stripe (support/comp testing)."""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import SessionLocal
from app.models import PlanTier, User


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("email")
    parser.add_argument("plan", choices=["free", "pro", "premium"])
    args = parser.parse_args()

    db = SessionLocal()
    user = db.query(User).filter(User.email == args.email.lower()).first()
    if not user:
        print(f"User not found: {args.email}")
        sys.exit(1)
    user.plan = PlanTier(args.plan)
    db.commit()
    print(f"Granted {args.plan} to {user.email}")
    db.close()


if __name__ == "__main__":
    main()