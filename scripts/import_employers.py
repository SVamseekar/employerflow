#!/usr/bin/env python3
"""Import employers from CSV into EmployerFlow database."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import Base, SessionLocal, engine
from app.models import Employer
from app.services.importer import import_from_csv

CSV_PATH = os.environ.get(
    "EMPLOYER_CSV",
    os.path.join(os.path.dirname(__file__), "..", "data", "master_employers.csv"),
)


def main():
    if not os.path.exists(CSV_PATH):
        print(f"CSV not found: {CSV_PATH}")
        sys.exit(1)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    added, skipped = import_from_csv(db, CSV_PATH)
    total = db.query(Employer).count()
    print(f"Import complete: {added} added, {skipped} skipped, {total} total in DB")
    db.close()


if __name__ == "__main__":
    main()