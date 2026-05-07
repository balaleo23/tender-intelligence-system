from sqlalchemy import create_engine, text
from dotenv import load_dotenv; load_dotenv()

import os
engine = create_engine(os.getenv('POSTGRES_URL'))
with engine.connect() as c:
    print('Postgres OK:', c.execute(text('SELECT version()')).scalar()[:30])