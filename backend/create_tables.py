from app import app
from models import db


print("=" * 60)
print("AI KNOWLEDGE DNA - DATABASE TABLE SETUP")
print("=" * 60)

try:
    with app.app_context():
        db.create_all()

    print()
    print("✅ ALL DATABASE TABLES CREATED SUCCESSFULLY")
    print()

except Exception as error:
    print()
    print("❌ DATABASE TABLE CREATION FAILED")
    print()
    print("Error:")
    print(error)
    print()