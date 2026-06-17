import os

from sqlalchemy import func

from app.database import SessionLocal
from app.models import Employer, JobSignal
from app.services.importer import import_employers_from_csv, import_job_signals_from_csv

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def maybe_seed():
    db = SessionLocal()
    try:
        emp_count = db.query(func.count(Employer.id)).scalar() or 0
        sig_count = db.query(func.count(JobSignal.id)).scalar() or 0

        if emp_count > 0 and sig_count > 0:
            return

        employer_csv = os.environ.get(
            "EMPLOYER_CSV",
            os.path.join(DATA_DIR, "master_employers.csv"),
        )
        signals_csv = os.environ.get(
            "JOB_SIGNALS_CSV",
            os.path.join(DATA_DIR, "job_signals.csv"),
        )

        if emp_count == 0 and os.path.exists(employer_csv):
            added, skipped = import_employers_from_csv(db, employer_csv)
            print(f"[startup] Seeded {added} employers ({skipped} skipped)")

        if sig_count == 0 and os.path.exists(signals_csv):
            added, skipped = import_job_signals_from_csv(db, signals_csv)
            print(f"[startup] Seeded {added} job signals ({skipped} skipped)")
    finally:
        db.close()