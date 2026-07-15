from sqlmodel import SQLModel, create_engine, Session
import os

database_url = os.getenv("DATABASE_URL")
if not database_url:
    sqlite_file_name = "spotify.db"
    # Resolve path to backend folder so the database is in the backend root
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sqlite_path = os.path.join(BASE_DIR, sqlite_file_name)
    database_url = f"sqlite:///{sqlite_path}"

if database_url.startswith("sqlite"):
    # Ensure directory exists for SQLite database path
    db_path = database_url.replace("sqlite:///", "")
    if db_path:
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
            except Exception as e:
                print(f"Warning: Could not create directory {db_dir} for database: {e}")

    connect_args = {"check_same_thread": False}
    engine = create_engine(database_url, echo=False, connect_args=connect_args)
else:
    engine = create_engine(database_url, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
