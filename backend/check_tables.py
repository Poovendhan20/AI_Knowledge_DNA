from app import app
from models import db


with app.app_context():
    print("=" * 60)
    print("AI KNOWLEDGE DNA - DATABASE TABLE CHECK")
    print("=" * 60)

    tables = db.metadata.tables

    for table_name in tables:
        print(f"✅ {table_name}")

    print("=" * 60)
    print(f"Total tables: {len(tables)}")