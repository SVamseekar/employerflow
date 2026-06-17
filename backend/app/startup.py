import os

from sqlalchemy import func

from app.database import SessionLocal
from app.models import Employer
from app.services.importer import import_from_csv


def maybe_seed():
    db = SessionLocal()
    try:
        count = db.query(func.count(Employer.id)).scalar() or 0
        if count > 0:
            return
        csv_path = os.environ.get(
            "EMPLOYER_CSV",
            os.path.join(os.path.dirname(__file__), "..", "data", "master_employers.csv"),
        )
        if not os.path.exists(csv_path):
            print(f"[startup] No employers in DB. Set EMPLOYER_CSV or place CSV at {csv_path}")
            return
        added, skipped = import_from_csv(db, csv_path)
        print(f"[startup] Seeded {added} employers ({skipped} skipped)")
    finally:
        db.close()