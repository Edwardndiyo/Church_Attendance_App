import csv
from io import TextIOWrapper
from ..models.state import State
from ..extensions import db

def import_states_from_file(file_storage):
    """
    Accepts a Werkzeug FileStorage from request.files.
    Expects CSV with headers: name,code,leader  (case-insensitive)
    Returns a summary dict.
    """
    # make sure file is treated as text
    wrapper = TextIOWrapper(file_storage.stream, encoding="utf-8")
    reader = csv.DictReader(wrapper)
    created = 0
    updated = 0
    errors = []
    for i, row in enumerate(reader, start=1):
        try:
            name = (row.get("name") or row.get("Name") or "").strip()
            code = (row.get("code") or row.get("Code") or "").strip()
            leader = (row.get("leader") or row.get("Leader") or "").strip()
            if not name:
                errors.append({"row": i, "error": "name missing"})
                continue

            existing = State.query.filter_by(name=name).first()
            if existing:
                existing.code = code or existing.code
                existing.leader = leader or existing.leader
                updated += 1
            else:
                s = State(name=name, code=code, leader=leader)
                db.session.add(s)
                created += 1
        except Exception as e:
            errors.append({"row": i, "error": str(e)})
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return {"created": 0, "updated": 0, "errors": [{"commit": str(e)}]}

    return {"created": created, "updated": updated, "errors": errors}
