from sqlalchemy import text
from db import SessionLocal

with SessionLocal() as db:
    db.execute(text("DELETE FROM template_tasks"))
    db.execute(text("DELETE FROM checklist_templates"))
    db.commit()
print("✅ template tables emptied")