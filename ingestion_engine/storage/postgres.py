from sqlalchemy import create_engine
from models import Base
import os
from dotenv import load_dotenv

load_dotenv()

# engine = create_engine(
#     "postgresql+psycopg2://tender_user:tender_pass@localhost:5432/tender_db"
# )
engine = create_engine(os.getenv("POSTGRES_URL"))

with engine.connect() as conn:
    print("Connected to Postgres successfully!")

def init_db():
    Base.metadata.create_all(bind=engine)