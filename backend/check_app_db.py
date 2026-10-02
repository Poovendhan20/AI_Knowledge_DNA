from app import app, db
from sqlalchemy import text

with app.app_context():
    print("DATABASE:", db.engine.url.database)
    print("HOST:", db.engine.url.host)
    print("PORT:", db.engine.url.port)
    print("TABLES:", db.session.execute(text("SHOW TABLES")).fetchall())