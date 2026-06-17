#!/usr/bin/env python3
"""Reseed EmployerFlow DB from split pipeline CSVs. Run after sync_from_discovery.sh"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import SessionLocal, engine, Base
from app.models import Employer, JobSignal
from app.services.importer import import_employers_from_csv, import_job_signals_from_csv

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
MASTER = os.path.join(DATA, "master_employers.csv")
SIGNALS = os.path.join(DATA, "job_signals.csv")


def main():
    if not os.path.exists(MASTER):
        print(f"Missing {MASTER} — run sync_from_discovery.sh first")
        return 1

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        print("Clearing employers and job_signals…")
        db.query(JobSignal).delete()
        db.query(Employer).delete()
        db.commit()

        added, skipped = import_employers_from_csv(db, MASTER)
        print(f"Employers: +{added} ({skipped} skipped)")

        if os.path.exists(SIGNALS):
            added_s, skipped_s = import_job_signals_from_csv(db, SIGNALS)
            print(f"Job signals: +{added_s} ({skipped_s} skipped)")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())