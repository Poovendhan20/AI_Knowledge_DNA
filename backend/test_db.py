import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


# Load backend/.env
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_FILE)


DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_SSL_CA = os.getenv("DB_SSL_CA")


required = {
    "DB_HOST": DB_HOST,
    "DB_PORT": DB_PORT,
    "DB_NAME": DB_NAME,
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
    "DB_SSL_CA": DB_SSL_CA,
}


missing = [
    name
    for name, value in required.items()
    if not value
]


if missing:
    print("❌ Missing environment variables:")
    for item in missing:
        print(f"   - {item}")
    raise SystemExit(1)


# Convert relative certificate path into an absolute path.
if not os.path.isabs(DB_SSL_CA):
    DB_SSL_CA = os.path.join(BASE_DIR, DB_SSL_CA)


if not os.path.exists(DB_SSL_CA):
    print(f"❌ CA certificate not found:")
    print(DB_SSL_CA)
    raise SystemExit(1)


DATABASE_URL = (
    f"mysql+pymysql://"
    f"{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/"
    f"{DB_NAME}"
)


connect_args = {
    "ssl": {
        "ca": DB_SSL_CA,
    }
}


print("=" * 60)
print("AI KNOWLEDGE DNA - DATABASE CONNECTION TEST")
print("=" * 60)
print(f"Host       : {DB_HOST}")
print(f"Port       : {DB_PORT}")
print(f"Database   : {DB_NAME}")
print(f"User       : {DB_USER}")
print(f"CA exists  : {os.path.exists(DB_SSL_CA)}")
print("=" * 60)


try:
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True,
    )

    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT VERSION()")
        )

        version = result.scalar()

        print()
        print("✅ DATABASE CONNECTION SUCCESSFUL")
        print(f"MySQL version: {version}")
        print()

except Exception as error:
    print()
    print("❌ DATABASE CONNECTION FAILED")
    print()
    print("Error:")
    print(error)
    print()

    raise SystemExit(1)